from polynom.schema.field import Field, PrimaryKeyField
from polynom.schema.polytypes import VarChar
from polynom.constants import DEFAULT_NAMESPACE

class BaseSchema:
    entity_name: str
    namespace_name: str = DEFAULT_NAMESPACE
    previous_name: str = None
    _base_fields = [
        PrimaryKeyField('_entry_id', VarChar(36), unique=True)
    ]
    _type_map: dict[str, Field] = None

    @classmethod
    def _get_fields(cls):
        return cls._base_fields + cls.fields
        
    @classmethod 
    def _get_field_map(cls):
        if cls._type_map is None:
            cls._type_map = {}
            for field in cls._get_fields():
                cls._type_map[field._python_field_name] = field
        return cls._type_map
        
    @classmethod
    def _to_dict(cls):
        return {
            "entity_name": cls.entity_name,
            "namespace_name": getattr(cls, "namespace_name", DEFAULT_NAMESPACE),
            "fields": [field._to_dict() for field in cls._get_fields()]
        }
            
        

