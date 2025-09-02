---
layout: page
title: "Dump"
toc: true
docs_area: "PolyNOM"
tags: backup, dump, load, import
lang: en
---

# Dump

The database state of a PolyNOM application can be persisted into a multi-language query (MLQ) file. While this procedure is explained in detail in the application documentation, this page takes a closer look at the MLQ file generated.

## Structure

Every MLQ file is split into two sections. The first section is the header containing meta-information about the file. The second section contains the statements in one or more query languages. MLQ is a format extending traditional SQL dumps. MLQ focuses on reverse compatibility with traditional SQL dumps in cases where the only query language used in the dump is SQL. Therefore, all extensions are wrapped in comments to be ignored by traditional systems.

## Header

The header of an MLQ file is a multiline comment containing three key-value pairs prefixed with an `@` symbol.

- **@format_version**: Denotes the format used for the MLQ dump. As of now, the corresponding value is always `1`. If the MLQ format is extended in the future, this number will be increased to enable differentiation and proper parsing.

- **@app_uuid**: The application UUID of the application from which the dump originates. This ensures that dumps are only loaded by the appropriate application.

- **@snapshot**: A JSON string representing a list of all schemas defined by the application from which the dump originated. This can be used to easily check for schema changes. It is used on load to verify that the schema to be created by the dump actually matches the expectations of the application loading the dump.

## Statements

The header is followed by a series of statements in one or more query languages. Each line begins with a comment of the form:

```sql
/*language@namespace*/
```

- `language` specifies the query language used for the following statement.
- `namespace` specifies in which namespace the statement should be executed.

## Example
Below an example of a short application dump as an MLQ is shown:

