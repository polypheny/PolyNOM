from enum import Enum
from polynom.schema.field import Field, PrimaryKeyField
from polynom.schema.polytypes import VarChar
import polynom.config as cfg

class DataModel(Enum):
    RELATIONAL = "RELATIONAL"
    DOCUMENT = "DOCUMENT"
    GRAPH = "GRAPH"

class BaseSchema:
    entity_name: str
    namespace_name: str = cfg.get(cfg.DEFAULT_NAMESPACE)
    data_model: DataModel = DataModel(cfg.get(cfg.DEFAULT_DATA_MODEL))
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
            "namespace_name": getattr(cls, "namespace_name", cfg.get(cfg.DEFAULT_NAMESPACE)),
            "data_model": getattr(cls, "data_model", DataModel(cfg.get(cfg.DEFAULT_DATA_MODEL))).name,
            "fields": [field._to_dict() for field in cls._get_fields()]
        }

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.data_model}, {self.namespace_name}, {self.entity_name}>"
            
        

