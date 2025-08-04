import pytest
import polynom.config as cfg

@pytest.fixture(autouse=True)
def reset_config_state():
    # Backup and restore config to avoid side effects across tests
    original_config = cfg.all_config().copy()
    # Reset lock count manually
    while True:
        try:
            cfg.unlock()
        except RuntimeError:
            break
    yield

    # Reset user-configurable keys
    for key in cfg.USER_CONFIGURABLE_KEYS:
        try:
            cfg.set(key, original_config[key])
        except RuntimeError:
            pass  # Config might be locked
    # Ensure lock count is 0 again
    while True:
        try:
            cfg.unlock()
        except RuntimeError:
            break

def test_get_internal():
    assert cfg.get(cfg.INTERNAL_NAMESPACE) == 'polynom_internal'
    assert cfg.get(cfg.CHANGE_LOG_TABLE) == 'change_log'

def test_get_user_configurable():
    assert cfg.get(cfg.DEFAULT_NAMESPACE) == 'polynom_entities'
    assert cfg.get(cfg.DEFAULT_USER) == 'pa'

def test_get_derived():
    derived = cfg.get(cfg.CHANGE_LOG_IDENTIFIER)
    assert isinstance(derived, str)
    assert derived == "polynom_internal.change_log"

def test_set_user_configurable():
    cfg.set(cfg.DEFAULT_NAMESPACE, 'test_ns')
    assert cfg.get(cfg.DEFAULT_NAMESPACE) == 'test_ns'

def test_set_invalid_key_raises():
    with pytest.raises(KeyError):
        cfg.set('INVALID_KEY', 'value')

def test_get_invalid_key_raises():
    with pytest.raises(KeyError):
        cfg.get('INVALID_KEY')

def test_set_config_bulk_update():
    overrides = {
        cfg.DEFAULT_NAMESPACE: 'custom',
        cfg.DEFAULT_USER: 'new_user'
    }
    cfg.set_config(overrides)
    assert cfg.get(cfg.DEFAULT_NAMESPACE) == 'custom'
    assert cfg.get(cfg.DEFAULT_USER) == 'new_user'

def test_lock_blocks_set():
    cfg.lock()
    with pytest.raises(RuntimeError, match="locked"):
        cfg.set(cfg.DEFAULT_NAMESPACE, 'locked_value')

def test_lock_blocks_bulk_update():
    cfg.lock()
    with pytest.raises(RuntimeError, match="locked"):
        cfg.set_config({cfg.DEFAULT_USER: 'blocked_user'})

def test_unlock_allows_updates_again():
    cfg.lock()
    cfg.unlock()
    cfg.set(cfg.DEFAULT_NAMESPACE, 'unlocked_value')
    assert cfg.get(cfg.DEFAULT_NAMESPACE) == 'unlocked_value'

def test_multiple_locks():
    cfg.lock()
    cfg.lock()
    with pytest.raises(RuntimeError):
        cfg.set(cfg.DEFAULT_NAMESPACE, 'nope')
    cfg.unlock()
    with pytest.raises(RuntimeError):
        cfg.set(cfg.DEFAULT_NAMESPACE, 'still nope')
    cfg.unlock()
    cfg.set(cfg.DEFAULT_NAMESPACE, 'finally allowed')
    assert cfg.get(cfg.DEFAULT_NAMESPACE) == 'finally allowed'

def test_unlock_more_than_locked_raises():
    with pytest.raises(RuntimeError):
        cfg.unlock()
