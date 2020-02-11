from copy import deepcopy
import pdb
from uuid import uuid4 as gen_uuid

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
sampleGraphFile = 'sample_graph.ttl'

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

    g = Graph()
    for r in triples:
        '''
        print('(%s)<%s> (%s)<%s> (%s)<%s>' %
              (r['s']['type'], r['s']['value'], r['p']['type'], r['p']['value'], r['o']['type'], r['o']['value']))
        '''
        triple = ()
        for term in (r['s'], r['p'], r['o']):
            if term['type'] == 'uri':
                triple = triple + (URIRef(term['value']),)
            elif term['type'] == 'literal':
                triple = triple + (Literal(term['value']))
            else:
                assert False, 'term type %s is not handled' % term['type']
        g.add(triple)

    return g
# end of queryGraph()

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

def loadGraph(g):
    for (s, p, o) in g:
        sparql = getSparql(update=True)
        q = 'WITH <http://www.example.org/graph-selected> INSERT {\n'
        triple_str = ' '.join([term.n3() for term in (s, p, o)]) + ' .\n'
        # triple_str = ' '.join(['<{0}>'.format(str(term)) for term in (s, p, o)]) + ' .\n'
        q += triple_str
        q += '}'
        sparql.setQuery(q)
        results = sparql.query()

deleteAll()
g = Graph()
g.parse(sampleGraphFile, format='turtle')

'''
for (s, p, o) in g:
    sparql = getSparql(update=True)
    q = 'WITH <http://www.example.org/graph-selected> INSERT {\n'
    triple_str = ' '.join([term.n3() for term in (s, p, o)]) + ' .\n'
    # triple_str = ' '.join(['<{0}>'.format(str(term)) for term in (s, p, o)]) + ' .\n'
    q += triple_str
    q += '}'
    sparql.setQuery(q)
    results = sparql.query()
'''

loadGraph(g)
resultG = queryGraph(details=True)
print(compare.isomorphic(g, resultG))

exit()

queryGraph()
loadFileViaURL()
deleteAll()

print('insert 2 triples')
sparql = getSparql(update=True)
sparql.setQuery("""
WITH <http://www.example.org/graph-selected>
INSERT
{ <http://dbpedia.org/resource/Asturias> rdfs:label "Asturies"@ast .
  <http://dbpedia.org/resource/Asturias> rdfs:label "XYZ"@ast }
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
queryGraph(details=True)

# Empty the default graph
deleteAll()

exit()
