from __future__ import annotations
import logging

from polynom.statement import Statement

logger = logging.getLogger(__name__)

class Migrator:
    def __init__(self):
        self.statements_with_namespace = []

    def _quote_identifier(self, *parts):
        return '.'.join(f'"{part}"' for part in parts if part)

    def _generate_statements(self, diff):
        for table_name, entity_diff in diff.items():
            namespace_name = entity_diff.get('namespace_name')
            qualified_table_name = self._quote_identifier(namespace_name, table_name)

            changes = entity_diff.get('changes', {})

            # Handle table rename
            previous_table_name = entity_diff.get('previous_name')    
            if previous_table_name and previous_table_name != table_name:
                qualified_previous_table_name = self._quote_identifier(namespace_name, previous_table_name)
                statement = f'ALTER TABLE {qualified_previous_table_name} RENAME TO "{table_name}"'
                self.statements_with_namespace.append((namespace_name, statement))
                logger.info(f"Rename entity{qualified_previous_table_name} to {table_name}.")

            for field_name, (old_field, new_field) in changes.items():
                # Drop column
                if old_field and not new_field:
                    statement = f'ALTER TABLE {qualified_table_name} DROP COLUMN "{field_name}"'
                    self.statements_with_namespace.append((namespace_name, statement))
                    logger.info(f"Remove field {field_name} from entity{qualified_table_name}.")

                # Add column
                elif new_field and not old_field:
                    statement = self._generate_add_column_statement(qualified_table_name, new_field)
                    self.statements_with_namespace.append((namespace_name, statement))
                    logger.info(f"Add field {new_field} to entity{qualified_table_name}.")

                # Rename column
                elif old_field and new_field and old_field.get('name') != new_field.get('name'):
                    previous_field_name = new_field.get('previous_name')
                    new_field_name = new_field['name']
                    if previous_field_name and previous_field_name != new_field_name:
                        statement = (
                            f'ALTER TABLE {qualified_table_name} '
                            f'RENAME COLUMN "{previous_field_name}" TO "{new_field_name}"'
                        )
                        self.statements_with_namespace.append((namespace_name, statement))
                        logger.info(f"Rename field {previous_field_name} in entity{qualified_table_name} to {new_field_name}.")

                # Modify column (if changed)
                if old_field and new_field and old_field != new_field:
                    modification_statements = self._generate_column_modification_statements(
                        qualified_table_name,
                        new_field['name'],
                        old_field,
                        new_field
                    )
                    for modification in modification_statements:
                        self.statements_with_namespace.append((namespace_name, modification))

    def _generate_add_column_statement(self, qualified_table_name, field):
        column_definition = self._column_definition(field)
        return f'ALTER TABLE {qualified_table_name} ADD COLUMN {column_definition}'

    def _column_definition(self, field):
        column_name = f'"{field["name"]}"'
        data_type = field['type']
        nullability = 'NULL' if field.get('nullable', True) else 'NOT NULL'
        default_value = f'DEFAULT {field["default"]}' if field.get('default') is not None else ''
        return f"{column_name} {data_type} {nullability} {default_value}".strip()

    def _generate_column_modification_statements(self, qualified_table_name, column_name, old_field, new_field):
        modifications = []
        quoted_column_name = f'"{column_name}"'

        if old_field.get('nullable') != new_field.get('nullable'):
            if new_field['nullable']:
                modifications.append(
                    f'ALTER TABLE {qualified_table_name} MODIFY COLUMN {quoted_column_name} DROP NOT NULL'
                )
                logger.info(f"Make field {column_name} in entity {qualified_table_name} nullable.")
            else:
                modifications.append(
                    f'ALTER TABLE {qualified_table_name} MODIFY COLUMN {quoted_column_name} SET NOT NULL'
                )
                logger.info(f"Make field {column_name} in entity {qualified_table_name} not nullable.")

        if old_field.get('default') != new_field.get('default'):
            if new_field.get('default') is not None:
                modifications.append(
                    f'ALTER TABLE {qualified_table_name} MODIFY COLUMN {quoted_column_name} '
                    f'SET DEFAULT {new_field["default"]}'
                )
                logger.info(f'Set default value for field {column_name} in entity {qualified_table_name} to {new_field["default"]}.')
            else:
                modifications.append(
                    f'ALTER TABLE {qualified_table_name} MODIFY COLUMN {quoted_column_name} DROP DEFAULT'
                )
                logger.info(f'Remove default value for field {column_name} in entity {qualified_table_name}.')

        if old_field.get('type') != new_field.get('type'):
            modifications.append(
                f'ALTER TABLE {qualified_table_name} MODIFY COLUMN {quoted_column_name} SET TYPE {new_field["type"]}'
            )
            logger.info(f'Set data type of field {column_name} in entity {qualified_table_name} to {new_field["type"]}.')

        return modifications

    def run(self, session: Session, diff: dict):
        logger.info("Performing automatic schema migration...")
        self._generate_statements(diff)
        for namespace_name, statement in self.statements_with_namespace:
            logger.debug(f"Migration: namespace={namespace_name}, statement={statement}")
            
            current_statement = Statement(
                language='sql',
                statement=statement,
                namespace=namespace_name 
            )
            session._application._log_statement(current_statement)
            session._execute(current_statement, fetch=False)
        logger.info("Automatic schema migration complete.")

