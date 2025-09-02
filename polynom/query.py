from __future__ import annotations

import logging

from typing import Type, List, Optional, Dict, Any, TYPE_CHECKING, Tuple
from polynom.schema.field import PrimaryKeyField, ForeignKeyField

if TYPE_CHECKING:
    from polynom.session import Session
    from polynom.model.model import BaseModel
    
logger = logging.getLogger(__name__)

class Query:
    def __init__(self, model_cls: Type[BaseModel], session: Session):
        self._session = session
        self._model_cls = model_cls
        self._distinct = False
        self._filters: Dict[str, Any] = {}
        self._limit: Optional[int] = None
        self._order_by: Optional[str] = None
        self._joins: List[str] = []
        self._eager_loads: List[Tuple[str, Type[BaseModel]]] = []

        for field in model_cls.schema._get_fields():
            if not hasattr(model_cls, field._python_field_name):
                setattr(model_cls, field._python_field_name, field)

    def filter_by(self, **kwargs) -> "Query":
        self._filters.update(kwargs)
        return self

    def filter(self, *expressions):
        for expr in expressions:
            if not isinstance(expr, tuple) or len(expr) != 3:
                raise ValueError("Invalid filter expression")
            op, field, value = expr
            
            clause = f'"{field}" {op} ?'
            self._filters.setdefault('_extra_clauses', []).append((clause, value))
        return self

    def distinct(self) -> "Query":
        self._distinct = True
        return self

    def limit(self, n: int) -> "Query":
        self._limit = n
        return self

    def order_by(self, field_name: str) -> "Query":
        field = next((f for f in self._model_cls.schema.fields if f._python_field_name == field_name), None)
        if not field:
            raise ValueError(f"Unkown field {field_name} for model {self._model_cls.__name__}")
        self._order_by = field._db_field_name
        return self

    def count(self) -> int:
        table = self._model_cls.schema.entity_name
        where_clause, values = self._build_where_clause()
        sql = f'SELECT COUNT(*) FROM "{table}"'
        if where_clause:
            sql += f" {where_clause}"
        self._session.flush()
        cursor = self._session._cursor
        cursor.execute(sql, values)
        return cursor.fetchone()[0]

    def get(self, pk_value: Any) -> Optional[BaseModel]:
        pk_field = next(
            (f for f in self._model_cls.schema._get_fields() if isinstance(f, PrimaryKeyField)),
            None
        )
        if not pk_field:
            raise ValueError(f"No PrimaryKeyField found for model {self._model_cls.__name__}.")

        sql = f'SELECT * FROM "{self._model_cls.schema.entity_name}" WHERE "{pk_field._db_field_name}" = ?'
        self._session.flush()
        cursor = self._session._cursor
        cursor.execute(sql, (pk_value,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            model = self._model_cls._from_dict(dict(zip(columns, row)))
            self._session._track(model) #ToDo AG: isch das richtig so?
            return model
        return None

    def exists(self) -> bool:
        sql, values = self._build_sql()
        sql = sql.replace("SELECT *", "SELECT 1")
        sql += " LIMIT 1"
        self._session.flush()
        cursor = self._session._cursor
        cursor.execute(sql, values)
        return cursor.fetchone() is not None

    def delete(self) -> int:
        models = self.all()
        for model in models:
            self._session.delete(model)
        return len(models)

    def update(self, values: dict[str, Any]) -> int:
        models = self.all()
        count = 0

        for model in models:
            for field_name, value in values.items():
                if not hasattr(model, field_name):
                    raise AttributeError(f"{self._model_cls.__name__} has no attribute '{field_name}'")
                setattr(model, field_name, value)
            count += 1

        return count

    def _build_sql(self):
        base_table = self._model_cls.schema.entity_name
        selected_fields = [f'"{base_table}"."{fld._db_field_name}"' for fld in self._model_cls.schema._get_fields()]

        joins = ""
        alias_counter = 1
        for related_model, on_clause in self._joins:
            related_table = related_model.schema.entity_name
            alias = f"{related_table}_{alias_counter}"
            alias_counter += 1
            if on_clause:
                cond = on_clause
            else:
                fk = next((f for f in related_model.schema._get_fields() if
                           isinstance(f, ForeignKeyField) and f.referenced_entity_name == base_table), None)
                if fk:
                    cond = f'"{alias}"."{fk._db_field_name}" = "{base_table}"."_entry_id"'
                else:
                    fk2 = next((f for f in self._model_cls.schema._get_fields() if
                                isinstance(f, ForeignKeyField) and f.referenced_entity_name == related_table), None)
                    if not fk2:
                        raise ValueError(f"Cannot infer join between {base_table} and {related_table}")
                    cond = f'"{base_table}"."{fk2._db_field_name}" = "{alias}"."{fk2.referenced_db_field_name}"'
            joins += f' LEFT JOIN "{related_table}" AS "{alias}" ON {cond}'
            for fld in related_model.schema._get_fields():
                selected_fields.append(
                    f'"{alias}"."{fld._db_field_name}" AS "{alias}__{fld._db_field_name}"'
                )

        where_clause, values = self._build_where_clause()
        sql = f'SELECT {", ".join(selected_fields)} FROM "{base_table}"{joins}'
        if where_clause:
            sql += f" {where_clause}"
        if self._order_by:
            sql += f' ORDER BY "{self._order_by}"'
        if self._limit is not None:
            sql += f' LIMIT {self._limit}'
        return sql, values

    def _build_where_clause(self):
        if not self._filters:
            return "", []

        clauses = []
        values = []
        for key, value in self._filters.items():
            if key == '_extra_clauses':
                continue
            field = next((f for f in self._model_cls.schema.fields if f._python_field_name == key), None)
            if not field:
                raise ValueError(f"Unknown field '{key}' for model {self._model_cls.__name__}")
            clauses.append(f'"{field._db_field_name}" = ?')
            values.append(value)

        for clause, val in self._filters.get('_extra_clauses', []):
            clauses.append(clause)
            values.append(val)

        where_clause = "WHERE " + " AND ".join(clauses) if clauses else ""
        return where_clause, values

    def all(self) -> List[BaseModel]:
        sql, values = self._build_sql()
        self._session.flush()
        cursor = self._session._cursor
        cursor.execute(sql, values)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in rows:
            row_map = dict(zip(columns, row))
            base_data = {
                f._db_field_name: row_map[f._db_field_name]
                for f in self._model_cls.schema._get_fields()}
            parent = self._model_cls._from_dict(base_data)
            self._session._track(parent)
            parent._session = self._session

            for attr_name, child_cls, alias in self._eager_loads:
                child_data = {}
                all_null = True
                for fld in child_cls.schema._get_fields():
                    col = fld._db_field_name
                    aliased_col = f"{alias}__{col}"
                    val = row_map.get(aliased_col)
                    if val is not None:
                        all_null = False
                    child_data[aliased_col] = val

                if not all_null:
                    child = child_cls._from_dict({
                        f._db_field_name: child_data[f"{alias}__{f._db_field_name}"]
                        for f in child_cls.schema._get_fields()
                    })
                    self._session._track(child)
                    child._session = self._session
                    setattr(parent, attr_name, child)
                else:
                    setattr(parent, attr_name, None)

            results.append(parent)
        return results

    def join(self, related_model: Type[BaseModel], on: Optional[str] = None) -> "Query":
        self._joins.append((related_model, on))
        return self

    def first(self) -> Optional[BaseModel]:
        sql, values = self._build_sql()
        sql += " LIMIT 1"
        self._session.flush()
        cursor = self._session._cursor
        cursor.execute(sql, values)
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            row_dict = dict(zip(columns, row))
            model = self._model_cls._from_dict(row_dict)
            model._session = self._session
            self._session._track(model)
            return model
        return None

    def options(self, *opts) -> "Query":
        for opt in opts:
            from polynom.query.joined_load import JoinedLoad
            if isinstance(opt, JoinedLoad):
                opt.apply(self) # this applies the eagerloading instruction
        return self
