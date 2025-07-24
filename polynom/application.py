import polypheny
import logging
import polynom.config as cfg
import polynom.docker as docker
from polynom.schema.migration import Migrator
from polynom.session import Session
from polynom.schema.schema_registry import _get_ordered_schemas, _to_json
from polynom.schema.schema import DataModel
from polynom.reflection import SchemaSnapshot, SchemaSnapshotSchema
from polynom.model import FlexModel
from polynom.statement import _SqlGenerator, get_generator_for_data_model

logger = logging.getLogger(__name__)

class Application:
    def __init__(
            self,
            app_uuid: str,
            address,
            user: str = cfg.get(cfg.DEFAULT_USER),
            password: str = cfg.get(cfg.DEFAULT_PASS),
            transport: str = cfg.get(cfg.DEFAULT_TRANSPORT),
            use_docker: bool = True,
            migrate: bool = False,
            stop_container: bool = False,
            remove_container: bool = False
        ):
        cfg.lock()

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
            docker._deploy_polypheny(self._address, self._user, self._password, self._transport)

        self._conn = polypheny.connect(
            self._address,
            username=self._user,
            password=self._password,
            transport=self._transport
        )
        self._cursor = self._conn.cursor()

        self._verify_schema()
        self._process_schemas()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._cursor:
            self._cursor.close()
        if self._conn:
            self._conn.close()
        
        if not self._use_docker:
            return
        if self._stop_container:
            docker._stop_container_by_name(cfg.get(cfg.POLYPHENY_CONTAINER_NAME))
        if self._remove_container:
            docker._remove_container_by_name(cfg.get(cfg.POLYPHENY_CONTAINER_NAME))
        cfg.unlock()

    def _verify_schema(self):
        self._process_schema(SchemaSnapshotSchema)

        session = Session(self)
        with session:
            logger.debug(f"Reading schema snapshot from database for application {self._app_uuid}.")
            previous = SchemaSnapshot.query(session).get(self._app_uuid)
            current_snapshot = _to_json()

            if not previous:
                logger.debug(f"No schema snapshot found for application {self._app_uuid}. Creating a first one.")
                previous = SchemaSnapshot(current_snapshot, _entry_id=self._app_uuid)
                session.add(previous)
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

    def _process_schemas(self):
        for schema in _get_ordered_schemas():
            self._process_schema(schema)

    def _process_schema(self, schema_class):
        entity = schema_class.entity_name
        namespace = schema_class.namespace_name
        data_model = schema_class.data_model

        logger.info(f"Initializing entity {entity} in namespace {namespace}.")

        if data_model is not DataModel.RELATIONAL:
            raise NotImplementedError("Non-relational entities are not yet supported!")
        
        generator = _SqlGenerator()

        generator._create_namespace(namespace, data_model, if_not_exists=True).execute(self._cursor)
        logger.debug(f"Created namespace {namespace} if absent.")

        generator._define_entity(schema_class).execute(self._cursor)
        self._conn.commit()

        logger.debug(f"Created entity {entity} if absent.")

    def dump(self, file_path: str):
        namespaces = []
        with open(file_path, 'w') as file:
            with Session(self) as session:
                for schema in _get_ordered_schemas():
                    sql_generator = _SqlGenerator()
                    namespace = schema.namespace_name
                    data_model = schema.data_model

                    if namespace not in namespaces:
                        namespaces.append(namespace)
                        file.write(sql_generator._create_namespace(namespace, data_model).dump())

                    generator = get_generator_for_data_model(data_model)
                    model = FlexModel.from_schema(schema)
                    entries = model.query(session).all()
                    for entry in entries:
                        file.write(generator._insert(entry).dump())
    
    def load_dump():
        pass
