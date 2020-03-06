import logging
import traceback
from rdflib import Namespace, Graph, BNode, URIRef, Literal
from SPARQLWrapper import SPARQLWrapper
from SPARQLWrapper import JSON, DIGEST, POST

import sys
sys.path.append('..')
from creds import virtuosoCreds

logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-7s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.DEBUG
)

class BrickEndpoint():

    def __init__(self, sparqlServer, brickVersion, defaultGraph, loadSchema=False):
        self.log = logging.getLogger()

        self.brickVerion = brickVersion
        self.sparqlServer = sparqlServer
        self.defaultGraph = defaultGraph

        self.BrickNS = Namespace(f"https://brickschema.org/schema/{brickVersion}/Brick#")
        self.BrickFrameNS = Namespace(f"https://brickschema.org/schema/{brickVersion}/BrickFrame#")
        self.BrickTagNS = Namespace(f"https://brickschema.org/schema/{brickVersion}/BrickTag#")
        self.BrickUseNS = Namespace(f"https://brickschema.org/schema/{brickVersion}/BrickUse#")

        self.Brick = f"https://brickschema.org/schema/{brickVersion}/Brick.ttl"
        self.BrickFrame = f"https://brickschema.org/schema/{brickVersion}/BrickFrame.ttl"
        self.BrickTag = f"https://brickschema.org/schema/{brickVersion}/BrickTag.ttl"
        self.BrickUse = f"https://brickschema.org/schema/{brickVersion}/BrickUse.ttl"


    def _getSparql(self, graphName=None, update=False):
        graph = graphName if graphName else self.defaultGraph
        sparql = SPARQLWrapper(endpoint=self.sparqlServer,
                               updateEndpoint=self.sparqlServer + '-auth',
                               defaultGraph=graph)
        try:
            sparql.setCredentials('dba', virtuosoCreds['dba'])
            sparql.setHTTPAuth(DIGEST)
            sparql.setReturnFormat(JSON)
            if update:
                sparql.setMethod(POST)
            return sparql
        except Exception as e:
            self.log.error(f"exception: {e}")
            raise e


    def listGraphs(self):
        dbGraphs = []
        try:
            sparql = self._getSparql()
            sparql.setQuery('SELECT DISTINCT ?g WHERE { GRAPH ?g {?s a ?t} }')
            results = sparql.query().convert()['results']['bindings']

            self.log.debug(f"# of graphs: {len(results)}")
            for r in results:
                graphName = r['g']['value']
                self.log.debug(f"{graphName} {self.queryGraphCount(graphName=graphName)}")
                dbGraphs.append(graphName)
            return dbGraphs
        except Exception as e:
            self.log.error(f"exception: {e}")
            raise e


    def dropGraph(self, graphName, force=False):
        if force:
            q = f"DROP SILENT GRAPH <{graphName}>"
        else:
            q = f"DROP GRAPH <{graphName}>"
        self.log.info(q)

        try:
            sparql = self._getSparql(graphName=graphName, update=True)
            sparql.setQuery(q)
            results = sparql.query()
        except Exception as e:
            self.log.error(f"exception: {e}")
            raise e


    def createGraph(self, graphName):
        try:
            sparql = self._getSparql(graphName=graphName, update=True)
            q = f"CREATE GRAPH <{graphName}>"
            self.log.info(q)
            sparql.setQuery(q)
            results = sparql.query()
        except Exception as e:
            self.log.error(f"exception: {e}")
            raise e


    def loadSchema(self):
        try:
            # delete all schema graphs before loading
            self.dropGraph(self.Brick, force=True)
            self.loadFileViaURL(self.Brick)
            self.dropGraph(self.BrickFrame, force=True)
            self.loadFileViaURL(self.BrickFrame)
            self.dropGraph(self.BrickUse, force=True)
            self.loadFileViaURL(self.BrickUse)
            self.dropGraph(self.BrickTag, force=True)
            self.loadFileViaURL(self.BrickTag)
        except Exception as e:
            self.log.error(f"exception: {e}")
            raise e

    def loadFileViaURL(self, graphFile, graphName=None):
        graph = graphName if graphName else graphFile
        try:
            sparql = self._getSparql(graphName=graph, update=True)
            q = f"LOAD <{graphFile}> INTO <{graph}>"
            self.log.info(q)
            sparql.setQuery(q)
            results = sparql.query()
        except Exception as e:
            self.log.error(f"exception: {e}")
            raise e


    def queryGraphCount(self, graphName=None):
        nTriples = None

        try:
            sparql = self._getSparql(graphName=graphName)

            # cheap op: get count
            q = 'SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o . }'
            sparql.setQuery(q)
            ret = sparql.query().convert()
            for r in ret['results']['bindings']:
                nTriples = r['count']['value']
                break
            return nTriples
        except Exception as e:
            self.log.error(f"exception: {e}")
            raise e


    def queryGraph(self, graphName, verbose=False):
        try:
            sparql = self._getSparql(graphName=graphName)
            sparql.setQuery('SELECT * WHERE { ?s ?p ?o. }')
            ret = sparql.query().convert()
            triples = ret['results']['bindings']
            self.log.debug(f'queryGraph # of triples:', len(triples))

            g = Graph()
            for r in triples:
                if verbose:
                    self.log.debug(f"({r['s']['type']})<{r['s']['value']}> " \
                                   f"({r['p']['type']})<{r['p']['value']}> " \
                                   f"({r['o']['type']})<{r['o']['value']}>")

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
                    else:
                        assert False, f"term type {term['type']} is not handled"
                # end of for term
                g.add(triple)

            return g
        except Exception as e:
            self.log.error(f"exception: {e}")
            raise e
    # end of queruGraph()


    def loadGraph(self, g, graphName):
        try:
            sparql = self._getSparql(graphName, update=True)
            q = f"WITH <{graphName}> INSERT {{\n"
            for (s, p, o) in g:
                q += ' '.join([term.n3() for term in (s, p, o)]) + ' .\n'
            q += '}'
            sparql.setQuery(q)
            results = sparql.query()
        except Exception as e:
            self.log.error(f"exception: {e}")
            raise e

    def execQuery(self, queryStr, graphName=None):
        try:
            sparql = self._getSparql(graphName=graphName)
            sparql.setQuery(queryStr)
            return sparql.query().convert()
        except Exception as e:
            self.log.error(f"exception: {e}")
            raise e

    def execUpdate(queryStr, graphName=None):
        try:
            sparql = self._getSparql(graphName=graphName, update=True)
            sparql.setQuery(queryStr)
            return sparql.query().convert()
        except Exception as e:
            self.log.error(f"exception: {e}")
            raise e

# end of BrickEndpoint()