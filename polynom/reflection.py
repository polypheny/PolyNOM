from polynom.model.model import BaseModel
from polynom.schema.schema_registry import polynom_schema
from polynom.model.model_registry import polynom_model
from polynom.schema.schema import BaseSchema
from polynom.schema.field import Field
from polynom.schema.polytypes import Timestamp, Text, Json
import polynom.config as cfg

@polynom_schema
class ChangeLogSchema(BaseSchema):
    entity_name = cfg.get(cfg.CHANGE_LOG_TABLE)
    namespace_name = cfg.get(cfg.INTERNAL_NAMESPACE)
    fields = [
        Field('app_uuid', Text(), nullable=False),
        Field('modified_entry_id', Text(), nullable=False),
        Field('modified_entity_namespace', Text(), nullable=False),
        Field('modified_entity_name', Text(), nullable=False),
        Field('modified_by', Text(), nullable=False),
        Field('date_of_change', Timestamp(), nullable=False),
        Field('changes', Json(), nullable=False),
    ]

@polynom_model
class ChangeLog(BaseModel):
    schema = ChangeLogSchema()

    def __init__(self, app_uuid: str, modified_entry_id: str, modified_entity_namespace: str, modified_entity_name: str, modified_by: str, date_of_change, changes: dict, _entry_id = None):
        super().__init__(_entry_id)
        self.app_uuid = app_uuid
        self.modified_entry_id = modified_entry_id
        self.modified_entity_namespace = modified_entity_namespace
        self.modified_entity_name = modified_entity_name
        self.modified_by = modified_by
        self.date_of_change = date_of_change
        self.changes = changes

@polynom_schema
class SchemaSnapshotSchema(BaseSchema):
    entity_name = cfg.get(cfg.SNAPSHOT_TABLE)
    namespace_name = cfg.get(cfg.INTERNAL_NAMESPACE)
    fields = [
        Field('snapshot', Json(), nullable=False),
    ]

@polynom_model
class SchemaSnapshot(BaseModel):
    schema = SchemaSnapshotSchema()

    def __init__(self, snapshot: dict, _entry_id = None):
        super().__init__(_entry_id)
        self.snapshot = snapshot
