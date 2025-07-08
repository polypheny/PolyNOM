---
layout: page
title: "Overview"
toc: true
docs_area: "PolyNOM"
tags: overview, model, session, application, connection
lang: en
---

## Ecosystem

The Polypheny Native Object Mapper (PolyNOM) ecosystem is structured into four layers:

1. **Instances**  
   Deployment of the Polypheny database management system.  

2. **Applications**  
   Individual applications that operate on an instance of Polypheny. 
   - Each application operates within a single Polypheny instance.
   - Multiple applications can access the same instance.  

3. **Sessions**  
   Sessions represent isolated execuiton environments within an application.  
   - Zero or more sessions can exist within an application.  
   - Each session has its own connection to the instance.  
   - Operations within a session are isolated from other sessions.

4. **Models**  
   Python objects representing data entries.  
   - Each instance of a model corresponds to a single entry belonging to an entity.  
   - An entity is what a relational database management system would refer to as a table.  
   - An entry is what a relational database management system would refer to as a row.

## Context Management

For each layer in the PolyNOM ecosystem, a corresponding python class is provided to encapsulate the relevant functionality. Each layer class can only be instantiated in the context of its respective higher layer class. The `Application` connects to an `Instance`. A `Session` must be created inside an active `Application`. A `Model` must be created within an active `Session`. All layer classes implement Python’s context manager protocol (`__enter__` / `__exit__`). This allows usage with the `with` statement to guarantee proper resource handling, maintain correct contextual relationships and to automatically clean up or close resources when exiting a scope.

### Example:

```python
from polynom.application import Application
from polynom.session import Session
from myproject.bike.model import Bike

APP_UUID = 'a8817239-9bae-4961-a619-1e9ef5575eff'

app = Application(APP_UUID, ('localhost', 20590))
with app:
    session = Session(app)
    with session:
        bike = Bike('Giant', 'Defy', 'Advanced 2', 8.6, 2000)
        session.add(bike)
        session.commit()
```
