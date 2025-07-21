import base64
import json
from datetime import date, time, datetime
from decimal import Decimal as PyDecimal
from enum import Enum as PyEnum
from shapely.geometry import mapping, base, shape

class _BaseType:
    def __init__(self, python_type: type):
        self._python_type: type = python_type

    def _to_json_serializable(self, value):
        if value is None:
            return None
        if isinstance(value, self._python_type):
            return value
        raise TypeError(f"Cannot serialize {value} of type {type(value)}. Expected type is {self._python_type}.")

    def _to_prism_serializable(self, value):
        return value

    def _from_prism_serializable(self, value):
        return value

    def _to_sql_expression(self, value):
        if value is None:
            return "NULL"
        serialized = self._to_json_serializable(value)
        if isinstance(serialized, (int, float)):
            return str(serialized)
        raise NotImplementedError(f"SQL expression serialization not implemented for {type(self).__name__}")

class _TemporalBaseType(_BaseType):
    def __init__(self, python_type: type, precision: int = 0):
        super().__init__(python_type)
        self._precision: int = precision

    def _to_json_serializable(self, value):
        if value is None:
            return None
        if isinstance(value, datetime) or isinstance(value, date) or isinstance(value, time):
            return value.isoformat()
        return super()._to_json_serializable(value)

    def _to_sql_expression(self, value):
        if value is None:
            return "NULL"
        return f"'{self._to_json_serializable(value)}'"

class PolyEnum(_BaseType):
    def __init__(self, python_enum: type[PyEnum]):
        super().__init__(python_enum)
        self._type_string: str = 'TEXT'
        self._python_enum: type[PyEnum] = python_enum

    def _to_json_serializable(self, value):
        if value is None:
            return None
        if isinstance(value, self._python_enum):
            return value.name
        return super()._to_json_serializable(value)

    def _to_prism_serializable(self, value):
        return self._to_json_serializable(value)

    def _from_prism_serializable(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return self._python_enum[value]
            except KeyError:
                raise ValueError(f"Invalid enum name: {value}")
        return super()._from_prism_serializable(value)

    def _to_sql_expression(self, value):
        if value is None:
            return "NULL"
        escaped = self._to_json_serializable(value).replace("'", "''")
        return f"'{escaped}'"

class BigInt(_BaseType):
    def __init__(self):
        super().__init__(int)
        self._type_string: str = 'BIGINT'

class Boolean(_BaseType):
    def __init__(self):
        super().__init__(bool)
        self._type_string: str = 'BOOLEAN'

    def _to_sql_expression(self, value):
        if value is None:
            return "NULL"
        return 'TRUE' if value else 'FALSE'

class Date(_BaseType):
    def __init__(self):
        super().__init__(date)
        self._type_string: str = 'DATE'

    def _to_json_serializable(self, value):
        if value is None:
            return None
        return value.isoformat()

    def _to_sql_expression(self, value):
        if value is None:
            return "NULL"
        return f"'{value.isoformat()}'"

class Decimal(_BaseType):
    def __init__(self, precision: int = 64, scale: int = 32):
        super().__init__(PyDecimal)
        self._precision: int = precision
        self._scale: int = scale
        self._type_string: str = f'DECIMAL({self._precision}, {self._scale})'

    def _to_json_serializable(self, value):
        if value is None:
            return None
        return float(value)

    def _to_sql_expression(self, value):
        if value is None:
            return "NULL"
        return str(value)

class Double(_BaseType):
    def __init__(self):
        super().__init__(float)
        self._type_string: str = 'DOUBLE'

class Integer(_BaseType):
    def __init__(self):
        super().__init__(int)
        self._type_string: str = 'INTEGER'

class Real(_BaseType):
    def __init__(self):
        super().__init__(float)
        self._type_string: str = 'REAL'

class SmallInt(_BaseType):
    def __init__(self):
        super().__init__(int)
        self._type_string: str = 'SMALLINT'

class Text(_BaseType):
    def __init__(self):
        super().__init__(str)
        self._type_string: str = 'TEXT'

    def _to_sql_expression(self, value):
        if value is None:
            return "NULL"
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"

class Json(_BaseType):
    def __init__(self):
        super().__init__(dict)
        self._type_string: str = 'TEXT'

    def _to_json_serializable(self, value):
        if value is None:
            return None
        if isinstance(value, dict):
            return json.dumps(value)
        return super()._to_json_serializable(value)

    def _to_prism_serializable(self, value):
        return self._to_json_serializable(value)

    def _from_prism_serializable(self, value):
        if value is None:
            return None
        return json.loads(value)

    def _to_sql_expression(self, value):
        if value is None:
            return "NULL"
        json_value = self._to_json_serializable(value)
        escaped = json_value.replace("'", "''")
        return f"'{escaped}'"


class Time(_TemporalBaseType):
    def __init__(self, precision: int = 0):
        super().__init__(time, precision)
        self._type_string: str = f'TIME({self._precision})'

class Timestamp(_TemporalBaseType):
    def __init__(self, precision: int = 0):
        super().__init__(datetime, precision)
        self._type_string: str = f'TIMESTAMP({self._precision})'

class TinyInt(_BaseType):
    def __init__(self):
        super().__init__(int)
        self._type_string: str = 'TINYINT'

class VarChar(_BaseType):
    def __init__(self, length: int):
        if length is None:
            raise ValueError("VARCHAR requires a length parameter")
        super().__init__(str)
        self._length: int = length
        self._type_string: str = f'VARCHAR({self._length})'

    def _to_sql_expression(self, value):
        if value is None:
            return "NULL"
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"

class File(_BaseType):
    def __init__(self):
        super().__init__(bytes)
        self._type_string: str = 'File'

    def _to_json_serializable(self, value):
        if value is None:
            return None
        if isinstance(value, bytes):
            return base64.b64encode(value).decode('utf-8')
        raise TypeError(f"Expected bytes for File, got {type(value)}")

    def _to_sql_expression(self, value):
        if value is None:
            return "NULL"
        encoded = self._to_json_serializable(value)
        escaped = encoded.replace("'", "''")
        return f"'{escaped}'"

class Geometry(_BaseType):
    def __init__(self):
        super().__init__(base.BaseGeometry)
        self._type_string: str = 'TEXT'

    def _to_json_serializable(self, value):
        if value is None:
            return None
        if isinstance(value, base.BaseGeometry):
            geojson_dict = mapping(value)
            return json.dumps(geojson_dict, separators=(",", ":"))
        return super()._to_json_serializable(value)

    def _to_prism_serializable(self, value):
        return self._to_json_serializable(value)

    def _from_prism_serializable(self, value):
        if value is None:
            return None
        geojson_obj = json.loads(value)
        return shape(geojson_obj)

    def _to_sql_expression(self, value):
        if value is None:
            return "NULL"
        geojson = self._to_json_serializable(value)
        escaped = geojson.replace("'", "''")
        return f"'{escaped}'"

