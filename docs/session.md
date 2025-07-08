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
with app.create_session(log_user="alice") as session:
    session.add(my_model) # this will work
```

## Operations

#### `add(model: BaseModel, tracking=True)`
Adds a model instance to the session, preparing it for insertion on the underlying polypheny instance.

- `tracking`: Wether to track changes performed to the added model after insertions. Changes to the model then trigger automatic updates on the associated entity on the underlying Polypheny instance. This is the default behaviour. Setting this to 'False' is considered experimental and thus not recommended for most use cases.

---

#### `add_all(models: Iterable[BaseModel])`

Adds multiple models to the session. Equivalent to calling `add()` repeatedly.

---

#### `delete(model: BaseModel)`

Marks a model for deletion from the database. The model must have a valid `_entry_id`.

---

#### `delete_all(models: Iterable[BaseModel])`

Deletes multiple models. Equivalent to calling `delete()` repeatedly.

---

#### `flush()`

Writes all in-session modifications (updates to tracked models) to the database, but does **not** commit the transaction.

- Detects model changes via `model._diff()`
- Persists diffs
- Updates associated change logs

---

#### `commit()`

Finalizes the session and commits all pending inserts, updates, and deletions to the database.

- Calls `flush()` internally.
- Invalidates all tracked models after commit.
- Marks session as `COMPLETED`.

---

#### `rollback()`

Discards all changes made during the session.

- Invalidates all tracked models.
- Rolls back the transaction.
- Marks session as `COMPLETED`.

---

#### `get_session_state() → _SessionState`

Returns the current state of the session:

- `INITIALIZED`
- `ACTIVE`
- `COMPLETED`

---

#### `detach_child(parent: BaseModel, attr_name: str)`

Detaches a related child model from its parent by relationship name.  
If the relationship is configured with `"delete-orphan"`, the child will also be deleted if it becomes unreferenced.

- `parent`: The parent model instance.
- `attr_name`: The name of the relationship attribute to detach.
