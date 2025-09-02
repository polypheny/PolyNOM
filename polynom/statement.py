from polynom.statement_logger import LoggerFactory
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Tuple
from polynom.schema.schema import DataModel
from polynom.schema.field import PrimaryKeyField, ForeignKeyField

@dataclass
class Statement:
    language: str
    statement: str
    values: Tuple[Any, ...] = None
    namespace: str = None

    def execute(self, cursor: Any) -> Any:
        return cursor.executeany(
            self.language,
            self.statement,
            self.values,
            namespace=self.namespace
        )

    def dump(self) -> str:
        if self.language == "sql" and self.values:
            parts = self.statement.split("?")
            rebuilt = parts[0]
            for part, val in zip(parts[1:], self.values):
                rebuilt += self._format_value(val) + part
            stmt = rebuilt
        else:
            stmt = self.statement

        namespace_comment = f'{self.language}@{self.namespace}' if self.namespace else f'{self.language}@None'
        return f'/*{namespace_comment}*/ {stmt}'
    
    def log(self, app_uuid: str = None) -> str:
        if not app_uuid:
            raise ValueError("app_uuid must be provided for logging")
        logger = LoggerFactory.get_logger(app_uuid)
        logger.info(self.dump())
    
    @staticmethod
    def _format_value(value: Any) -> str:
        if isinstance(value, str):
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        return str(value)

class _BaseGenerator(ABC):
    @abstractmethod
    def _insert(self, model) -> Statement:
        pass

    @abstractmethod
    def _update(self, model) -> Statement:
        pass

    @abstractmethod
    def _delete(self, model) -> Statement:
        pass

    @abstractmethod
    def _create_namespace(self, namespace: str, datamodel: DataModel, if_not_exists: bool = False) -> Statement:
        pass

    @abstractmethod
    def _drop_namespace(self, namespace: str, if_exists: bool = False) -> Statement:
        pass

    @abstractmethod
    def _define_entity(self, schema, if_not_exists: bool = False) -> Statement:
        pass

    @abstractmethod
    def _drop_entity(self, schema, if_exists: bool = False) -> Statement:
        pass

class _SqlGenerator(_BaseGenerator):
    LANGUAGE = 'sql'

    def _insert(self, model) -> Statement:
        entity = model.schema.entity_name
        namespace = model.schema.namespace_name
        data = model._to_dict()

        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        values = list(data.values())

        sql = f'INSERT INTO "{namespace}"."{entity}" ({columns}) VALUES ({placeholders})'

        return Statement(
            namespace=namespace,
            language=self.LANGUAGE,
            statement=sql,
            values=values
        )

    def _update(self, model) -> Statement:
        entity = model.schema.entity_name
        namespace = model.schema.namespace_name
        data = model._to_dict()

        if not hasattr(model, "_entry_id") or model._entry_id is None:
            raise ValueError("Model must have an _entry_id to perform update.")

        data.pop('_entry_id', None)  # Ensure it's not part of SET clause

        set_clause = ', '.join(f"{col} = ?" for col in data.keys())
        values = list(data.values())
        values.append(model._entry_id)

        sql = f'UPDATE "{namespace}"."{entity}" SET {set_clause} WHERE _entry_id = ?'

        return Statement(
            namespace=namespace,
            language=self.LANGUAGE,
            statement=sql,
            values=values
        )

    def _delete(self, model) -> Statement:
        entity = model.schema.entity_name
        namespace = model.schema.namespace_name

        sql = f'DELETE FROM "{namespace}"."{entity}" WHERE _entry_id = ?'

        return Statement(
            namespace=namespace,
            language=self.LANGUAGE,
            statement=sql,
            values=(model._entry_id,)
        )
    
    def _create_namespace(self, namespace: str, datamodel: DataModel, if_not_exists: bool = False) -> Statement:
        option = 'IF NOT EXISTS ' if if_not_exists else ''
        sql = f'CREATE {datamodel.value} NAMESPACE {option}"{namespace}"'

        return Statement(
            language=self.LANGUAGE,
            statement=sql
        )

    def _drop_namespace(self, namespace: str, if_exists: bool = False) -> Statement:
        option = 'IF EXISTS ' if if_exists else ''
        statement = f'DROP NAMESPACE {option}"{namespace}"'
        
        return Statement(
            namespace=namespace,
            language=self.LANGUAGE,
            statement=statement
        )
    
    def _define_entity(self, schema, if_not_exists: bool = False) -> Statement:
        data_model = schema.data_model
        if data_model is not DataModel.RELATIONAL:
            raise ValueError("This generator cannot create definitions for nonrelational entities.")

        entity = schema.entity_name
        namespace = schema.namespace_name
        fields = schema._get_fields()

        column_defs = []
        foreign_keys = []
        unique_columns = []
        primary_key_columns = []

        for field in fields:
            col_def = f'"{field._db_field_name}" {field._polytype._type_string}'
            if not getattr(field, 'nullable', False):
                col_def += " NOT NULL"
            default_value = getattr(field, 'default', None)
            if default_value is not None:
                col_def += f" DEFAULT {field._polytype._to_sql_expression(default_value)}"
            if getattr(field, 'unique', False):
                unique_columns.append(field._db_field_name)
            if isinstance(field, PrimaryKeyField):
                primary_key_columns.append(field._db_field_name)
            column_defs.append(col_def)

            if isinstance(field, ForeignKeyField):
                fk = (
                    f'FOREIGN KEY ("{field._db_field_name}") '
                    f'REFERENCES "{field.referenced_namespace_name}"."{field.referenced_entity_name}"("{field.referenced_db_field_name}")'
                )
                foreign_keys.append(fk)

        constraints = foreign_keys[:]
        if primary_key_columns:
            constraints.append(f"PRIMARY KEY ({', '.join(primary_key_columns)})")
        constraints += [f'UNIQUE ("{col}")' for col in unique_columns]

        option = 'IF NOT EXISTS ' if if_not_exists else ''
        create_stmt = f'CREATE TABLE {option}"{namespace}"."{entity}" ({", ".join(column_defs + constraints)});'

        return Statement(
            namespace=namespace,
            language=self.LANGUAGE,
            statement=create_stmt
        )
    
    def _drop_entity(self, schema, if_exists: bool = False) -> Statement:
        option = 'IF EXISTS ' if if_exists else ''
        namespace = schema.namespace_name
        entity = schema.entity_name
        statement = f'DROP TABLE {option}"{namespace}"."{entity}"'
        
        return Statement(
            namespace=namespace,
            language=self.LANGUAGE,
            statement=statement
        )

def get_generator_for_data_model(data_model: DataModel) -> _BaseGenerator:
    match data_model:
        case DataModel.RELATIONAL:
            return _SqlGenerator()
        case DataModel.DOCUMENT:
            raise NotImplementedError("Document query generation not implemented yet.")
        case DataModel.GRAPH:
            raise NotImplementedError("Graph query generation not implemented yet.")
        case _:
            raise ValueError(f"Unsupported data model: {data_model}")
