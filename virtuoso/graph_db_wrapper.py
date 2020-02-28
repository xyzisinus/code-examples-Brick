from copy import deepcopy
import pdb
from uuid import uuid4 as gen_uuid

import rdflib
from rdflib import RDFS, RDF, OWL, Namespace, Graph, BNode
from rdflib.namespace import FOAF
from SPARQLWrapper import SPARQLWrapper
from SPARQLWrapper import JSON, SELECT, INSERT, DIGEST, GET, POST
from rdflib import URIRef, Literal
import traceback

import sys
sys.path.append('..')
from creds import virtuosoCreds

#from .common import *
#from ..helpers import chunks

import sys
sys.path.append('..')
from creds import virtuosoCreds

class BrickEndpoint():

    def __init__(self, sparqlServer, brickVersion, graphName, loadSchema=False):
        self.brickVerion = brickVersion
        self.sparqlServer = sparqlServer
        self.brickVersion = brickVersion

        self.BrickNS = Namespace(f"https://brickschema.org/schema/{brickVersion}/Brick#")
        self.BrickFrameNS = Namespace(f"https://brickschema.org/schema/{brickVersion}/BrickFrame#")
        self.BrickTagNS = Namespace(f"https://brickschema.org/schema/{brickVersion}/BrickTag#")
        self.BrickUseNS = Namespace(f"https://brickschema.org/schema/{brickVersion}/BrickUse#")

        # Schma file urls.  Each also serves as graph name in DB.
        self.Brick = f"https://brickschema.org/schema/{brickVersion}/Brick.ttl"
        self.BrickFrame = f"https://brickschema.org/schema/{brickVersion}/BrickFrame.ttl"
        self.BrickTag = f"https://brickschema.org/schema/{brickVersion}/BrickTag.ttl"
        self.BrickUse = f"https://brickschema.org/schema/{brickVersion}/BrickUse.ttl"

        # All known dbGraphs
        self.dbGraphs = []

        self.defaultGraph = graphName

        '''
        self.sparql = SPARQLWrapper(endpoint=sparqlServer,
                                    updateEndpoint=sparqlServer + '-auth',
                                    defaultGraph=graphName)
        self.sparql.setCredentials('dba', virtuosoCreds['dba'])
        self.sparql.setHTTPAuth(DIGEST)
        self.sparql.setReturnFormat(JSON)
        '''

    def _getSparql(self, graphName, update=False):
        sparql = SPARQLWrapper(endpoint='http://localhost:8890/sparql',
                               updateEndpoint='http://localhost:8890/sparql-auth')
        #defaultGraph=graphName)
        # print('getSparql, default graph:', graphName)
        sparql.setCredentials('dba', virtuosoCreds['dba'])
        sparql.setHTTPAuth(DIGEST)
        sparql.setReturnFormat(JSON)
        if update:
            sparql.setMethod(POST)
        return sparql


    def listGraphs(self):
        sparql = self._getSparql(self.defaultGraph)
        sparql.setQuery('SELECT DISTINCT ?g WHERE { GRAPH ?g {?s a ?t} }')
        results = sparql.query().convert()['results']['bindings']
        for r in results:
            if r['g']['value'] not in self.dbGraphs:
                self.dbGraphs.append(r['g']['value'])
        for g in self.dbGraphs:
            print(g, self.__queryCount(g))
        return self.dbGraphs


    def deleteAllInGraph(self, graphName):
        print(f"{graphName} size:", self.__queryCount(graphName))

        print('delete all triples in:', graphName)
        try:
            sparql = self._getSparql(graphName, update=True)
            print(f"WITH <{graphName}> DELETE {{ ?s ?p ?o . }} WHERE {{ ?s ?p ?o . }}")
            sparql.setQuery(f"WITH <{graphName}> DELETE {{ ?s ?p ?o . }} WHERE {{ ?s ?p ?o . }}")
            results = sparql.query()
            print(f"{graphName} size:", self.__queryCount(graphName))
        except Exception as e:
            print('delete all exception %s' % e)
            raise(e)


    def loadSchema(self):
        self.listGraphs()
        self.loadFileViaURL(self.Brick)
        # self.loadFileViaURL(self.BrickFrame)
        # self.loadFileViaURL(self.BrickUse)
        #self.loadFileViaURL(self.BrickTag)
        self.listGraphs()

    def __setUpdate(self):
        print('set update')
        self.sparql.setMethod(POST)


    def loadFileViaURL(self, url, cleanFirst=False, dbGraphName=None):
        try:
            graphName = dbGraphName if dbGraphName else url
            graphName = graphName.replace('https', 'http').replace('.ttl', '')
            print('load file:', url, graphName)
            graphName = 'http://www.xyz.abc/graph-selected'
            #graphName = 'http://www.brickschema.or/schema'
            # graphName = 'http://brick'
            if cleanFirst:
               self.deleteAllInGraph(graphName)

            sparql = self._getSparql(graphName, update=True)
            print(f"WITH <{graphName}> LOAD <{url}> INTO <{graphName}>")
            sparql.setQuery(f"WITH <{graphName}> LOAD <{url}> INTO <{graphName}>")
            results = sparql.query()
            self.__queryCount(graphName)
        except Exception as e:
            print('load file via URL exception:', e)
            raise(e)


    def __queryCount(self, graphName):
        nTriples = None

        sparql = self._getSparql(graphName)
        sparql.setQuery(f"""
        WITH <{graphName}> SELECT (COUNT(*) AS ?count) WHERE {{ ?s ?p ?o . }}
        """)
        ret = sparql.query().convert()
        for r in ret['results']['bindings']:
            nTriples = r['count']['value']
            break

        # print(f"count: in {graphName}:", nTriples)
        return nTriples

    def queryGraph(self, graphName, verbose=False):
        sparql = self._getSparql(graphName)
        sparql.setQuery(f"WITH <{graphName}> SELECT * WHERE {{ ?s ?p ?o. }}")
        ret = sparql.query().convert()
        triples = ret['results']['bindings']
        print(f"queryGraph # of triples in {graphName}:", len(triples))

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
    # end of queruGraph()

    def loadGraph(self, g, graphName):
        print('load local graph')

        sparql = getSparql(graphName, update=True)
        q = f"WITH <{graphName}> INSERT {{\n'
        for (s, p, o) in g:
        q += ' '.join([term.n3() for term in (s, p, o)]) + ' .\n'
        q += '}}"
        sparql.setQuery(q)
        results = sparql.query()

        queryGraphCount()

    def execQuery(self, q, graphName):
        sparql = getSparql(graphName)
        sparql.setQuery(q)
        results = sparql.query().convert()
        return results

