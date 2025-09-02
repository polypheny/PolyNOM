
# keys
INTERNAL_NAMESPACE = 'INTERNAL_NAMESPACE'
CHANGE_LOG_TABLE = 'CHANGE_LOG_TABLE'
SYSTEM_USER_NAME = 'SYSTEM_USER_NAME'
SNAPSHOT_TABLE = 'SNAPSHOT_TABLE'
DUMP_FORMAT_VERSION = 'DUMP_FORMAT_VERSION'
DROP_PROTECTED_NAMESPACES = 'DROP_PROTECTED_NAMESPACES'

DEFAULT_NAMESPACE = 'DEFAULT_NAMESPACE'
DEFAULT_DATA_MODEL = 'DEFAULT_DATA_MODEL'
POLYPHENY_CONTAINER_NAME = 'POLYPHENY_CONTAINER_NAME'
POLYPHENY_IMAGE_NAME = 'POLYPHENY_IMAGE_NAME'
POLYPHENY_PORTS = 'POLYPHENY_PORTS'
DEFAULT_TRANSPORT = 'DEFAULT_TRANSPORT'
DEFAULT_USER = 'DEFAULT_USER'
DEFAULT_PASS = 'DEFAULT_PASS'

CHANGE_LOG_IDENTIFIER = 'CHANGE_LOG_IDENTIFIER'

STATEMENT_LOG_FILE_NAME = 'STATEMENT_LOG_FILE_NAME'

# constants
_internals = {
    INTERNAL_NAMESPACE: 'polynom_internal',
    CHANGE_LOG_TABLE: 'change_log',
    SYSTEM_USER_NAME: 'SYSTEM',
    SNAPSHOT_TABLE: 'snapshot',
    DUMP_FORMAT_VERSION: 1,
    DROP_PROTECTED_NAMESPACES: ['public']
}

# user configurables
_config = {
    DEFAULT_NAMESPACE: 'polynom_entities',
    DEFAULT_DATA_MODEL: 'RELATIONAL',
    POLYPHENY_CONTAINER_NAME: 'polypheny',
    POLYPHENY_IMAGE_NAME: 'vogti/polypheny',
    POLYPHENY_PORTS: {
        "20590/tcp": 20590,
        "7659/tcp": 7659,
        "80/tcp": 80,
        "8081/tcp": 8081,
        "8082/tcp": 8082,
    },
    DEFAULT_TRANSPORT: 'plain',
    DEFAULT_USER: 'pa',
    DEFAULT_PASS: '',
    STATEMENT_LOG_FILE_NAME: 'statements.log'
}

# derived options
_derived = {}

def _refresh_derived():
    _derived[CHANGE_LOG_IDENTIFIER] = f"{_internals[INTERNAL_NAMESPACE]}.{_internals[CHANGE_LOG_TABLE]}"

_refresh_derived()

USER_CONFIGURABLE_KEYS = set(_config.keys())

_lock_count = 0

def lock():
    global _lock_count
    _lock_count += 1

def unlock():
    global _lock_count
    if _lock_count == 0:
        raise RuntimeError("Unlock called more times than lock")
    _lock_count -= 1

def get(key: str):
    if key in _config:
        return _config[key]
    elif key in _internals:
        return _internals[key]
    elif key in _derived:
        return _derived[key]
    else:
        raise KeyError(f"Unknown config key: {key}")

def set(key: str, value):
    if key not in USER_CONFIGURABLE_KEYS:
        raise KeyError(f"Cannot set config key: {key}")
    if _lock_count > 0:
        raise RuntimeError("Configuration is locked. No updates are allowed.")
    _config[key] = value
    _refresh_derived()

def set_config(overrides: dict):
    if _lock_count > 0:
        raise RuntimeError("Configuration is locked. No updates are allowed.")
    for key, value in overrides.items():
        set(key, value)

def all_config():
    return {**_internals, **_config, **_derived}
