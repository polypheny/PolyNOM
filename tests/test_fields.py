import pytest
import polynom.schema.schema_registry as schema_registry
from polynom.schema.field import _BaseField, Field, ForeignKeyField, PrimaryKeyField
from polynom.schema.schema import BaseSchema
from polynom.schema.polytypes import Text

def test_base_defaults():
    field = _BaseField('test', Text())
    assert field._db_field_name == 'test'
    assert isinstance(field._polytype, Text)
    assert field._python_field_name == field._db_field_name
    assert field._previous_name == None

def test_base_extended():
    field = _BaseField('db_test', Text(), 'python_test', previous_name='prev_test')
    assert field._db_field_name == 'db_test'
    assert isinstance(field._polytype, Text)
    assert field._python_field_name == 'python_test'
    assert field._previous_name == 'prev_test'

def test_field_default():
    field = Field('test', Text())
    assert field._db_field_name == 'test'
    assert isinstance(field._polytype, Text)
    assert field._python_field_name == field._db_field_name
    assert field._previous_name == None
    assert field.nullable == True
    assert field.default == None
    assert field.unique == False

def test_field_extended_1():
    field = Field('test', Text(), nullable=True, default='default', unique=True, python_field_name='py_test', previous_name='prev_test')
    assert field._db_field_name == 'test'
    assert isinstance(field._polytype, Text)
    assert field._python_field_name == 'py_test'
    assert field._previous_name == 'prev_test'
    assert field.nullable == True
    assert field.default == 'default'
    assert field.unique == True

def test_field_extended_2():
    field = Field('test', Text(), nullable=False, default='default', unique=False, python_field_name='py_test', previous_name='prev_test')
    assert field._db_field_name == 'test'
    assert isinstance(field._polytype, Text)
    assert field._python_field_name == 'py_test'
    assert field._previous_name == 'prev_test'
    assert field.nullable == False
    assert field.default == 'default'
    assert field.unique == False

def test_primary_key_default():
    field = PrimaryKeyField('test', Text())
    assert field._db_field_name == 'test'
    assert isinstance(field._polytype, Text)
    assert field._python_field_name == field._db_field_name
    assert field._previous_name == None
    assert field.nullable == False
    assert field.unique == False
    assert field.default == None

def test_primary_key_extended():
    field = PrimaryKeyField('test', Text(), python_field_name='py_test', previous_name='prev')
    assert field._db_field_name == 'test'
    assert isinstance(field._polytype, Text)
    assert field._python_field_name == 'py_test'
    assert field._previous_name == 'prev'
    assert field.nullable == False
    assert field.unique == False
    assert field.default == None

def tets_foreign_key_defaults():
    class SchemaA(BaseSchema):
        namespace_name = 'my_namespace'
        entity_name = 'a'
        fields = [
            Field('test', Text())
        ]

    field = ForeignKeyField('a_id', SchemaA)
    assert field._db_field_name == 'a_id'
    assert isinstance(field._polytype, Text)
    assert field.referenced_namespace_name == SchemaA.namespace_name
    assert field.referenced_entity_name == SchemaA.entity_name
    assert field.referenced_db_field_name == '_entry_id'
    assert field.nullable == True
    assert field.unique == False
    assert field._python_field_name == field._db_field_name
    assert field._previous_name == None

def tets_foreign_key_defaults_1():
    class SchemaA(BaseSchema):
        namespace_name = 'my_namespace'
        entity_name = 'a'
        fields = [
            Field('test', Text())
        ]

    field = ForeignKeyField('a_id', SchemaA, referenced_db_field_name='foo')
    assert field._db_field_name == 'a_id'
    assert isinstance(field._polytype, Text)
    assert field.referenced_namespace_name == SchemaA.namespace_name
    assert field.referenced_entity_name == SchemaA.entity_name
    assert field.referenced_db_field_name == 'foo'
    assert field.nullable == True
    assert field.unique == False
    assert field._python_field_name == field._db_field_name
    assert field._previous_name == None

def tets_foreign_key_extended():
    class SchemaA(BaseSchema):
        namespace_name = 'my_namespace'
        entity_name = 'a'
        fields = [
            Field('test', Text())
        ]

    field = ForeignKeyField('a_id', SchemaA, referenced_db_field_name='foo', nullable=False, unique=True, python_field_name='py_test', previous_name='prev_test')
    assert field._db_field_name == 'a_id'
    assert isinstance(field._polytype, Text)
    assert field.referenced_namespace_name == SchemaA.namespace_name
    assert field.referenced_entity_name == SchemaA.entity_name
    assert field.referenced_db_field_name == 'foo'
    assert field.nullable == False
    assert field.unique == True
    assert field._python_field_name == 'py_test'
    assert field._previous_name == 'prev_test'

