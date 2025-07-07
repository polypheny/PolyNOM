# Constants
INTERNAL_NAMESPACE = 'internal'
CHANGE_LOG_TABLE = 'change_log'
SYSTEM_USER_NAME = 'SYSTEM'
SNAPSHOT_TABLE = 'snapshot'
DEFAULT_NAMESPACE = 'public'
POLYPHENY_CONTAINER_NAME = 'polypheny'
POLYPHENY_IMAGE_NAME = 'vogti/polypheny'
POLYPHENY_PORTS = {
    "20590/tcp": 20590,
    "7659/tcp": 7659,
    "80/tcp": 80,
    "8081/tcp": 8081,
    "8082/tcp": 8082,
}
DEFAULT_TRANSPORT = 'plain'
DEFAULT_USER = 'pa'
DEFAULT_PASS = ''
SCHEMA_SNAPSHOT_NAME = 'schema.mappingsnap'

# Derived Variables
CHANGE_LOG_IDENTIFIER = f'{INTERNAL_NAMESPACE}.{CHANGE_LOG_TABLE}'

