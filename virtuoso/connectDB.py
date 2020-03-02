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

defaultGraph = 'http://www.example.org/graph-default'
defaultGraph = 'http://www.xyz.abc/graph-selected'
withGraph = 'http://www.example.org/graph-with'
brickFile =  'https://brickschema.org/schema/1.0.3/Brick.ttl'
sampleGraphFile = 'sample_graph.ttl'

def getSparql(graphName=None, update=False):
    graph = graphName if graphName else defaultGraph
    print('get sparql', graph)
    sparql = SPARQLWrapper(endpoint='http://localhost:8890/sparql',
                           updateEndpoint='http://localhost:8890/sparql-auth',
                           defaultGraph=graph)
    sparql.setCredentials('dba', virtuosoCreds['dba'])
    sparql.setHTTPAuth(DIGEST)
    sparql.setReturnFormat(JSON)
    if update:
        sparql.setMethod(POST)
    return sparql


def queryGraphCount(graphName=None):
    nTriples = None

    sparql = getSparql(graphName=graphName)

    # cheap op: get count
    q = f"""
    SELECT (COUNT(*) AS ?count) WHERE {{ ?s ?p ?o . }}
    """
    sparql.setQuery(q)
    ret = sparql.query().convert()
    for r in ret['results']['bindings']:
        nTriples = r['count']['value']
        break
    return nTriples


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

def deleteAll(graphName):
    print('delete all triples from', graphName)
    try:
        sparql = getSparql(graphName=graphName, update=True)
        q = f"""
        DROP SILENT GRAPH <{graphName}>
        """
        print('delete', q)
        sparql.setQuery(q)
        results = sparql.query()
        return

        sparql = getSparql(graphName=graphName, update=True)
        q = f"""
        CREATE GRAPH <{graphName}>
        """
        print('create', q)
        sparql.setQuery(q)
        results = sparql.query()


    except Exception as e:
        print('delete all exception %s' % e)

    queryGraphCount()

def loadFileViaURL(graphFile, graphName):
    print('load file via URL')

    try:
        sparql = getSparql(graphName=graphName, update=True)
        q = f"""LOAD <{graphFile}> INTO <{graphFile}>"""
        print(q)
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

dbGraphs = []
def listGraphs():
    existingGraphs = []
    sparql = getSparql()
    sparql.setQuery('SELECT DISTINCT ?g WHERE { GRAPH ?g {?s a ?t} }')
    results = sparql.query().convert()['results']['bindings']
    print('# of graphs:', len(results))
    for r in results:
        graphName = r['g']['value']
        print(graphName, queryGraphCount(graphName=graphName))
        dbGraphs.append(graphName)


listGraphs()
deleteAll('https://brickschema.org/schema/1.0.3/Brick.ttl')
listGraphs()
exit()
loadFileViaURL('https://brickschema.org/schema/1.0.3/Brick.ttl',
               'https://brickschema.org/schema/1.0.3/Brick.ttl')
listGraphs()
exit()

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
