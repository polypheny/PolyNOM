import pytest
import polynom.schema.schema_registry as schema_registry
from polynom.schema.field import Field, ForeignKeyField
from polynom.schema.schema import BaseSchema
from polynom.schema.polytypes import Text

# independent schemas

class SchemaA(BaseSchema):
    entity_name = 'a'
    fields = [
        Field('first', Text)
    ]

class SchemaB(BaseSchema):
    entity_name = 'b'
    fields = [
        Field('first', Text)
    ]

# simple chain

class SchemaRefsBtoA(BaseSchema):
    entity_name = 'refs_b_to_a'
    fields = [
        ForeignKeyField('first', Text, referenced_entity_name='a', referenced_db_field_name='first')
    ]

# cycle free multiple foreign keys

class SchemaRefsAandB(BaseSchema):
    entity_name = 'refs_a_and_b'
    fields = [
        ForeignKeyField('first', Text, referenced_entity_name='a', referenced_db_field_name='first'),
        ForeignKeyField('first', Text, referenced_entity_name='b', referenced_db_field_name='first'),
    ]

# cycle 1

class SchemaAwithFKtoB(BaseSchema):
    entity_name = 'a'
    fields = [
        Field('first', Text),
        ForeignKeyField('first', Text, referenced_entity_name='b', referenced_db_field_name='first')
    ]

class SchemaBwithFKtoA(BaseSchema):
    entity_name = 'b'
    fields = [
        Field('first', Text),
        ForeignKeyField('first', Text, referenced_entity_name='a', referenced_db_field_name='first')
    ]

# cycle 2

class SchemaAwithFKtoB(BaseSchema):
    entity_name = 'a'
    fields = [
        Field('first', Text),
        ForeignKeyField('first', Text, referenced_entity_name='b', referenced_db_field_name='first')
    ]

class SchemaBwithFKtoC(BaseSchema):
    entity_name = 'b'
    fields = [
        Field('first', Text),
        ForeignKeyField('first', Text, referenced_entity_name='c', referenced_db_field_name='first')
    ]

class SchemaCwithFKtoA(BaseSchema):
    entity_name = 'c'
    fields = [
        Field('first', Text),
        ForeignKeyField('first', Text, referenced_entity_name='a', referenced_db_field_name='first')
    ]

# self loop

class SchemaAwithSelfFK(BaseSchema):
    entity_name = 'a'
    fields = [
        Field('first', Text),
        ForeignKeyField('first', Text, referenced_entity_name='a', referenced_db_field_name='first')
    ]

# test cases

def test_sort_by_foreign_key_independent():
    input = set([SchemaA, SchemaB])
    output = schema_registry._sort_by_foreign_key(input)
    expected = (
        [SchemaA, SchemaB],
        [SchemaB, SchemaA]
    )
    assert output in expected

def test_sort_by_foreign_key_simple_chain():
    input = set([SchemaA, SchemaRefsBtoA])
    output = schema_registry._sort_by_foreign_key(input)
    expected = [SchemaA, SchemaRefsBtoA]
    assert output == expected

def test_sort_by_foreign_key_chain_multiple_fk():
    input = set([SchemaA, SchemaB, SchemaRefsAandB])
    output = schema_registry._sort_by_foreign_key(input)
    expected = (
        [SchemaA, SchemaB, SchemaRefsAandB],
        [SchemaB, SchemaA, SchemaRefsAandB]
    )
    assert output in expected

def test_sort_by_foreign_key_cycle_1():
    input = set([SchemaAwithFKtoB, SchemaBwithFKtoA])
    with pytest.raises(RuntimeError):
        schema_registry._sort_by_foreign_key(input)

def test_sort_by_foreign_key_cycle_2():
    input = set([SchemaAwithFKtoB, SchemaBwithFKtoC, SchemaCwithFKtoA])
    with pytest.raises(RuntimeError):
        schema_registry._sort_by_foreign_key(input)