import uuid as uuidlib
from typing import Any, Type, TypeVar
from copy import deepcopy
from polynom.query.query import Query
T = TypeVar("T")


class BaseModel:
    schema: Type[Any]

    def __init__(self, _entry_id: str = None):
        if _entry_id is None:
            _entry_id = str(uuidlib.uuid4())
        self._entry_id = _entry_id
        self._original_state = deepcopy(self.__dict__)
        self._is_active = True
        
    def __setattr__(self, name, value):
        if name == '_is_active':
            object.__setattr__(self, name, value)
            return
        
        if getattr(self, "_is_active", True):
            object.__setattr__(self, name, value)
            return
            
        raise AttributeError(f"This instance of entry {self._entry_id} is no longer mapped: it is either outside its session, deleted within its session, or replaced by a query result.")
      
    @classmethod
    def query(cls, session):
        return Query(cls, session)
        
    def _diff(self) -> dict[str, tuple]:
        if not self._is_active:
            raise ValueError('The session creating this model has completed. This model should thus be discarded.')
        changelog = {}

        all_keys = set(self._original_state.keys()) | set(self.__dict__.keys())
        for key in self.schema._get_field_map().keys():
            original_value = self._original_state.get(key)
            current_value = self.__dict__.get(key)
            if original_value != current_value:
                changelog[key] = (original_value, current_value)
        return changelog
        
    @classmethod
    def _from_row(cls: Type[T], row: dict[str, Any]) -> T:
        obj_data = {
            field._python_field_name: field._polytype._from_prism_serializable(row[field._db_field_name])
            for field in cls.schema._get_fields()
        }
        return cls(**obj_data)

    def _to_update_dict(self) -> dict[str, Any]:
        return {
            field._db_field_name: field._polytype._to_prism_serializable(getattr(self, field._python_field_name))
            for field in self.schema._get_fields()
            if hasattr(self, field._python_field_name)
     }

    def _to_insert_dict(self) -> dict[str, Any]:
        return {
            field._db_field_name: field._polytype._to_prism_serializable(getattr(self, field._python_field_name))
            for field in self.schema._get_fields()
            if hasattr(self, field._python_field_name)
        }

    def __repr__(self):
        field_map = self.schema._get_field_map()
        field_values = {
            name: getattr(self, name, None)
            for name in field_map.keys()
        }
        return f"<{self.__class__.__name__} {field_values}>"

