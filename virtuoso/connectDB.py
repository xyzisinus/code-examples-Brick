from copy import deepcopy
import pdb
from uuid import uuid4 as gen_uuid

import rdflib
from rdflib import RDFS, RDF, OWL, Namespace
from rdflib.namespace import FOAF
from SPARQLWrapper import SPARQLWrapper
from SPARQLWrapper import JSON, SELECT, INSERT, DIGEST, GET, POST
from rdflib import URIRef, Literal

import sys
sys.path.append('..')
from creds import virtuosoCreds

# Demonstrate grap db operations via SPARQLWrapper.
# The ops here need permissions granted to "sparql" by virtuoso db.
# See README.md for details.

defaultGraph = 'http://www.example.org/graph-selected'

def getSparql(update=False):
    sparql = SPARQLWrapper(endpoint='http://localhost:8890/sparql',
                           updateEndpoint='http://localhost:8890/sparql-auth',
                           defaultGraph='http://www.example.org/graph-selected')
    sparql.setCredentials('dba', virtuosoCreds['dba'])
    sparql.setHTTPAuth(DIGEST)
    sparql.setReturnFormat(JSON)
    if update:
        sparql.setMethod(POST)
    return sparql

def queryGraph(details=False):
    sparql = getSparql()
    sparql.setQuery('WITH <http://www.example.org/graph-selected> SELECT * WHERE { ?s ?p ?o. }')
    ret = sparql.query().convert()
    triples = ret['results']['bindings']
    print(f'# of triples in {defaultGraph}', len(triples))

    if not details: return
    for r in triples:
        print('<%s> <%s> <%s>' % (r['s']['value'], r['p']['value'], r['o']['value']))

def deleteAll():
    print('delete all triples')
    try:
        sparql = getSparql(update=True)
        sparql.setQuery("""
        WITH <http://www.example.org/graph-selected>
        DELETE { ?s ?p ?o } WHERE { ?s ?p ?o . }
        """)
        results = sparql.query()
    except Exception as e:
        print('delete all exception %s' % e)

    queryGraph()

def loadFileViaURL():
    print('load file via URL')
    try:
        sparql = getSparql(update=True)
        sparql.setQuery("""
        WITH <http://www.example.org/graph-selected>
        LOAD <https://brickschema.org/schema/1.0.3/Brick.ttl> INTO <http://www.example.org/graph-selected>
        """)
        results = sparql.query()
    except Exception as e:
        print('load file via URL exception %s' % e)

    queryGraph()

queryGraph()
loadFileViaURL()
queryGraph(details=True)
deleteAll()


# try insert: must exec
# grant execute on "DB.DBA.SPARQL_INSERT_DICT_CONTENT" to "SPARQL";
sparql = getSparql(update=True)
sparql.setQuery("""
WITH <http://www.example.org/graph-selected>
INSERT
{ <http://dbpedia.org/resource/Asturias> rdfs:label "Asturies"@ast }
""")
print('request', sparql.isSparqlUpdateRequest())
results = sparql.query()
print(results)

# try query
sparql = getSparql()
sparql.setQuery('WITH <http://www.example.org/graph-selected> SELECT * WHERE { ?s ?p ?o. }')
try :
   ret = sparql.query().convert()
   print(ret)
   for r in ret['results']['bindings']:
       print ('result', r)
except :
   deal_with_the_exception()

# try update, must exec
# grant execute on "DB.DBA.SPARQL_MODIFY_BY_DICT_CONTENTS" to "SPARQL";
sparql = getSparql(update=True)
sparql.setQuery("""
WITH <http://www.example.org/graph-selected>
DELETE
{ <http://dbpedia.org/resource/Asturias> rdfs:label "Asturies"@ast }
INSERT
{ <http://dbpedia.org/resource/Asturias> rdfs:label "ASTURIES"@ast }
""")
print('request', sparql.isSparqlUpdateRequest())
results = sparql.query()
print(results)

# try delete, must exec
# grant execute on "DB.DBA.SPARQL_DELETE_DICT_CONTENT" to "SPARQL";
sparql = getSparql(update=True)
sparql.setQuery("""
WITH <http://www.example.org/graph-selected>
DELETE
{ <http://dbpedia.org/resource/Asturias> rdfs:label "ASTURIES"@ast }
""")
print('request', sparql.isSparqlUpdateRequest())
results = sparql.query()
print(results)

# try query again
# get nothing
sparql = getSparql()
sparql.setQuery('SELECT * WHERE { ?s ?p ?o. }')
try :
   ret = sparql.query().convert()
   print(ret)
   for r in ret['results']['bindings']:
       print ('result', r)
except :
   deal_with_the_exception()

exit()
