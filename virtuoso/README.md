`connectDB.py`: select/insert/delete triples using the sparqlWrapper package as database user dba.  Do the following
to grant permissions to `SPARQL` using Virtuoso's web interface `DBhost:8890`.
```
grant execute on "DB.DBA.SPARQL_INSERT_DICT_CONTENT" to "SPARQL";
grant execute on "DB.DBA.SPARQL_DELETE_DICT_CONTENT" to "SPARQL";
grant execute on "DB.DBA.SPARQL_MODIFY_BY_DICT_CONTENTS" to "SPARQL";
grant execute on "DB.DBA.SPARUL_LOAD" to "SPARQL";
```

** With blank nodes in the graph parsed from a .ttl file, the database side loading method (LOAD INTO) should be used,
That is because the database makes no guarantee the Bnode names will be kept consistent across multiple INSERT queries.
When the file is large, even if the caller of SPARQLWrapper inserts all triples with one query SPARQLWrapper may
still devide the inserts into batches and thus break the bnode name consistency. **
