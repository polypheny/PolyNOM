from orm.model import BaseModel
from orm.schema.schema_registry import register_schema
from orm.schema.schema import BaseSchema
from orm.schema.field import Field
from orm.schema.polytypes import Timestamp, Text, Json
from orm.constants import INTERNAL_NAMESPACE, CHANGE_LOG_TABLE, SNAPSHOT_TABLE

class ChangeLogSchema(BaseSchema):
    entity_name = CHANGE_LOG_TABLE
    namespace_name = INTERNAL_NAMESPACE
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
    entity_name = SNAPSHOT_TABLE
    namespace_name = INTERNAL_NAMESPACE
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