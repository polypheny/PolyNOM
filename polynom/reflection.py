from polynom.model import BaseModel
from polynom.schema.schema_registry import register_schema
from polynom.schema.schema import BaseSchema
from polynom.schema.field import Field
from polynom.schema.polytypes import Timestamp, Text, Json
import polynom.config as cfg

class ChangeLogSchema(BaseSchema):
    entity_name = cfg.get(cfg.CHANGE_LOG_TABLE)
    namespace_name = cfg.get(cfg.INTERNAL_NAMESPACE)
    fields = [
        Field('modified_entry_id', Text(), nullable=False),
        Field('modified_entity_name', Text(), nullable=False),
        Field('modified_by', Text(), nullable=False),
        Field('date_of_change', Timestamp(), nullable=False),
        Field('changes', Json(), nullable=False),
    ]

class ChangeLog(BaseModel):
    schema = ChangeLogSchema()

    def __init__(self, modified_entry_id: str, modified_entity_name: str, modified_by: str, date_of_change, changes: dict, _entry_id = None):
        super().__init__(_entry_id)
        self.modified_entry_id = modified_entry_id
        self.modified_entity_name = modified_entity_name
        self.modified_by = modified_by
        self.date_of_change = date_of_change
        self.changes = changes

class SchemaSnapshotSchema(BaseSchema):
    entity_name = cfg.get(cfg.SNAPSHOT_TABLE)
    namespace_name = cfg.get(cfg.INTERNAL_NAMESPACE)
    fields = [
        Field('snapshot', Json(), nullable=False),
    ]

class SchemaSnapshot(BaseModel):
    schema = SchemaSnapshotSchema()

    def __init__(self, snapshot: dict, _entry_id = None):
        super().__init__(_entry_id)
        self.snapshot = snapshot

register_schema(ChangeLogSchema)
register_schema(SchemaSnapshotSchema)