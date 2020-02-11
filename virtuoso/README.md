`connectDB.py`: select/insert/delete triples using the sparqlWrapper package as database user dba.  Do the following
to grant permissions to `SPARQL` using Virtuoso's web interface `DBhost:8890`.
```
grant execute on "DB.DBA.SPARQL_INSERT_DICT_CONTENT" to "SPARQL";
grant execute on "DB.DBA.SPARQL_DELETE_DICT_CONTENT" to "SPARQL";
grant execute on "DB.DBA.SPARQL_MODIFY_BY_DICT_CONTENTS" to "SPARQL";
grant execute on "DB.DBA.SPARUL_LOAD" to "SPARQL";
```
