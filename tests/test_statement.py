import pytest
from polynom.statement import _SqlGenerator, get_generator_for_data_model, Statement
from polynom.schema.schema import DataModel

def test_simple():
    statement = Statement(
        language='sql',
        statement='select * from emps'
    )
    assert statement.language == 'sql'
    assert statement.statement == 'select * from emps'
    assert statement.values is None
    assert statement.namespace is None

def test_simple_with_namespace():
    statement = Statement(
        language='sql',
        statement='select * from emps',
        namespace='public'
    )
    assert statement.language == 'sql'
    assert statement.statement == 'select * from emps'
    assert statement.namespace == 'public'
    assert statement.values is None

def test_parameterized_single_parameter():
    statement = Statement(
        language='sql',
        statement='SELECT * FROM emps WHERE dept_id = ?',
        values=(42,),
    )
    assert statement.values == (42,)

def test_parameterized_multiple_parameters():
    statement = Statement(
        language='sql',
        statement='SELECT * FROM emps WHERE dept_id = ? AND role = ?',
        values=(42, 'Manager'),
    )
    assert statement.values == (42, 'Manager')

def test_parameterized_single_parameter_with_namespace():
    statement = Statement(
        language='sql',
        statement='SELECT * FROM emps WHERE dept_id = ?',
        values=(42,),
        namespace='test'
    )
    assert statement.namespace == 'test'

def test_dump_no_parameters():
    stmt = Statement(
        language='sql',
        statement='SELECT * FROM emps',
        namespace='public'
    )
    expected = '/*sql@public*/ SELECT * FROM emps'
    assert stmt.dump() == expected

def test_dump_single_parameter():
    stmt = Statement(
        language='sql',
        statement='SELECT * FROM emps WHERE dept_id = ?',
        values=(42,),
        namespace='hr'
    )
    expected = '/*sql@hr*/ SELECT * FROM emps WHERE dept_id = 42'
    assert stmt.dump() == expected

def test_dump_multiple_parameters():
    stmt = Statement(
        language='sql',
        statement='SELECT * FROM emps WHERE dept_id = ? AND active = ? AND name = ?',
        values=(101, True, "O'Brien"),
        namespace='people'
    )
    expected = "/*sql@people*/ SELECT * FROM emps WHERE dept_id = 101 AND active = TRUE AND name = 'O''Brien'"
    assert stmt.dump() == expected

def test_dump_with_null_parameter():
    stmt = Statement(
        language='sql',
        statement='INSERT INTO emps (name, dept_id) VALUES (?, ?)',
        values=('Alice', None),
        namespace='hr'
    )
    expected = "/*sql@hr*/ INSERT INTO emps (name, dept_id) VALUES ('Alice', NULL)"
    assert stmt.dump() == expected

def test_dump_non_sql_language():
    stmt = Statement(
        language='cypher',
        statement='MATCH (n) RETURN n',
        values=(1, 2),
        namespace='graph'
    )
    expected = '/*cypher@graph*/ MATCH (n) RETURN n'
    assert stmt.dump() == expected

def test_dump_missing_namespace():
    stmt = Statement(
        language='sql',
        statement='SELECT 1',
    )
    expected = '/*sql@None*/ SELECT 1'
    assert stmt.dump() == expected

def test_dump_empty_values():
    stmt = Statement(
        language='sql',
        statement='SELECT 1',
        values=()
    )
    expected = '/*sql@None*/ SELECT 1'
    assert stmt.dump() == expected

def test_return_relational_generator():
    generator = get_generator_for_data_model(DataModel.RELATIONAL)
    assert isinstance(generator, _SqlGenerator)

def test_throws_document_generator():
    with pytest.raises(NotImplementedError, match="Document query generation not implemented yet."):
        get_generator_for_data_model(DataModel.DOCUMENT)

def test_throws_graph_generator():
    with pytest.raises(NotImplementedError, match="Graph query generation not implemented yet."):
        get_generator_for_data_model(DataModel.GRAPH)

def test_create_namespace_if_not_exists():
    stmt = _SqlGenerator()._create_namespace('testns', DataModel.RELATIONAL, if_not_exists=True)
    assert stmt.statement == 'CREATE RELATIONAL NAMESPACE IF NOT EXISTS "testns"'

def test_create_namespace_without_if_not_exists():
    stmt = _SqlGenerator()._create_namespace('testns', DataModel.RELATIONAL, if_not_exists=False)
    assert stmt.statement == 'CREATE RELATIONAL NAMESPACE "testns"'

def test_drop_namespace_if_exists():
    stmt = _SqlGenerator()._drop_namespace('testns', if_exists=True)
    assert stmt.statement == 'DROP NAMESPACE IF EXISTS "testns"'
    assert stmt.namespace == 'testns'

def test_drop_namespace_without_if_exists():
    stmt = _SqlGenerator()._drop_namespace('testns', if_exists=False)
    assert stmt.statement == 'DROP NAMESPACE "testns"'
    assert stmt.namespace == 'testns'

def test_drop_entity_if_exists():
    class DummySchema:
        namespace_name = 'ns'
        entity_name = 'table'

    stmt = _SqlGenerator()._drop_entity(DummySchema(), if_exists=True)
    assert stmt.statement == 'DROP TABLE IF EXISTS "ns"."table"'

def test_drop_entity_without_if_exists():
    class DummySchema:
        namespace_name = 'ns'
        entity_name = 'table'

    stmt = _SqlGenerator()._drop_entity(DummySchema(), if_exists=False)
    assert stmt.statement == 'DROP TABLE "ns"."table"'