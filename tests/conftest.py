import os

import pytest

from polynom.application import Application
from tests.utils import APP_UUID


@pytest.fixture(scope='module')
def polypheny_address():
    host = os.environ.get('POLYNOM_TEST_HOST', '127.0.0.1')
    port = int(os.environ.get('POLYNOM_TEST_PORT', '20590'))
    return host, port


@pytest.fixture(scope='module')
def app(polypheny_address):
    with Application(APP_UUID, polypheny_address) as application:
        yield application
