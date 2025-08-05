import logging
import uuid as uuidlib
from typing import Any, Type, TypeVar
from copy import deepcopy
from polynom.query import Query

T = TypeVar("T")
logger = logging.getLogger(__name__)

class BaseModel:
    schema: Type[Any]

    def __init__(self, _entry_id: str = None):
        if _entry_id is None:
            _entry_id = str(uuidlib.uuid4())
        self._entry_id = _entry_id
        self._is_active = True
        self._update_snapshot()

    def __setattr__(self, name, value):
        if name == '_is_active':
            object.__setattr__(self, name, value)
            return

        if getattr(self, "_is_active", True):
            object.__setattr__(self, name, value)
            return

        self._throw_invalid()
        
    def _throw_invalid(self):
        message = f"This instance of entry {self._entry_id} is no longer mapped: it is either outside its session, deleted within its session, or replaced by a query result"
        logger.debug(message)
        raise AttributeError(message)
        
    def _update_snapshot(self):
        self._snapshot = {
            field._python_field_name: deepcopy(self.__dict__.get(field._python_field_name))
            for field in self.schema._get_fields()
        }

    def _diff(self) -> dict[str, tuple]:
        if not self._is_active:
            self._throw_invalid()

        changelog = {}
        for field in self.schema._get_fields():
            key = field._python_field_name
            old = self._snapshot.get(key)
            new = self.__dict__.get(key)
            if old != new:
                changelog[key] = (old, new)
        return changelog
        
    def __repr__(self):
        field_map = self.schema._get_field_map()
        field_values = {
            name: getattr(self, name, None)
            for name in field_map.keys()
        }
        return f"<{self.__class__.__name__} {field_values}>"

    @classmethod
    def query(cls, session):
        return Query(cls, session)

    @classmethod
    def _from_dict(cls: Type[T], row: dict[str, Any]) -> T:
        obj_data = {
            field._python_field_name: field._polytype._from_prism_serializable(row[field._db_field_name])
            for field in cls.schema._get_fields()
        }
        return cls(**obj_data)

    def _to_dict(self) -> dict[str, Any]:
        return {
            field._db_field_name: field._polytype._to_prism_serializable(getattr(self, field._python_field_name))
            for field in self.schema._get_fields()
            if hasattr(self, field._python_field_name)
     }

class FlexModel(BaseModel):
    def __init__(self, _entry_id: str = None, **kwargs):
        if not hasattr(self, 'schema'):
            raise ValueError("FlexModel must have a schema attribute defined before instantiation.")
        
        for field in self.schema._get_fields():
            value = kwargs.get(field._python_field_name)
            setattr(self, field._python_field_name, value)
        
        super().__init__(_entry_id=_entry_id)

    @classmethod
    def from_schema(cls, schema) -> Type['FlexModel']:

        class _DynamicFlexModel(FlexModel):
            pass

        _DynamicFlexModel.schema = schema
        return _DynamicFlexModel

    @classmethod
    def _from_dict(cls: Type[T], row: dict[str, Any]) -> T:
        if not hasattr(cls, 'schema'):
            raise ValueError("Schema must be defined on FlexModel subclass before calling _from_dict.")

        obj_data = {
            field._python_field_name: field._polytype._from_prism_serializable(row[field._db_field_name])
            for field in cls.schema._get_fields()
            if field._db_field_name in row
        }
        return cls(**obj_data)