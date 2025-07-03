from orm.session.session import Session

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

            print(changes)
            # Handle table rename
            previous_table_name = entity_diff.get('previous_name')    
            if previous_table_name and previous_table_name != table_name:
                qualified_previous_table_name = self._quote_identifier(namespace_name, previous_table_name)
                statement = f'ALTER TABLE {qualified_previous_table_name} RENAME TO "{table_name}"'
                self.statements_with_namespace.append((namespace_name, statement))

            for field_name, (old_field, new_field) in changes.items():
                # Drop column
                if old_field and not new_field:
                    statement = f'ALTER TABLE {qualified_table_name} DROP COLUMN "{field_name}"'
                    self.statements_with_namespace.append((namespace_name, statement))

                # Add column
                elif new_field and not old_field:
                    statement = self._generate_add_column_statement(qualified_table_name, new_field)
                    self.statements_with_namespace.append((namespace_name, statement))

                # Rename column
                elif old_field and new_field and old_field.get('name') != new_field.get('name'):
                    previous_field_name = new_field.get('previous_name')
                    if previous_field_name and previous_field_name != new_field['name']:
                        statement = (
                            f'ALTER TABLE {qualified_table_name} '
                            f'RENAME COLUMN "{previous_field_name}" TO "{new_field["name"]}"'
                        )
                        self.statements_with_namespace.append((namespace_name, statement))

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
            else:
                modifications.append(
                    f'ALTER TABLE {qualified_table_name} MODIFY COLUMN {quoted_column_name} SET NOT NULL'
                )

        if old_field.get('default') != new_field.get('default'):
            if new_field.get('default') is not None:
                modifications.append(
                    f'ALTER TABLE {qualified_table_name} MODIFY COLUMN {quoted_column_name} '
                    f'SET DEFAULT {new_field["default"]}'
                )
            else:
                modifications.append(
                    f'ALTER TABLE {qualified_table_name} MODIFY COLUMN {quoted_column_name} DROP DEFAULT'
                )

        if old_field.get('type') != new_field.get('type'):
            modifications.append(
                f'ALTER TABLE {qualified_table_name} MODIFY COLUMN {quoted_column_name} SET TYPE {new_field["type"]}'
            )

        return modifications

    def run(self, session: Session, diff: dict):
        self._generate_statements(diff)
        for namespace_name, statement in self.statements_with_namespace:
            print(statement)
            session._execute('sql', statement, namespace=namespace_name, fetch=False)

