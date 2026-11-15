import polypheny
import logging
import polynom.config as cfg
import polynom.docker as docker
from contextlib import ExitStack
from enum import Enum, auto
from polynom.schema.migration import Migrator
from polynom.session import Session
from polynom.statement import Statement
from polynom.schema.schema_registry import _get_ordered_schemas, _to_dict
from polynom.schema.schema import DataModel
from polynom.reflection import SchemaSnapshot, SchemaSnapshotSchema
from polynom.statement import _SqlGenerator
from polynom.dump import _dump, _load, _compare_snapshots

logger = logging.getLogger(__name__)

class _ApplicationState(Enum):
    INITIALIZED = auto()
    ACTIVE = auto()
    COMPLETED = auto()

class Application:
    def __init__(
            self,
            app_uuid: str,
            address,
            user: str = cfg.get(cfg.DEFAULT_USER),
            password: str = cfg.get(cfg.DEFAULT_PASS),
            transport: str = cfg.get(cfg.DEFAULT_TRANSPORT),
            use_docker: bool = False,
            migrate: bool = False,
            stop_container: bool = False,
            remove_container: bool = False,
            log_statements: bool = False
        ):
        self._app_uuid = app_uuid
        self._address = address
        self._user = user
        self._password = password
        self._transport = transport
        self._use_docker = use_docker
        self._migrate = migrate
        self._stop_container = stop_container
        self._remove_container = remove_container
        self._log_statements = log_statements

        self._conn = None
        self._cursor = None
        self._resources = ExitStack()
        self._state = _ApplicationState.INITIALIZED

    def __enter__(self):
        if self._state != _ApplicationState.INITIALIZED:
            raise ValueError("Application must only be initialized once.")
        try:
            with ExitStack() as resources:
                cfg.lock()
                resources.callback(cfg.unlock)

                if self._use_docker:
                    docker._deploy_polypheny(self._address, self._user, self._password, self._transport)
                    container = cfg.get(cfg.POLYPHENY_CONTAINER_NAME)
                    if self._remove_container:
                        resources.callback(docker._remove_container_by_name, container)
                    if self._stop_container:
                        resources.callback(docker._stop_container_by_name, container)

                self._conn = polypheny.connect(
                    self._address,
                    username=self._user,
                    password=self._password,
                    transport=self._transport
                )
                resources.callback(self._conn.close)
                self._cursor = self._conn.cursor()
                resources.callback(self._cursor.close)

                self._state = _ApplicationState.ACTIVE
                self._verify_schema()
                self._process_schemas()
                self._resources = resources.pop_all()
        except BaseException:
            self._mark_completed()
            raise
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            return self._resources.__exit__(exc_type, exc_val, exc_tb)
        finally:
            self._mark_completed()

    def _mark_completed(self):
        self._cursor = None
        self._conn = None
        self._state = _ApplicationState.COMPLETED

    def _verify_schema(self):
        self._process_schema(SchemaSnapshotSchema)

        session = Session(self)
        with session:
            logger.debug(f"Reading schema snapshot from database for application {self._app_uuid}.")
            previous = SchemaSnapshot.query(session).get(self._app_uuid)
            current_snapshot = _to_dict()

            if not previous:
                logger.debug(f"No schema snapshot found for application {self._app_uuid}. Creating a first one.")
                previous = SchemaSnapshot(current_snapshot, _entry_id=self._app_uuid)
                session.add(previous)
                session.commit()
                return

            logger.debug(f"Checking for schema changes for application {self._app_uuid}.")
            diff = _compare_snapshots(previous.snapshot, current_snapshot)

            if diff and self._migrate:
                logger.debug(f"Schema changes for application {self._app_uuid} found.")
                migrator = Migrator()
                migrator.run(session, diff)

            previous.snapshot = current_snapshot
            session.commit()

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

        statement = generator._create_namespace(namespace, data_model, if_not_exists=True)
        self._log_statement(statement)
        statement.execute(self._cursor)
        logger.debug(f"Created namespace {namespace} if absent.")

        statement = generator._define_entity(schema_class, if_not_exists=True)
        self._log_statement(statement)
        statement.execute(self._cursor)
        self._conn.commit()

        logger.debug(f"Created entity {entity} if absent.")
    
    def _log_statement(self, statement: Statement):
        if not self._log_statements:
            return
        statement.log(self._app_uuid)
        
    
    def dump(self, file_path):
        if self._state != _ApplicationState.ACTIVE:
            message = f'Application {self._app_uuid} must first be activated by using it in a "with" block'
            logger.error(message)
            raise RuntimeError(message)
        _dump(self, file_path)
    
    def load(self, file_path):
        if self._state != _ApplicationState.ACTIVE:
            message = f'Application {self._app_uuid} must first be activated by using it in a "with" block'
            logger.error(message)
            raise RuntimeError(message)
        _load(self, file_path)
