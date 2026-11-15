from unittest.mock import Mock

import pytest

import polynom.config as cfg
from polynom.application import Application


@pytest.mark.parametrize('startup_fails', [False, True])
def test_application_closes_resources_and_unlocks_configuration(monkeypatch, startup_fails):
    connection = Mock()
    monkeypatch.setattr('polynom.application.polypheny.connect', Mock(return_value=connection))
    app = Application('test-app', ('127.0.0.1', 20590))
    monkeypatch.setattr(app, '_process_schemas', Mock())
    default_user = cfg.get(cfg.DEFAULT_USER)

    def verify_schema():
        with pytest.raises(RuntimeError, match='Configuration is locked'):
            cfg.set(cfg.DEFAULT_USER, default_user)
        if startup_fails:
            raise ValueError('schema setup failed')

    monkeypatch.setattr(app, '_verify_schema', verify_schema)
    if startup_fails:
        with pytest.raises(ValueError, match='schema setup failed'), app:
            pytest.fail('A failed startup must not enter the application')
    else:
        with app:
            connection.close.assert_not_called()

    connection.cursor.return_value.close.assert_called_once()
    connection.close.assert_called_once()
    cfg.set(cfg.DEFAULT_USER, default_user)
    with pytest.raises(ValueError, match='only be initialized once'), app:
        pytest.fail('An application may be opened only once')
