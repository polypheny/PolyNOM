from __future__ import annotations
from typing import Type, TypeVar, TYPE_CHECKING
from polynom.schema.polytypes import _BaseType

if TYPE_CHECKING:
    from polynom.schema.schema import BaseSchema

T = TypeVar('T', bound=_BaseType)

class _BaseField:
    def __init__(self, db_field_name: str, polytype, python_field_name: str = None, previous_name: str = None):
        self._db_field_name = db_field_name
        self._python_field_name = python_field_name if python_field_name is not None else db_field_name
        self._polytype = polytype
        self._previous_name = previous_name

    def _transform(self, row: dict[str, any]) -> any:
        value = row.get(self._db_field_name)
        if value is None:
            return None
        if hasattr(self._polytype, "from_db"):
            return self._polytype.from_db(value)
        return value
        
    def _to_dict(self):
        return {
            "name": self._python_field_name,
            "db_name": self._db_field_name,
            "type": self._polytype.__class__.__name__,
            "previous_name": self._previous_name,
        }

              
class Field(_BaseField):
    def __init__(self, db_field_name: str, polytype: Type[T], nullable: bool = True, default = None, unique: bool = False, python_field_name: str = None, previous_name: str = None):
        super().__init__(db_field_name, polytype, python_field_name, previous_name)
        self.nullable: bool = nullable
        self.default = default
        self.unique: bool = unique

    def __eq__(self, other):
        return ("=", self, other)

    def __ne__(self, other):
        return ("!=", self, other)

    def __gt__(self, other):
        return (">", self, other)

    def __lt__(self, other):
        return ("<", self, other)

    def __ge__(self, other):
        return (">=", self, other)

    def __le__(self, other):
        return ("<=", self, other)
        
    def _to_dict(self):
        base = super()._to_dict()
        base.update({
            "nullable": self.nullable,
            "unique": self.unique,
            "default": self.default,
            "is_primary_key": False,
            "is_foreign_key": False
        })
        return base

class PrimaryKeyField(Field):
    def __init__(self, db_field_name: str, polytype: Type[T], unique: bool = False, python_field_name: str = None, previous_name: str = None):
        super().__init__(db_field_name, polytype, nullable=False, unique=unique, python_field_name=python_field_name, previous_name=previous_name)
        
    def _to_dict(self):
        base = super()._to_dict()
        base["is_primary_key"] = True
        return base
        
class ForeignKeyField(Field):    
    def __init__(self, db_field_name: str, referenced_schema: "type[BaseSchema]", referenced_db_field_name: str = '_entry_id', nullable: bool = True, unique: bool = False, python_field_name: str = None, previous_name: str = None):
        polytype = referenced_schema._get_field_map()[referenced_db_field_name]._polytype
        super().__init__(db_field_name, polytype, nullable, unique, python_field_name, previous_name=previous_name)
        self.referenced_namespace_name: str = referenced_schema.namespace_name
        self.referenced_entity_name: str = referenced_schema.entity_name
        self.referenced_db_field_name: str = referenced_db_field_name
        
    def _to_dict(self):
        base = super()._to_dict()
        base.update({
            "is_foreign_key": True,
            "references_namespace": self.referenced_namespace_name,
            "references_entity": self.referenced_entity_name,
            "references_field": self.referenced_db_field_name
        })
        return base
