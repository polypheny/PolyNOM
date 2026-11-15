# PolyNOM — Polypheny Native Object Mapper

PolyNOM currently maps Python model instances to rows in relational tables in [Polypheny](https://polypheny.com). Use sessions to insert, query, update, and delete model instances in a transaction. PolyNOM can create missing tables from registered schemas and offers optional schema migration and statement logging.

## Installation

You need Python 3.11 or later and a Polypheny server with a compatible Prism 2.x interface. PolyNOM uses the Python connector version `>=2,<3`. The package name on PyPI is `polypheny-polynom`, and the module name is `polynom`.

```sh
python -m pip install polypheny-polynom
```

To install the version from this repository, run `python -m pip install .` from the checkout.

## Quick start

Start Polypheny with its plain Prism interface on port 20590. The example uses the default local credentials. For another server, pass its address, `user`, and `password` to `Application`. Choose one application UUID and reuse it across runs so PolyNOM can identify the application's schema snapshot.

```python
from polynom.application import Application
from polynom.model.model import BaseModel
from polynom.schema.field import Field
from polynom.schema.polytypes import VarChar
from polynom.schema.schema import BaseSchema
from polynom.schema.schema_registry import polynom_schema
from polynom.session import Session


@polynom_schema
class ContactSchema(BaseSchema):
    namespace_name = "polynom_example"
    entity_name = "polynom_contacts"
    fields = [Field("name", VarChar(80), nullable=False)]


class Contact(BaseModel):
    schema = ContactSchema()

    def __init__(self, name, _entry_id=None):
        super().__init__(_entry_id)
        self.name = name


with Application("9cfe6791-0333-4689-9b77-37a83161fa93", ("127.0.0.1", 20590)) as app:
    with Session(app) as session:
        contact = Contact("Ada Lovelace")
        session.add(contact)
        contact_id = contact._entry_id
        session.commit()

    with Session(app) as session:
        saved = Contact.query(session).get(contact_id)
        print(saved.name)
```

Enable schema migration with `Application(..., migrate=True)` when you want PolyNOM to apply changes to existing tables. For Docker-managed startup, configure `POLYPHENY_IMAGE_NAME` with a compatible Prism 2.x image in `polynom.config` before opening an application with `use_docker=True`.

## Development

Run these commands from the repository root. Start a disposable Polypheny instance for the integration tests, which create and delete test data. Set `POLYNOM_TEST_HOST` and `POLYNOM_TEST_PORT` to override the defaults of `127.0.0.1` and `20590`.

```sh
python -m pip install -e '.[dev]'
python -m pytest
```

Run the tests that do not require a database with `python -m pytest -m 'not integration'`.

## Further reading

- [Application and session lifecycle](https://github.com/polypheny/PolyNOM/blob/main/docs/overview.md)
- [Schemas and models](https://github.com/polypheny/PolyNOM/blob/main/docs/models.md)
- [Writing queries](https://github.com/polypheny/PolyNOM/blob/main/docs/query.md)
- [Apache License 2.0](https://github.com/polypheny/PolyNOM/blob/main/LICENSE)
