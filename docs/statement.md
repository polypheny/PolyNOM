---
layout: page
title: "Statement"
toc: true
docs_area: "PolyNOM"
tags: query, statement, language
lang: en
---

## Statement

The `Statement` class represents an individual statement to be executed as part of a session. It thereby combines a query language, a statement in that language, optional parameters and an optional namespace to execute the expression in. Statements enable users to write and execute queries directly beyond the methods provided by the `Query` object.

## Initialization Parameters
```python
Statement(
    language: str,
    statement: str,
    values: Tuple[Any, ...] = None,
    namespace: str = None
)
```

- `language` (`str`, required):  
  The name of the query language of the provided statement (e.g., `'sql'`, `'cypher'`, `'mongo'`).

- `statement`:  
  The statement string to be executed. This must be in the query language specified useing the `language` parameter.

- `values` (`str`, optional):  
  If the statement string provided contains placeholders, their values must be specified here. Values are assigned to placeholders from left to right.
  If no placeholders are present no values must be set.

- `namespace` (`str`, optional):  
  The name of the namespace in which the statement should be executed. If not specified the default namespace configured in the PolyNOM config is used.

## Examples
```python
from polynom.application import Application
from polynom.session import Session
from polynom.statement import Statement

APP_UUID = 'a8817239-9bae-4961-a619-1e9ef5575eff'

with Application(APP_UUID, ('localhost', 20590)) as app:
    with Session(app) as session:
        expensive_brands_statement = Statement(
            'sql',
            'SELECT DISTINCT brand FROM bikes WHERE price > ?;',
            (6000,),
            'cycling'
        )
        expensive_brands = session._execute(expensive_brands_statement, fetch=True)
```