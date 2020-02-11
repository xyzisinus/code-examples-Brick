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
        print('(%s)<%s> (%s)<%s> (%s)<%s>' %
              (r['s']['type'], r['s']['value'], r['p']['type'], r['p']['value'], r['o']['type'], r['o']['value']))

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
deleteAll()

print('insert a triple')
sparql = getSparql(update=True)
sparql.setQuery("""
WITH <http://www.example.org/graph-selected>
INSERT
{ <http://dbpedia.org/resource/Asturias> rdfs:label "Asturies"@ast }
""")
results = sparql.query()
queryGraph(details=True)

print('update a triple -- delete and insert')
sparql = getSparql(update=True)
sparql.setQuery("""
WITH <http://www.example.org/graph-selected>
DELETE
{ <http://dbpedia.org/resource/Asturias> rdfs:label "Asturies"@ast }
INSERT
{ <http://dbpedia.org/resource/Asturias> rdfs:label "ASTURIES"@ast }
""")
results = sparql.query()
queryGraph(details=True)

print('delete a triple')
sparql = getSparql(update=True)
sparql.setQuery("""
WITH <http://www.example.org/graph-selected>
DELETE
{ <http://dbpedia.org/resource/Asturias> rdfs:label "ASTURIES"@ast }
""")
results = sparql.query()
queryGraph()

exit()
