---
layout: page
title: "Query"
toc: true
docs_area: "PolyNOM"
tags: query, filter, search, manipulation
lang: en
---

## Query

This page discusses the retrieval of data. This involves three classes. Namely those are the `Session`, `Model` and the `Query` class. Each retrieval triggers queries on the underlying polypheny instance and must thus take place as part of a `Session`. To avoid the need for user written statements, the `Query` class provides a variety of methods for filtering as well as calculations. Each `Model` provides a corresponding instance of the `Query` class by its `query` method:

### `query(session: Session)`

Returns a `Query` instance that can be used to query entries of the type of the Model class.

- `session` (`Session`): The session under as part of which to execute the query. 

## Filter Methods
Filter methods are the first type of method provided by a `Query` instance. Filter methods allow to define restriction to filter the entries to be returned. Filter methods always return a `Query` instance allowing them to be chained to bulid more copmlex filters.

### `filter_by(**kwargs) → Query`
Adds simple equality filters to the query based on model fields.  

- `**kwargs`: Key-value pairs where keys are model attribute names and values are the values to filter by. Their format is `key=value` (e.g. last_name='meyer').

Returns the updated `Query` instance to allow the chaining of query methods.

---

#### `filter(*expressions) → Query`
Adds complex filter expressions to the query. Each expression must be a tuple of `(operator, field, value)`.  

- `expressions`: Tuples specifying conditions.  
- `operator`: A string SQL operator (e.g., `"="`, `">"`).  
- `field`: A `Field` object representing a model field.  
- `value`: The value to compare against.

Returns the updated `Query` instance to allow the chaining of query methods.

---

### `distinct() → Query`
Marks the query to return only distinct results.

Returns the updated `Query` instance to allow the chaining of query methods.

---

### `limit(n: int) → Query`
Limits the number of results returned by the query.  

- `n`: Maximum number of entries to return.

Returns the updated `Query` instance to allow the chaining of query methods.

---

#### `order_by(field_name: str) → Query`
Specifies a field to order the query results by.  

- `field_name`: The name of the model field to sort by.  
Raises `ValueError` if the field does not exist.

Returns the updated `Query` instance to allow the chaining of query methods.

---

### `join(related_model: Type[BaseModel], on: Optional[str] = None) → Query`
Adds a JOIN to include related models in the query.  

- `related_model`: The model class to join.  
- `on` (optional): Custom join condition as a SQL string. If omitted, the system attempts to infer the join based on foreign keys.

Returns the updated `Query` instance to allow the chaining of query methods.

---

### `options(*opts) → Query`
Applies query options, such as eager-loading instructions.  

- `*opts`: Option objects to apply. Currently supports `JoinedLoad` for eager loading of related models.  
Returns the updated `Query` instance to allow the chaining of query methods.


## Result Methods
Result methods are the secon type of method provided by a `Query` instance. Result methods trigger the execution of the `Query` instance and return a method specific result.

### `all() → List[BaseModel]`
Executes the query and returns all matching model instances.

Returns a list of model instances. Related children are attached according to any configured eager loads.

---

### `first() → Optional[BaseModel]`
Fetches the first row matching the query, if any.  

Returns a single model instance if a row exists; otherwise, `None`.

---

### `exists() → bool`
Checks whether any records exist matching the current query filters.  

Returns `True` if at least one matching row exists; otherwise, `False`.

---

#### `count() → int`
Counts the number of entries matching the current query filters.  
Returns an integer representing the number of matching entries.

---

### `delete() → int`
Deletes all model instances matching the current query.  

Returns the number of models deleted.

---

### `update(values: Dict[str, Any]) → int`
Updates all models matching the current query with the specified field values.  

- `values`: Dictionary mapping model field names to new values.  
Returns the number of models updated.  
Raises `AttributeError` if a field in `values` does not exist on the model.

---


### `get(pk_value: Any) → Optional[BaseModel]`
Fetches a single entry by its primary key.  

- `pk_value`: The value of the primary key to search for.  
Returns the model instance if found; otherwise, `None`.  
Raises `ValueError` if the model does not have a `PrimaryKeyField`.

---


