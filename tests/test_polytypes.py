import base64
import json
import pytest
from datetime import date, time, datetime
from decimal import Decimal
from enum import Enum
from shapely.geometry import Point

from polynom.schema.polytypes import (
    _BaseType, _TemporalBaseType, PolyEnum, BigInt, Boolean, Date, Decimal as PolyDecimal,
    Double, Integer, Real, SmallInt, Text, Json, Time, Timestamp, TinyInt, VarChar, File, Geometry
)

# Sample enum for PolyEnum tests
class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class TestBaseType:
    def test_to_json_serializable_correct_type(self):
        bt = _BaseType(int)
        assert bt._to_json_serializable(5) == 5

    def test_to_json_serializable_none(self):
        bt = _BaseType(int)
        assert bt._to_json_serializable(None) is None

    def test_to_json_serializable_wrong_type_raises(self):
        bt = _BaseType(int)
        with pytest.raises(TypeError):
            bt._to_json_serializable("string")

    def test_to_sql_expression_null(self):
        bt = _BaseType(int)
        assert bt._to_sql_expression(None) == "NULL"

    def test_to_sql_expression_number(self):
        bt = _BaseType(int)
        assert bt._to_sql_expression(42) == "42"

    def test_to_sql_expression_not_implemented(self):
        class Dummy(_BaseType):
            def __init__(self):
                super().__init__(dict)
        dummy = Dummy()
        with pytest.raises(NotImplementedError):
            dummy._to_sql_expression({"key": "value"})


class TestTemporalBaseType:
    def test_to_json_serializable_datetime(self):
        temp = _TemporalBaseType(datetime)
        dt = datetime(2023, 1, 1, 12, 30)
        assert temp._to_json_serializable(dt) == dt.isoformat()

    def test_to_json_serializable_date(self):
        temp = _TemporalBaseType(date)
        d = date(2023, 1, 1)
        assert temp._to_json_serializable(d) == d.isoformat()

    def test_to_json_serializable_time(self):
        temp = _TemporalBaseType(time)
        t = time(15, 45)
        assert temp._to_json_serializable(t) == t.isoformat()

    def test_to_sql_expression_non_null(self):
        temp = _TemporalBaseType(datetime)
        dt = datetime(2023, 1, 1, 12, 30)
        sql_expr = temp._to_sql_expression(dt)
        assert sql_expr == f"'{dt.isoformat()}'"

    def test_to_sql_expression_null(self):
        temp = _TemporalBaseType(datetime)
        assert temp._to_sql_expression(None) == "NULL"


class TestPolyEnum:
    def test_to_json_serializable_enum(self):
        poly_enum = PolyEnum(Color)
        assert poly_enum._to_json_serializable(Color.RED) == "RED"

    def test_to_json_serializable_none(self):
        poly_enum = PolyEnum(Color)
        assert poly_enum._to_json_serializable(None) is None

    def test_to_json_serializable_wrong_type_raises(self):
        poly_enum = PolyEnum(Color)
        with pytest.raises(TypeError):
            poly_enum._to_json_serializable(123)

    def test_to_prism_serializable(self):
        poly_enum = PolyEnum(Color)
        assert poly_enum._to_prism_serializable(Color.GREEN) == "GREEN"

    def test_from_prism_serializable_valid(self):
        poly_enum = PolyEnum(Color)
        assert poly_enum._from_prism_serializable("BLUE") == Color.BLUE

    def test_from_prism_serializable_invalid_raises(self):
        poly_enum = PolyEnum(Color)
        with pytest.raises(ValueError):
            poly_enum._from_prism_serializable("YELLOW")

    def test_from_prism_serializable_none(self):
        poly_enum = PolyEnum(Color)
        assert poly_enum._from_prism_serializable(None) is None

    def test_to_sql_expression_escaping(self):
        poly_enum = PolyEnum(Color)
        val = Color.RED
        sql_expr = poly_enum._to_sql_expression(val)
        assert sql_expr == "'RED'"


@pytest.mark.parametrize("cls, python_val, expected_sql", [
    (BigInt, 1234567890123, "1234567890123"),
    (Boolean, True, "TRUE"),
    (Boolean, False, "FALSE"),
    (Date, date(2020, 1, 1), "'2020-01-01'"),
    (PolyDecimal, Decimal("123.45"), "123.45"),
    (Double, 3.14159, "3.14159"),
    (Integer, 42, "42"),
    (Real, 3.14, "3.14"),
    (SmallInt, 1, "1"),
    (Text, "hello", "'hello'"),
    (TinyInt, 7, "7"),
])

def test_basic_types_to_sql_expression(cls, python_val, expected_sql):
    instance = cls()
    if cls is Text:
        assert instance._to_sql_expression(python_val) == expected_sql
    else:
        assert instance._to_sql_expression(python_val) == expected_sql


def test_text_escaping():
    txt = Text()
    val = "O'Reilly"
    assert txt._to_sql_expression(val) == "'O''Reilly'"

def test_varchar_requires_length():
    with pytest.raises(ValueError):
        VarChar(None)

def test_varchar_to_sql_expression():
    v = VarChar(10)
    assert v._type_string == "VARCHAR(10)"
    val = "O'Reilly"
    assert v._to_sql_expression(val) == "'O''Reilly'"

def test_decimal_to_json_and_sql():
    dec = PolyDecimal(precision=10, scale=2)
    d = Decimal("123.45")
    assert dec._to_json_serializable(d) == 123.45
    assert dec._to_sql_expression(d) == "123.45"

def test_json_serialization_and_deserialization():
    js = Json()
    d = {"key": "value"}
    json_str = js._to_json_serializable(d)
    assert isinstance(json_str, str)
    assert json.loads(json_str) == d
    assert js._from_prism_serializable(json_str) == d

def test_json_to_sql_expression_escaping():
    js = Json()
    d = {"key": "O'Reilly"}
    sql_expr = js._to_sql_expression(d)
    assert sql_expr == '\'{"key": "O\'\'Reilly"}\''

def test_file_to_json_and_sql():
    f = File()
    data = b"binarydata"
    json_val = f._to_json_serializable(data)
    assert isinstance(json_val, str)
    sql_expr = f._to_sql_expression(data)
    assert sql_expr.startswith("'") and sql_expr.endswith("'")

def test_file_wrong_type_raises():
    f = File()
    with pytest.raises(TypeError):
        f._to_json_serializable("notbytes")

def test_geometry_serialization_and_deserialization():
    geom = Geometry()
    point = Point(1, 2)
    json_str = geom._to_json_serializable(point)
    assert isinstance(json_str, str)
    restored = geom._from_prism_serializable(json_str)
    assert restored.equals(point)

def test_geometry_to_sql_expression():
    geom = Geometry()
    point = Point(1, 2)
    sql_expr = geom._to_sql_expression(point)
    assert sql_expr.startswith("'") and sql_expr.endswith("'")

def test_time_and_timestamp_to_sql_expression():
    t = Time(3)
    tm = time(10, 15, 30)
    assert t._to_sql_expression(tm) == f"'{tm.isoformat()}'"

    ts = Timestamp(6)
    dt = datetime(2023, 7, 1, 12, 0, 0)
    assert ts._to_sql_expression(dt) == f"'{dt.isoformat()}'"

