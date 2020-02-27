from copy import deepcopy
import pdb
from uuid import uuid4 as gen_uuid
import requests

import rdflib
from rdflib import RDFS, RDF, OWL, Namespace, Graph, Literal, BNode, URIRef, compare
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
brickFile =  'https://brickschema.org/schema/1.0.3/Brick.ttl'
sampleGraphFile = 'sample_graph.ttl'
#sampleGraphFile = 'short.ttl'

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


def queryGraphCount():
    nTriples = None

    # cheap op: get count first
    sparql = getSparql()
    sparql.setQuery('WITH <http://www.example.org/graph-selected> SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o . }')
    ret = sparql.query().convert()
    for r in ret['results']['bindings']:
        nTriples = r['count']['value']
        break
    print(f'queryGraphCount # of triples in {defaultGraph}', nTriples)


def queryGraph(verbose=False):
    sparql = getSparql()
    sparql.setQuery('WITH <http://www.example.org/graph-selected> SELECT * WHERE { ?s ?p ?o. }')
    ret = sparql.query().convert()
    triples = ret['results']['bindings']
    print(f'queryGraph # of triples in {defaultGraph}', len(triples))

    g = Graph()
    for r in triples:
        if verbose:
            print('(%s)<%s> (%s)<%s> (%s)<%s>' %
                  (r['s']['type'], r['s']['value'], r['p']['type'], r['p']['value'], r['o']['type'], r['o']['value']))

        triple = ()
        for term in (r['s'], r['p'], r['o']):
            if term['type'] == 'uri':
                triple = triple + (URIRef(term['value']),)
            elif term['type'] == 'literal':
                if term['xml:lang']:
                    triple = triple + (Literal(term['value'], term['xml:lang']),)
                else:
                    triple = triple + (Literal(term['value']),)
            elif term['type'] == 'bnode':
                triple = triple + (BNode(term['value']),)
                hasBnode = True
            else:
                assert False, 'term type %s is not handled' % term['type']

        g.add(triple)

    return g


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

    queryGraphCount()

def loadFileViaURL():
    print('load file via URL')

    try:
        sparql = getSparql(update=True)
        q = 'WITH <http://www.example.org/graph-selected> LOAD <%s> INTO <http://www.example.org/graph-selected>' % brickFile
        sparql.setQuery(q)
        results = sparql.query()
    except Exception as e:
        print('load file via URL exception %s' % e)

    queryGraphCount()

# CAUTION: With blank nodes in the graph parsed from a .ttl file, the database side
# loading method loadViaURL should be used,
# That is because the database makes no guarantee the Bnode names will be kept
# consistent across multiple INSERT queries.
# When the file is large, even if the caller of SPARQLWrapper inserts all triples
# with one query SPARQLWrapper may still devide the inserts into batches and thus
# break the bnode name consistency.
def loadGraph(g):
    print('load local graph')

    sparql = getSparql(update=True)
    q = 'WITH <http://www.example.org/graph-selected> INSERT {\n'
    for (s, p, o) in g:
        q += ' '.join([term.n3() for term in (s, p, o)]) + ' .\n'
    q += '}'
    sparql.setQuery(q)
    results = sparql.query()

    queryGraphCount()

def listGraphs():
    sparql = getSparql()
    sparql.setQuery('SELECT DISTINCT ?g WHERE { GRAPH ?g {?s a ?t} }')
    results = sparql.query().convert()['results']['bindings']
    print('# of graphs:', len(results))
    for r in results:
        print(r['g']['value'])


deleteAll()

# parse a SMALL .ttl file, load as tripls, query and compare
g = Graph()
g.parse(sampleGraphFile, format='turtle')
loadGraph(g)
resultG = queryGraph()
print('compare db graph and local:', compare.isomorphic(g, resultG))

deleteAll()

# load a file via URL, query.  parse the same file into graph and compare.
loadFileViaURL()
resultG = queryGraph()
# write to file for analysis
with open('BrickFromDB.ttl', 'wb') as f:
    f.write(resultG.serialize(format='ttl'))
# download the same file and parse into grapy
r = requests.get(brickFile, allow_redirects=True)
open('Brick.ttl', 'wb').write(r.content)
g = Graph()
g.parse('Brick.ttl', format='turtle')
print('compare db graph and local:', compare.isomorphic(g, resultG))

deleteAll()

listGraphs()

print('insert 2 triples')
sparql = getSparql(update=True)
sparql.setQuery("""
WITH <http://www.example.org/graph-selected>
INSERT
{ <http://dbpedia.org/resource/Asturias> rdfs:label "Asturies"@ast .
  <http://dbpedia.org/resource/Asturias> rdfs:label "XYZ"@ast }
""")
results = sparql.query()
resultG = queryGraph(verbose=True)
print('graph:', resultG.serialize(format='ttl').decode('utf-8'))

listGraphs()

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
queryGraph()

print('delete a triple')
sparql = getSparql(update=True)
sparql.setQuery("""
WITH <http://www.example.org/graph-selected>
DELETE
{ <http://dbpedia.org/resource/Asturias> rdfs:label "ASTURIES"@ast }
""")
results = sparql.query()
queryGraph()

# Empty the default graph
deleteAll()

exit()
