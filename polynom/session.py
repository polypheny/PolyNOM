import inspect
import logging
import polypheny
import json
import uuid
from json import dumps
from typing import Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum, auto
from dataclasses import dataclass, field
from polynom.model import BaseModel
from polynom.reflection import ChangeLog
from polynom.schema.relationship import Relationship

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from polynom.application import Application

class _SessionState(Enum):
    INITIALIZED = auto()
    ACTIVE = auto()
    COMPLETED = auto()

@dataclass
class Session:
    def __init__(
        self,
        application: 'Application',
        log_user: str = None,
    ):

        from polynom.application import Application
        if not application._initialized:
            message = "The application must be initialized before its sessions"
            logger.error(message)
            raise ValueError(message)
            
        self._application = application
        self._log_user: str = log_user
        self._session_id = uuid.uuid4()

        self._conn = None
        self._cursor = None
        self._state = _SessionState.INITIALIZED
        self._tracked_models: dict[str, BaseModel] = {}

    def __enter__(self):
        if self._state == _SessionState.ACTIVE:
            return
            
        self._conn = polypheny.connect(
            self._application._address,
            username=self._application._user,
            password=self._application._password,
            transport=self._application._transport
        )
        self._cursor = self._conn.cursor()
        self._state = _SessionState.ACTIVE
        logger.debug(f"Session {self._session_id} started.")
        return self
        
    def _throw_if_not_active(self):
        if self._state == _SessionState.INITIALIZED:
            message = f'Session {self._session_id} must first be activated by using it in a "with" block'
            logger.error(message)
            raise RuntimeError(message)
            
        if self._state == _SessionState.COMPLETED:
            message = f'This operation cannot be performed by the completed Session {self._session_id}'
            logger.error(message)
            raise RuntimeError(message)

    def _update(self, model):
        entity = model.schema.entity_name
        namespace = model.schema.namespace_name
        data = model._to_update_dict()

        if not hasattr(model, "_entry_id") or model._entry_id is None:
            raise ValueError("Model must have an _entry_id to perform update.")

        if '_entry_id' in data:
            data.pop('_entry_id')

        set_clause = ', '.join(f"{col} = ?" for col in data.keys())
        values = list(data.values())
        values.append(model._entry_id)
    
        sql = f'UPDATE "{namespace}"."{entity}" SET {set_clause} WHERE _entry_id = ?'
        self._cursor.executeany("sql", sql, values, namespace=namespace)

    def _update_change_log(self, model, diff: dict):   
        field_map = model.schema._get_field_map()
        change_data = {}
        for field_name, (old_value, new_value) in diff.items():
            poly_type = field_map.get(field_name)._polytype
            old_serialized = poly_type._to_json_serializable(old_value)
            new_serialized = poly_type._to_json_serializable(new_value)
            change_data[field_name] = [old_serialized, new_serialized]

        change_log = ChangeLog(
            model._entry_id,
            model.schema.entity_name,
            self._log_user,
            datetime.now(),
            change_data
        )
        
        self.add(change_log, tracking=False)
        self._update(change_log)
        

    def add(self, model, tracking=True):
        self._throw_if_not_active()
        
        if not model._is_active:
            raise ValueError('The passed model either originates from another session or is no longer the newest version in this session.')
      
        if tracking:
            # add all the children to the session too
            self._track(model)
            self._add_related_models(model)
        
        entity = model.schema.entity_name
        namespace = model.schema.namespace_name
        data = model._to_insert_dict()

        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        values = tuple(data.values())
        
        sql = f'INSERT INTO "{namespace}"."{entity}" ({columns}) VALUES ({placeholders})'
        self._cursor.executeany("sql" ,sql, values, namespace=namespace)
            
    def add_all(self, models, tracking=True):
        # session state is checked by add
        for model in models:
            self.add(model, tracking=tracking)
            
    def _add_related_models(self, model):
        for attr in vars(model.__class__):
            rel = inspect.getattr_static(model.__class__, attr)
            if not isinstance(rel, Relationship):
                continue
                
            cascade = rel._cascade or ""
            if "save-update" not in cascade and "all" not in cascade:
                continue
                
            child = getattr(model, attr)
            if not child:
                continue
                
            if getattr(child, "_session", None) is None:
                child._session = self
                
            self.add(child)
            
    def _track(self, model):
        old = self._tracked_models.get(model._entry_id)
        if old:
            logger.debug(f'Tracked entry {old._entry_id} replaced by query result in session {self._session_id}')
            old._is_active = False
        self._tracked_models[model._entry_id] = model

    
    def _track_all(self, models):
        for model in models:
            self._track(model)
        
    def _execute(self, language, statement, parameters=None, namespace=None, fetch=True ):
        self._cursor.executeany(language, statement, params=parameters, namespace=namespace)
        if fetch:
            return self._cursor.fetchall()
        return

    def delete(self, model):
        self._throw_if_not_active()
        
        entity = model.schema.entity_name
        namespace = model.schema.namespace_name
        sql = f'DELETE FROM "{namespace}"."{entity}" WHERE _entry_id = ?'
        self._cursor.executeany("sql", sql, (model._entry_id,), namespace=model.schema.namespace_name)
        if model._entry_id in self._tracked_models:
            model._is_active = False

    def delete_all(self, models):
        # session state is checked by delete
        for model in models:
            self.delete(model)
            
    def flush(self):
        self._throw_if_not_active()
        for model in self._tracked_models.values():
            if not model._is_active:
                continue
            
            diff = model._diff()
            if diff:
                self._update(model)
                if self._log_user:
                    self._update_change_log(model, diff)
            model._update_snapshot()
        logger.debug(f"Session {self._session_id} flushed to polypheny.")

    def commit(self):
        self._throw_if_not_active()
        
        self.flush()     
        self._conn.commit()

        # check if the model has a child or not and then only commit that
        self._invalidate_models()
            
        self._state = _SessionState.COMPLETED
        logger.debug(f"Session {self._session_id} committed.")

    def rollback(self):
        self._throw_if_not_active()
        self._invalidate_models()
        self._conn.rollback()
        self._state = _SessionState.COMPLETED
        logger.debug(f"Session {self._session_id} rolled back.")
        
    def _invalidate_models(self):
        for model in self._tracked_models.values():
            model._is_active = False

    def get_session_state(self):
        return self._state

    def detach_child(self, parent: BaseModel, attr_name: str):
        self._throw_if_not_active()
        rel = inspect.getattr_static(parent.__class__, attr_name)
        if not isinstance(rel, Relationship):
            raise TypeError(f"{attr_name} is not a Relationship field")

        child = getattr(parent, attr_name)
        if child is None:
            print("child is none ")
            return

        setattr(parent, attr_name, None)

        if "delete-orphan" in (rel._cascade or ""):
            back_attr = rel._back_populates
            if back_attr:
                setattr(child, back_attr, None)
            if getattr(child, back_attr, None) is None:
                self.delete(child)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._state == _SessionState.ACTIVE:
            logger.debug(f"Automatically rolling back Session {self._session_id} before exit.")
            self.rollback()
        if self._cursor:
            self._cursor.close()
        if self._conn:
            self._conn.close()