```sql
/*
@format_version: 1
@app_uuid: a8817239-9bae-4961-a619-1e9ef5575eff
@snapshot: {"version": "20250902T084338", "schemas": [{"entity_name": "User", "namespace_name": "polynom_entities", "data_model": "RELATIONAL", "fields": [{"name": "_entry_id", "db_name": "_entry_id", "type": "VarChar", "previous_name": null, "nullable": false, "unique": true, "default": null, "is_primary_key": true, "is_foreign_key": false}, {"name": "username", "db_name": "username", "type": "VarChar", "previous_name": "username2", "nullable": false, "unique": true, "default": null, "is_primary_key": false, "is_foreign_key": false}, {"name": "email", "db_name": "email", "type": "VarChar", "previous_name": null, "nullable": false, "unique": true, "default": null, "is_primary_key": false, "is_foreign_key": false}, {"name": "first_name", "db_name": "first_name", "type": "VarChar", "previous_name": null, "nullable": true, "unique": false, "default": null, "is_primary_key": false, "is_foreign_key": false}, {"name": "last_name", "db_name": "last_name", "type": "VarChar", "previous_name": null, "nullable": true, "unique": false, "default": null, "is_primary_key": false, "is_foreign_key": false}, {"name": "active", "db_name": "active", "type": "Boolean", "previous_name": null, "nullable": true, "unique": false, "default": null, "is_primary_key": false, "is_foreign_key": false}, {"name": "is_admin", "db_name": "is_admin", "type": "Boolean", "previous_name": null, "nullable": true, "unique": false, "default": null, "is_primary_key": false, "is_foreign_key": false}]}, {"entity_name": "Bike", "namespace_name": "polynom_entities", "data_model": "RELATIONAL", "fields": [{"name": "_entry_id", "db_name": "_entry_id", "type": "VarChar", "previous_name": null, "nullable": false, "unique": true, "default": null, "is_primary_key": true, "is_foreign_key": false}, {"name": "brand", "db_name": "brand", "type": "VarChar", "previous_name": null, "nullable": false, "unique": false, "default": null, "is_primary_key": false, "is_foreign_key": false}, {"name": "model", "db_name": "model", "type": "VarChar", "previous_name": null, "nullable": false, "unique": false, "default": null, "is_primary_key": false, "is_foreign_key": false}, {"name": "owner_id", "db_name": "owner_id", "type": "VarChar", "previous_name": null, "nullable": false, "unique": null, "default": false, "is_primary_key": false, "is_foreign_key": true, "references_namespace": "polynom_entities", "references_entity": "User", "references_field": "_entry_id"}]}]}
*/
/*sql@None*/ CREATE RELATIONAL NAMESPACE IF NOT EXISTS "polynom_internal"
/*sql@None*/ CREATE RELATIONAL NAMESPACE IF NOT EXISTS "polynom_entities"
/*sql@polynom_entities*/ CREATE TABLE IF NOT EXISTS "polynom_entities"."User" ("_entry_id" VARCHAR(36) NOT NULL, "username" VARCHAR(80) NOT NULL, "email" VARCHAR(80) NOT NULL, "first_name" VARCHAR(30), "last_name" VARCHAR(30), "active" BOOLEAN, "is_admin" BOOLEAN, PRIMARY KEY (_entry_id), UNIQUE ("_entry_id"), UNIQUE ("username"), UNIQUE ("email"));
/*sql@polynom_entities*/ INSERT INTO "polynom_entities"."User" (_entry_id, username, email, first_name, last_name, active, is_admin) VALUES ('93a8779e-3c40-4baf-a7a5-27765effd6f8', 'testuser', 'u1@demo.ch', 'max', 'muster', TRUE, FALSE)
/*sql@polynom_entities*/ INSERT INTO "polynom_entities"."User" (_entry_id, username, email, first_name, last_name, active, is_admin) VALUES ('1c87088a-7a23-47e5-be1d-6891b097138f', 'testuser2', 'u2@demo.ch', 'mira', 'muster', FALSE, TRUE)
/*sql@polynom_entities*/ INSERT INTO "polynom_entities"."User" (_entry_id, username, email, first_name, last_name, active, is_admin) VALUES ('0a6a071a-8fc3-470d-bec1-bb9adf7a0015', 'testuser3', 'u3@demo.ch', 'miraculix', 'musterin', FALSE, TRUE)
/*sql@polynom_entities*/ INSERT INTO "polynom_entities"."User" (_entry_id, username, email, first_name, last_name, active, is_admin) VALUES ('a09435c6-6037-4d8e-aba0-8d2d67063945', 'testuser4', 'u4@demo.ch', 'maxine', 'meier', TRUE, FALSE)
/*sql@polynom_entities*/ INSERT INTO "polynom_entities"."User" (_entry_id, username, email, first_name, last_name, active, is_admin) VALUES ('d63a89b6-f339-4e5e-955a-4d36ad5edb37', 'testuser5', 'u5@demo.ch', 'mia', 'müller', FALSE, FALSE)
/*sql@polynom_entities*/ CREATE TABLE IF NOT EXISTS "polynom_entities"."Bike" ("_entry_id" VARCHAR(36) NOT NULL, "brand" VARCHAR(50) NOT NULL, "model" VARCHAR(50) NOT NULL, "owner_id" VARCHAR(36) NOT NULL DEFAULT 'False', FOREIGN KEY ("owner_id") REFERENCES "polynom_entities"."User"("_entry_id"), PRIMARY KEY (_entry_id), UNIQUE ("_entry_id"));
/*sql@polynom_entities*/ INSERT INTO "polynom_entities"."Bike" (_entry_id, brand, model, owner_id) VALUES ('d48d23ac-a308-45f0-9250-86fdde8d58dd', 'Trek', 'Marlin 7', '93a8779e-3c40-4baf-a7a5-27765effd6f8')
/*sql@polynom_entities*/ INSERT INTO "polynom_entities"."Bike" (_entry_id, brand, model, owner_id) VALUES ('ba13bb9a-40cc-437a-8b66-8a8b00bb5f6d', 'Specialized', 'Rockhopper', '93a8779e-3c40-4baf-a7a5-27765effd6f8')
/*sql@polynom_entities*/ INSERT INTO "polynom_entities"."Bike" (_entry_id, brand, model, owner_id) VALUES ('040ecfde-db16-4a3f-bb6a-4e93331b0925', 'Cannondale', 'Trail 8', '0a6a071a-8fc3-470d-bec1-bb9adf7a0015')
/*sql@polynom_entities*/ INSERT INTO "polynom_entities"."Bike" (_entry_id, brand, model, owner_id) VALUES ('7c36a17b-deb8-45e5-91da-0c33943504ec', 'Giant', 'Talon 3', 'a09435c6-6037-4d8e-aba0-8d2d67063945')

```