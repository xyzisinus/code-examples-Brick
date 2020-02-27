from copy import deepcopy
import pdb
from uuid import uuid4 as gen_uuid

import rdflib
from rdflib import RDFS, RDF, OWL, Namespace
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

        self.sparql = SPARQLWrapper(endpoint=sparqlServer,
                                    updateEndpoint=sparqlServer + '-auth',
                                    defaultGraph=graphName)
        self.sparql.setCredentials('dba', virtuosoCreds['dba'])
        self.sparql.setHTTPAuth(DIGEST)
        self.sparql.setReturnFormat(JSON)

    def _getSparql(self, update=False):
        sparql = SPARQLWrapper(endpoint='http://localhost:8890/sparql',
                               updateEndpoint='http://localhost:8890/sparql-auth',
                               defaultGraph='http://www.example.org/graph-selected')
        sparql.setCredentials('dba', virtuosoCreds['dba'])
        sparql.setHTTPAuth(DIGEST)
        sparql.setReturnFormat(JSON)
        if update:
            sparql.setMethod(POST)
        return sparql


    def _getGraphs(self):
        self.sparql.setQuery('SELECT DISTINCT ?g WHERE { GRAPH ?g {?s a ?t} }')
        results = self.sparql.query().convert()['results']['bindings']
        for r in results:
            if r['g']['value'] not in self.dbGraphs:
                self.dbGraphs.append(r['g']['value'])
                print(r['g']['value'])
        print('graphs', self.dbGraphs)


    def deleteAllInGraph(self, graphName):
        self.__queryCount(graphName)

        print('delete all triples in:', graphName)
        try:
            sparql = self._getSparql(update=True)
            q = f"""
            WITH <{graphName}> DELETE {{ ?s ?p ?o }} WHERE {{ ?s ?p ?o . }}
            """
            print('delete query:', q)
            self.sparql.setQuery(f"""
            WITH <{graphName}> DELETE {{ ?s ?p ?o }} WHERE {{ ?s ?p ?o . }}
            """)
            sparql.setQuery('WITH <https://brickschema.org/schema/1.0.3/Brick.ttl> DELETE { ?s ?p ?o } WHERE { ?s ?p ?o . }')
            results = sparql.query()
            self.__queryCount(graphName)
        except Exception as e:
            print('delete all exception %s' % e)
            raise(e)


    def loadSchema(self):
        self._getGraphs()
        # self.loadFileViaURL(self.Brick)
        self.loadFileViaURL(self.BrickFrame)
        # self.loadFileViaURL(self.BrickUse)
        # self.loadFileViaURL(self.BrickTag)
        self._getGraphs()

    def __setUpdate(self):
        print('set update')
        self.sparql.setMethod(POST)


    def loadFileViaURL(self, url, cleanFirst=False, dbGraphName=None):
        try:
            graphName = dbGraphName if dbGraphName else url
            print('load file:', graphName)
            graphName = 'http://www.example.org/graph-selected'
            if cleanFirst:
                self.deleteAllInGraph(graphName)
            self.__setUpdate()
            print(f"WITH <{graphName}> LOAD <{url}> INTO <{graphName}>")
            self.sparql.setQuery(f"WITH <{graphName}> LOAD <{url}> INTO <{url}>")
            results = self.sparql.query()
            self.__queryCount(graphName)
        except Exception as e:
            print('load file via URL exception:', e)
            raise(e)


    def __queryCount(self, graphName):
        nTriples = None

        self.sparql.setQuery(f"""
        WITH <{graphName}> SELECT (COUNT(*) AS ?count) WHERE {{ ?s ?p ?o . }}
        """)
        ret = self.sparql.query().convert()
        for r in ret['results']['bindings']:
            nTriples = r['count']['value']
            break

        print(f"count: in {graphName}:", nTriples)
        return nTriples

# end of BrickEndpoint()

if __name__ == '__main__':
    endpoint = BrickEndpoint('http://localhost:8890/sparql',
                             '1.0.3',
                             'http://www.example.org/graph',
                             loadSchema=False)
    endpoint.loadSchema()
