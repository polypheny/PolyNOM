import json
import re
import logging
import polynom.config as cfg
from polynom.session import Session
from polynom.schema.schema_registry import _get_ordered_schemas, _to_dict
from polynom.statement import _SqlGenerator, Statement, get_generator_for_data_model
from polynom.model.model import FlexModel
from polynom.reflection import ChangeLog

logger = logging.getLogger(__name__)

def _dump(application, file_path: str):
        logger.info("Start dumping data...")
        namespaces = []
        with open(file_path, 'w') as file:
            file.write('/*\n')
            file.write(f'@format_version: {cfg.get(cfg.DUMP_FORMAT_VERSION)}\n')
            file.write(f'@app_uuid: {application._app_uuid}\n')
            file.write(f'@snapshot: {json.dumps(_to_dict())}\n')
            file.write('*/\n')
            with Session(application) as session:
                for schema in _get_ordered_schemas():
                    sql_generator = _SqlGenerator()
                    namespace = schema.namespace_name
                    data_model = schema.data_model

                    if namespace not in namespaces:
                        namespaces.append(namespace)
                        file.write(sql_generator._create_namespace(namespace, data_model, if_not_exists=True).dump())
                        file.write('\n')

                    if schema.entity_name == cfg.get(cfg.SNAPSHOT_TABLE):
                        continue

                    generator = get_generator_for_data_model(data_model)
                    file.write(generator._define_entity(schema, if_not_exists=True).dump())
                    file.write('\n')

                    model = FlexModel.from_schema(schema)
                    
                    if schema.entity_name == cfg.get(cfg.CHANGE_LOG_TABLE):
                        entries = ChangeLog.query(session).filter_by(app_uuid=application._app_uuid).all()
                    else:
                        entries = model.query(session).all()

                    for entry in entries:
                        file.write(generator._insert(entry).dump())
                        file.write('\n')
                session.commit()
        logger.info(f"Dump succesfully written to {file_path}...")

def _load(application, file_path: str):
    logger.info(f'Start reading dump: {file_path}')
    with open(file_path, 'r') as file:
        _verify_header(application, file)
        _drop_database(application)
        _execute_statements(application, file)
            
def _verify_header(application, file):
    # Check start of header
    line = file.readline().strip()
    if line != '/*':
        logger.error("File does not match dump format")
        raise ValueError("File does not match dump format")
        
    # check format version
    line = file.readline().strip()
    if not line.startswith('@format_version:'):
        logger.error("Malformed header in dump file")
        raise ValueError("Malformed header in dump file")
    _, version = line.split(':', 1)
    format_version = int(version.strip())
    if format_version != cfg.get(cfg.DUMP_FORMAT_VERSION):
        logger.error(f"The dump uses a format of version {format_version} which is incompatible to the format of version {cfg.get(cfg.DUMP_FORMAT_VERSION)} used by this application")
        raise ValueError(f"The dump uses a format of version {format_version} which is incompatible to the format of version {cfg.get(cfg.DUMP_FORMAT_VERSION)} used by this application")
        
    # check app uuid
    line = file.readline().strip()
    if not line.startswith('@app_uuid:'):
        logger.error("File does not match dump format")
        raise ValueError("File does not match dump format")
    _, app_uuid = line.split(':', 1)
    app_uuid = app_uuid.strip()
    if app_uuid != application._app_uuid:
        logger.error(f"The dump file originates from another application. This application: {application._app_uuid}, the dump: {app_uuid}")
        raise ValueError(f"The dump file originates from another application. This application: {application._app_uuid}, the dump: {app_uuid}")
    
    logger.info("Dump app uuid verification successful")
        
    # check snapshot
    line = file.readline().strip()
    if not line.startswith('@snapshot:'):
        logger.error("File does not match dump format")
        raise ValueError("File does not match dump format")
    _, snapshot_str = line.split(':', 1)
    try:
        dump_snapshot = json.loads(snapshot_str.strip())
        app_snapshot = _to_dict()
        diff = _compare_snapshots(app_snapshot, dump_snapshot)
        if diff and not application._migrate:
            logger.error("The schema of the application and the dump do not match")
            raise RuntimeError("The schema of the application and the dump do not match")

    except json.JSONDecodeError as e:
        logger.error("Exception while decoding schema snapshot: {e}")
        raise ValueError("Exception while decoding schema snapshot") from e
    
    logger.info("Dump schema verification successful")
        
    line = file.readline().strip()
    if line != '*/':
        logger.error("File does not match dump format")
        raise ValueError("File does not match dump format")


def _compare_snapshots(previous, current):
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

def _drop_database(application):
    logger.info("Dropping database...")
    namespaces = []
    with Session(application) as session:
        for schema in _get_ordered_schemas():
            namespace = schema.namespace_name

            if namespace not in namespaces:
                namespaces.append(namespace)
            
            data_model = schema.data_model
            generator = get_generator_for_data_model(data_model)

            if schema.entity_name == cfg.get(cfg.SNAPSHOT_TABLE):
                # We do not drop the snapthot entity as other application store data here as well.
                # We do not need to delete this applications entry as it has been confirmed to be matching the dump during header validation.
                continue

            if schema.entity_name == cfg.get(cfg.CHANGE_LOG_TABLE):
                logger.debug(f"Dropping changelog records of application {application._app_uuid}")
                ChangeLog.query(session).filter_by(app_uuid=application._app_uuid).delete()
                continue

            logger.debug(f"Dropping entity '{schema.entity_name}' on namespace '{schema.namespace_name}'")
            session._execute(generator._drop_entity(schema))
        
        protected_namespaces = cfg.get(cfg.DROP_PROTECTED_NAMESPACES)
        for namespace in namespaces:
            generator = _SqlGenerator()
            if namespace in protected_namespaces:
                continue
            if namespace == cfg.get(cfg.INTERNAL_NAMESPACE):
                continue
            logger.debug(f"Dropping namespace '{schema.namespace_name}'")
            session._execute(generator._drop_namespace(namespace))
        
        session.commit()
    logger.info("Database dropped sucessfuly")
        
def _execute_statements(application, file):
    pattern = re.compile(r"/\*(\w+)@([\w\-]+|None)\*/\s*(.+)")
    logger.info("Start importing data...")
    with Session(application) as session:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            match = pattern.match(line)
            if not match:
                logger.debug(f"Skipping line {line_number}: no match found.")
                continue

            language, namespace, statement_text = match.groups()
            namespace = None if namespace == "None" else namespace

            statement = Statement(
                language=language,
                namespace=namespace,
                statement=statement_text,
            )

            try:
                logger.debug(statement.dump())
                application._log_statement(statement)
                session._execute(statement, fetch=False)
            except Exception as e:
                logger.error(f"Error executing line {line_number}: {e}")

        session.commit()
    logger.info("Data imported sucessfully")
