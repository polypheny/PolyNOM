import polypheny
import docker
import logging
import polynom.constants as cst
from polynom.schema.migration import Migrator
from polynom.session import Session
from docker.errors import DockerException, NotFound, ImageNotFound
from polynom.schema.schema_registry import _get_ordered_schemas, _to_json
from polynom.schema.field import PrimaryKeyField, ForeignKeyField
from polynom.reflection import SchemaSnapshot, SchemaSnapshotSchema

logger = logging.getLogger(__name__)

class Application:
    def __init__(self, app_uuid: str, address, user: str = cst.DEFAULT_USER,
                 password: str = cst.DEFAULT_PASS, transport: str = cst.DEFAULT_TRANSPORT,
                 use_docker: bool = True, migrate: bool = True,
                 stop_container: bool = False, remove_container: bool = False):
        
        self._app_uuid = app_uuid
        self._address = address
        self._user = user
        self._password = password
        self._transport = transport
        self._use_docker = use_docker
        self._migrate = migrate
        self._stop_container = stop_container
        self._remove_container = remove_container

        self._conn = None
        self._cursor = None
        self._initialized = False

    def __enter__(self):
        if self._initialized:
            raise ValueError("Application must only be initialized once.")
        self._initialized = True
        
        if self._use_docker:
            self._deploy_polypheny()

        self._conn = polypheny.connect(
            self._address,
            username=self._user,
            password=self._password,
            transport=self._transport
        )
        self._cursor = self._conn.cursor()

        self._verify_schema()
        self._create_schema()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._cursor:
            self._cursor.close()
        if self._conn:
            self._conn.close()
        
        if not self._use_docker:
            return
        if self._stop_container:
            self._stop_container_by_name(cst.POLYPHENY_CONTAINER_NAME)
        if self._remove_container:
            self._remove_container_by_name(cst.POLYPHENY_CONTAINER_NAME)

    def _deploy_polypheny(self):
        logger.info("Establishing connection to Docker...")
        try:
            client = docker.from_env()
            client.ping()
        except DockerException as e:
            logger.error("Docker is not running or not accessible.")
            raise RuntimeError("Docker is not running or not accessible.") from e

        logger.info(f"Checking for presence of Polypheny container '{cst.POLYPHENY_CONTAINER_NAME}'...")
        try:
            container = client.containers.get(cst.POLYPHENY_CONTAINER_NAME)
            container.start()
            logger.info(f"Container '{cst.POLYPHENY_CONTAINER_NAME}' found and started.")
        except NotFound:
            logger.info("Polypheny container not found. Deploying a new container. This may take a moment...")
            try:
                client.images.pull(cst.POLYPHENY_IMAGE_NAME)
                client.containers.run(
                    cst.POLYPHENY_IMAGE_NAME,
                    name=cst.POLYPHENY_CONTAINER_NAME,
                    ports=cst.POLYPHENY_PORTS,
                    detach=True
                )
                logger.info(f"New Polypheny container '{cst.POLYPHENY_CONTAINER_NAME}' deployed and started.")
            except DockerException as e:
                logger.error(f"Failed to create or run the Polypheny container: {e}")
                raise RuntimeError("Failed to create or run the Polypheny container.") from e

    def _verify_schema(self):
        self._process_schema(SchemaSnapshotSchema)

        session = Session(self, cst.SYSTEM_USER_NAME)
        with session:
            logger.debug(f"Reading schema snapshot from database for application {self._app_uuid}.")
            previous = SchemaSnapshot.query(session).get(self._app_uuid)
            current_snapshot = _to_json()

            if not previous:
                logger.debug(f"No schema snapshot found for application {self._app_uuid}. Creating a first one.")
                previous = SchemaSnapshot(current_snapshot, _entry_id=self._app_uuid)
                session.add(previous, tracking=False)
                session.commit()
                return

            logger.debug(f"Checking for schema changes for application {self._app_uuid}.")
            diff = self._compare_snapshots(previous.snapshot, current_snapshot)

            if diff and self._migrate:
                logger.debug(f"Schema changes for application {self._app_uuid} found.")
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
                    entity_diff['changes'][curr_name] = [prev_fields[prev_name], curr_field]
                    handled_prev_fields.add(prev_name)
                    continue
                if curr_name not in prev_fields:
                    entity_diff['changes'][curr_name] = [None, curr_field]

            for prev_name, prev_field in prev_fields.items():
                if prev_name in handled_prev_fields:
                    continue
                if prev_name not in curr_fields:
                    entity_diff['changes'][prev_name] = [prev_field, None]
                elif prev_fields[prev_name] != curr_fields[prev_name]:
                    entity_diff['changes'][prev_name] = [prev_field, curr_fields[prev_name]]

            if entity_diff['changes']:
                diff[entity_name] = entity_diff

        return diff

    def _process_schema(self, schema_class):
        entity = schema_class.entity_name
        namespace = schema_class.namespace_name
        fields = schema_class._get_fields()

        logger.info(f"Initializing entity {entity} in namespace {namespace}.")

        self._cursor.execute(f'CREATE RELATIONAL NAMESPACE IF NOT EXISTS "{namespace}"')
        logger.debug(f"Created namespace {namespace} if absent.")

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
                    f'REFERENCES "{field.referenced_entity_name}"("{field.referenced_db_field_name}")'
                )
                foreign_keys.append(fk)

        constraints = foreign_keys[:]
        if primary_key_columns:
            constraints.append(f"PRIMARY KEY ({', '.join(primary_key_columns)})")
        constraints += [f'UNIQUE ("{col}")' for col in unique_columns]

        create_stmt = f'CREATE TABLE IF NOT EXISTS "{namespace}"."{entity}" ({", ".join(column_defs + constraints)});'
        self._cursor.executeany('sql', create_stmt, namespace=namespace)
        self._conn.commit()

        logger.debug(f"Created entity {entity} if absent.")

    def _stop_container_by_name(self, container_name):
        try:
            client = docker.from_env()
            client.ping()
            container = client.containers.get(container_name)
            if container.status == 'running':
                container.stop()
            logger.info(f"Container '{container_name}' stopped.")
        except NotFound:
            logger.warning(f"No container named '{container_name}' found.")
        except DockerException as e:
            logger.error(f"Failed to stop the container '{container_name}': {e}")
            raise RuntimeError(f"Failed to stop the container '{container_name}'") from e

    def _remove_container_by_name(self, container_name):
        try:
            client = docker.from_env()
            client.ping()
            container = client.containers.get(container_name)
            container.remove()
            logger.info(f"Container '{container_name}' removed.")
        except NotFound:
            logger.warning(f"No container named '{container_name}' found.")
        except DockerException as e:
            logger.error(f"Failed to remove the container '{container_name}': {e}")
            raise RuntimeError(f"Failed to remove the container '{container_name}'") from e

