---
layout: page
title: "Statement Log"
toc: true
docs_area: "PolyNOM"
tags: backup, dump, file, log
lang: en
---

# Statement Log

Every PolyNOM application maintains a statement log. This log records all committed, data-modifying statements executed by the application. The base name of the log file can be configured using the PolyNOM configuration. The base name is extended by the UUID of the application. A new file is created once the current one reaches a size of 1 GB. The new file's name is further extended with a timestamp of its creation.

**WARNING:** Statement log files are kept indefinitely. It is the user's responsibility to manage and dispose of old logs that are no longer needed.

## File Name

If the base name in the configuration is set to `statements.log`, the first file created might be named: `statements_a8817239-9bae-4961-a619-1e9ef5575eff.log`. Here, the UUID of the application is `a8817239-9bae-4961-a619-1e9ef5575eff`. Once this file reaches 1 GB, a new file is created with a timestamp appended to the name: `statements_a8817239-9bae-4961-a619-1e9ef5575eff.20250902-100915.log`.

## Structure

The statement log contains one statement per line in one or more query languages. Similar to MLQ files used for application dumps, each line begins with comments storing metadata for the statement:

1. **Timestamp comment** – indicates when the entry was created.  
2. **Language and namespace comment** – specifies the query language and the namespace in which the statement was executed.  

Example:

```sql
/*2025-09-02 08:44:06,008*/ /*sql@polynom_entities*/ DELETE FROM "polynom_entities"."User" WHERE _entry_id = '19b69a99-bc5a-4e10-b90e-c276f56b440f'
```

## Rollbacks and Reads
The log only contains statements from committed sessions. Statements from sessions that were rolled back, either manually or automatically, are omitted. Only statements that modify schema or data are recorded. Statements that do not modify any data are omitted.