# end of BrickEndpoint()

if __name__ == '__main__':
    endpoint = BrickEndpoint('http://localhost:8890/sparql',
                             '1.0.3',
                             'http://www.example.org/graph',
                             loadSchema=False)
    endpoint.listGraphs()
    endpoint.queryGraph('https://brickschema.org/schema/1.0.3/Brick.ttl')
    endpoint.queryGraph('http://brickschema.org/schema/1.0.3/Brick.ttl')
    endpoint.loadFileViaURL('https://brickschema.org/schema/1.0.3/Brick.ttl')
    # endpoint.deleteAllInGraph('http://www.xyz.abc/graph-selected')
    endpoint.deleteAllInGraph('http://www.example.org/graph-selected')
    endpoint.deleteAllInGraph('http://x.y.z/graph-selected')
    endpoint.deleteAllInGraph('http://www.brick.frame/graph')
    endpoint.deleteAllInGraph('http://brickschema.org/schema/1.0.3/Brick.ttl')
    endpoint.listGraphs()
    exit()
    endpoint.queryGraph('https://brickschema.org/schema/1.0.3/Brick.ttl')
    endpoint.deleteAllInGraph('http://brickschema.org/schema/1.0.3/Brick.ttl')
    #endpoint.deleteAllInGraph('http://www.example.org/graph-selected')
    exit()
    # endpoint.loadSchema()
    endpoint.deleteAllInGraph('http://brickschema.org/schema/1.0.3/BrickFrame.ttl')
    endpoint.listGraphs()
    endpoint.query
    exit()
    endpoint.loadSchema()
