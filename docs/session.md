---
layout: page
title: "Session"
toc: true
docs_area: "PolyNOM"
tags: session, model, schema, isolation
lang: en
---

## Session

The `Session` class represents an isolated, transactional unit of work within a Polypheny `Application`. Each session manages a set of data operations (insertions, updates, deletions) on models while keeping changes scoped to that session until explicitly committed.

- Acts as a transactional layer within an `Application`.
- Provides isolation: each session is independent of others.
- Tracks changes to models and optionally propagates cascading updates or deletions.
- Supports full lifecycle management through commit/rollback.
- Compatible with Python context managers to ensure proper initialization and cleanup.

## Initialization Parameters
```python
Session(
    application: Application,
    log_user: str = None
)
```

- `application` (`Application`, required):  
  The application the new session will be part of. 

- `log_user` (`str`, optional):  
  PolyNOM offers a changelog functionality were committed changes are recorded for future reference or auditing. The provided `log_user` is an identifier stored in the changelog that can be used to retrieve the correpsonding changes in the future. This defaults to 'None' which thereby disables the changelog features for this session.


## Activation

A session must be activated via a context block to become operational. Outside the context block, session operations will raise errors.

```python
with Session(app, log_user="alice") as session:
    session.add(my_model)
```

## Operations

#### `add(model: BaseModel, tracking=True)`
Adds a model instance to the session, preparing it for insertion on the underlying polypheny instance. Changes to the added model are automatically tracked triggering updates on the underlying Polypheny instance.

- `tracking` (`bool`, optional): Wether to track changes performed to the added model after insertions. Changes to the model then trigger automatic updates on the associated entity on the underlying Polypheny instance. This is the default behaviour. Setting this to 'False' is considered experimental and thus not recommended for most use cases.

---

#### `add_all(models: Iterable[BaseModel], tracking=True)`

Adds multiple models to the session. Equivalent to calling `add()` repeatedly.

- `tracking` (`bool`, optional): Wether to track changes performed to the added model after insertions. Changes to the model then trigger automatic updates on the associated entity on the underlying Polypheny instance. This is the default behaviour. Setting this to 'False' is considered experimental and thus not recommended for most use cases.

---

#### `delete(model: BaseModel)`

Marks a model for deletion from the database. After this operation, changes to the model are no longer tracked and the model is invalidated.

---

#### `delete_all(models: Iterable[BaseModel])`

Deletes multiple models. Equivalent to calling `delete()` repeatedly.

---

#### `flush()`

Writes all cached updates to tracked models to the database **without** commiting. The flush operation is called automatically before query execution if required.

---

#### `commit()`

Finalizes the session and commits all pending inserts, updates, and deletions to the database. This invalidates all tracked models and finalizes the session. After this operation any further operations on the session or modifications of the invalidated models raise errors.

---

#### `rollback()`

Discards all changes made as part of this session. This invalidates all tracked models and finalizes the session. After this operation any further operations on the session or modifications of the invalidated models raise errors.

---

#### `_execute(language, statement, parameters=None, namespace=None, fetch=True)`

Executes a statement using the session's internal cursor. This method supports both DDL and DML operations across different query languages (e.g., SQL, Cypher, MQL).

- `language`: The query language to use (e.g., `'sql'`, `'cypher'`, `'mongo'`).
- `statement`: The statement string to be executed.
- `parameters` (optional): A dictionary of parameters to bind in the statement. Parameterization is currently only supported for SQL.
- `namespace` (optional): The namespace in which to execute the statement. If not specified or set to None, the default namespace specified in the PolyNOM config is used.
- `fetch` (optional, default=`True`): If `True`, the result of the query is returned if present. If set to `False` no results are retrieved independent of the query type.
---

#### `get_session_state() → _SessionState`

Returns the current state of the session.

- `INITIALIZED`: The session had been created but not yet activated.
- `ACTIVE`: The session is active.
- `COMPLETED`: The session had been finalized by either a `commit()` or a `rollback()`. Any further session operations raise errors. 

---

#### `detach_child(parent: BaseModel, attr_name: str)`

Detaches a related child model from its parent by relationship name.  
If the relationship is configured with `"delete-orphan"`, the child will also be deleted if it becomes unreferenced.

- `parent`: The parent model instance.
- `attr_name`: The name of the relationship attribute to detach.


## Examples
```python
from polynom.application import Application
from polynom.session import Session
from myproject.bike.model import Bike

APP_UUID = 'a8817239-9bae-4961-a619-1e9ef5575eff'

with Application(APP_UUID, ('localhost', 20590)) as app:
    with Session(app) as session:
        bike = Bike('Canyon', 'Aeroad', 'CFR Di2', 7.04, 8849)
        session.add(bike)
        bike.price = 7000
        session.commit()
```
