import polypheny
import docker
from orm.schema.migration import Migrator
from orm.session.session import Session
from docker.errors import DockerException, NotFound, ImageNotFound
from orm.schema.schema_registry import _get_ordered_schemas, _to_json
from orm.schema.field import PrimaryKeyField, ForeignKeyField
from orm.constants import PRISM_PORT, WEBUI_PORT, HTTP_PORT, CONFIG_SERVER_PORT, INFORMATION_SERVER_PORT, SYSTEM_USER_NAME
from orm.reflection.reflection import SchemaSnapshot, SchemaSnapshotSchema

class Initializer:
    def __init__(self, app_uuid: str, host: str, port: int, user: str = "pa", password: str = "", transport: str = 'plain', deploy_on_docker: bool = True, migrate: bool = True):
        self._app_uuid = app_uuid
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._transport = transport
        self._deploy_on_docker = deploy_on_docker
        self._migrate = migrate
        
        self._conn = None
        self._cursor = None

    def __enter__(self):
        self._conn = polypheny.connect(
            (self._host, self._port),
            username=self._user,
            password=self._password,
            transport = self._transport
        )
        self._cursor = self._conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._cursor:
            self._cursor.close()
        if self._conn:
            self._conn.close()

    def run(self):
        if self._deploy_on_docker:
            self._deploy_polypheny()
        with self:
            self._verify_schema()
            self._create_schema()
        
    def _deploy_polypheny(self, container_name="polypheny", prism_port=20591):
        try:
            client = docker.from_env()
            client.ping()
        except DockerException as e:
            raise RuntimeError("Docker is not running or not accessible") from e

        try:
            container = client.containers.get(container_name)
            container.start()
        except NotFound:
            try:
                client.images.pull("polypheny/polypheny")
                client.containers.run(
                    "polypheny/polypheny",
                    name=container_name,
                    ports={
                        "20591/tcp": PRISM_PORT,
                        "8080/tcp": WEBUI_PORT, # TODO TH: adjust this to new port once new container is available
                        "80/tcp": HTTP_PORT,
                        "8081/tcp": CONFIG_SERVER_PORT,
                        "8082/tcp": INFORMATION_SERVER_PORT,
                    },
                    detach=True
                )
            except DockerException as e:
                raise RuntimeError("Failed to create or run the Polypheny container") from e
            
    def _verify_schema(self):
        self._process_schema(SchemaSnapshotSchema)
        session = Session(self._host, self._port, SYSTEM_USER_NAME)
        with session:
            previous = SchemaSnapshot.query(session).get(self._app_uuid)
            current_snapshot = _to_json()

            if not previous:
                previous = SchemaSnapshot(current_snapshot, _entry_id=self._app_uuid)
                session.add(previous, tracking=False) # tracking system not yet initialized on initial setup
                session.commit()
                return
            
            diff = self._compare_snapshots(previous.snapshot, current_snapshot)
            
            if diff and self._migrate:
                migrator = Migrator()
                migrator.run(session, diff)

            previous.snapshot = current_snapshot
            session.commit()

    def _create_schema(self):
        for schema in _get_ordered_schemas():
            self._process_schema(schema)
            
    def _compare_snapshots(self, previous, current):
        diff = {}

        current_schemas = {s['entity_name']: s for s in current['schemas']}
        previous_schemas = {s['entity_name']: s for s in previous['schemas']}

        for entity_name, prev_entity in previous_schemas.items():
            curr_entity = current_schemas.get(entity_name)

            entity_diff = {
                'namespace_name': prev_entity.get('namespace_name'),
                'changes': {}
            }
    
            if not curr_entity:
                diff[entity_name] = entity_diff
                continue

            prev_fields = {f['name']: f for f in prev_entity.get('fields', [])}
            curr_fields = {f['name']: f for f in curr_entity.get('fields', [])}

            handled_prev_fields = set()

            for curr_name, curr_field in curr_fields.items():
                prev_name = curr_field.get('previous_name')
                if prev_name and prev_name in prev_fields:
                    # Renamed field
                    entity_diff['changes'][curr_name] = [
                        prev_fields[prev_name], curr_field
                    ]
                    handled_prev_fields.add(prev_name)
                    continue
                if curr_name not in prev_fields:
                    # New field
                    entity_diff['changes'][curr_name] = [None, curr_field]

            for prev_name, prev_field in prev_fields.items():
                if prev_name in handled_prev_fields:
                    continue
                if prev_name not in curr_fields:
                    # Deleted field
                    entity_diff['changes'][prev_name] = [prev_field, None]
                    continue
                if prev_fields[prev_name] != curr_fields[prev_name]:
                    # Modified field
                    entity_diff['changes'][prev_name] = [
                        prev_fields[prev_name], curr_fields[prev_name]
                    ]

            if entity_diff['changes']:
                diff[entity_name] = entity_diff

        return diff
            
    def _process_schema(self, schema_class):
        entity = schema_class.entity_name
        namespace = schema_class.namespace_name
        fields = schema_class._get_fields()
        
        query = f'CREATE RELATIONAL NAMESPACE IF NOT EXISTS "{namespace}"'
        self._cursor.execute(query)

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
                value_str = field._polytype._to_sql_expression(default_value)
                col_def += f" DEFAULT {value_str}"

            if getattr(field, 'unique', False):
                unique_columns.append(field._db_field_name)
            if isinstance(field, PrimaryKeyField):
                primary_key_columns.append(field._db_field_name)
            column_defs.append(col_def)

            if isinstance(field, ForeignKeyField):
                fk = (
                    f'FOREIGN KEY ("{field._db_field_name}") '
                    f'REFERENCES "{field.referenced_entity_name}"("{field.referenced_db_field_name}")'
                )
                foreign_keys.append(fk)
                
        constraints = foreign_keys[:]
        if primary_key_columns:
            constraints.append(f"PRIMARY KEY ({', '.join(primary_key_columns)})")
        if unique_columns:
            for col in unique_columns:
                constraints.append(f'UNIQUE ("{col}")')

        create_stmt = f'CREATE TABLE IF NOT EXISTS "{namespace}"."{entity}" ({", ".join(column_defs + constraints)});'
        print(create_stmt)
        self._cursor.executeany('sql', create_stmt, namespace=namespace)
        self._conn.commit()
