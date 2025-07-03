import inspect

import polypheny
import json
from json import dumps
from datetime import datetime
from enum import Enum, auto
from dataclasses import dataclass, field
from orm.model import BaseModel
from orm.reflection.reflection import ChangeLog
from orm.schema.relationship import Relationship


class _SessionState(Enum):
    INITIALIZED = auto()
    ACTIVE = auto()
    COMPLETED = auto()

@dataclass
class Session:
    _host: str
    _port: int
    _log_user: str
    _db_user: str = "pa"
    _password: str = ""
    _transport: str = 'plain'

    _conn: any = field(init=False, default=None)
    _cursor: any = field(init=False, default=None)
    _state: _SessionState = field(init=False, default=_SessionState.INITIALIZED)
    _tracked_models: dict[str, BaseModel] = field(default_factory=dict, init=False)

    def __enter__(self):
        if self._state == _SessionState.ACTIVE:
            return
            
        self._conn = polypheny.connect(
            (self._host, self._port),
            username=self._db_user,
            password=self._password,
            transport=self._transport
        )
        self._cursor = self._conn.cursor()
        self._state = _SessionState.ACTIVE
        return self

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
        if not model._is_active:
            raise ValueError('The passed model originates from an already completed session and should be discarded.')
      
        if tracking:
            # add all the children to the session too
            self._track(model)
            for attr in vars(model.__class__):
                rel = inspect.getattr_static(model.__class__, attr)
                if isinstance(rel, Relationship):
                    if "save-update" in (rel._cascade or "") or "all" in (rel._cascade or ""):
                        child = getattr(model, attr)
                        if child:
                            if getattr(child, "_session", None) is None:
                                child._session = self
                            self.add(child)

        entity = model.schema.entity_name
        namespace = model.schema.namespace_name
        data = model._to_insert_dict()

        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))

        values = tuple(data.values())
        
        if model._is_active:
            sql = f'INSERT INTO "{namespace}"."{entity}" ({columns}) VALUES ({placeholders})'
            self._cursor.executeany("sql" ,sql, values, namespace=namespace)
            
    def add_all(self, models):
        for model in models:
            self.add(model)
            
    def _track(self, model):
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
        entity = model.schema.entity_name
        namespace = model.schema.namespace_name
        sql = f'DELETE FROM "{namespace}"."{entity}" WHERE _entry_id = ?'
        self._cursor.executeany("sql", sql, (model._entry_id,), namespace=model.schema.namespace_name)
        if model._entry_id in self._tracked_models:
            model._is_active = False

    def delete_all(self, models):
        for model in models:
            self.delete(model)
            
    def flush(self):
        for model in self._tracked_models.values():
            if not model._is_active:
                continue
            
            diff = model._diff()
            if diff:
                self._update(model)
                self._update_change_log(model, diff)

    def commit(self):
        if self._state != _SessionState.ACTIVE:
            raise RuntimeError(f"Cannot commit in session state {self._state.name}.")

        self.flush()     
        self._conn.commit()

        for model in self._tracked_models.values():
            # check if the model has a child or not and then only commit that
            model._is_active = False
            
        self._state = _SessionState.COMPLETED

    def rollback(self):
        if self._state != _SessionState.ACTIVE:
            raise RuntimeError(f"Cannot rollback in session state {self._state.name}.")
        self._conn.rollback()
        self._state = _SessionState.COMPLETED

    def get_session_state(self):
        return self._state

    def detach_child(self, parent: BaseModel, attr_name: str):
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
            self.rollback()
        if self._cursor:
            self._cursor.close()
        if self._conn:
            self._conn.close()

