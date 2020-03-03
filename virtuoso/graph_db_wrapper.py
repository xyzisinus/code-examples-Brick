from rdflib import Namespace, Graph, BNode, URIRef, Literal
from SPARQLWrapper import SPARQLWrapper
from SPARQLWrapper import JSON, DIGEST, POST

import sys
sys.path.append('..')
from creds import virtuosoCreds

class BrickEndpoint():

    def __init__(self, sparqlServer, brickVersion, defaultGraph, loadSchema=False):
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
        sparql.setCredentials('dba', virtuosoCreds['dba'])
        sparql.setHTTPAuth(DIGEST)
        sparql.setReturnFormat(JSON)
        if update:
            sparql.setMethod(POST)
        return sparql


    def listGraphs(self):
        dbGraphs = []
        sparql = self._getSparql()
        sparql.setQuery('SELECT DISTINCT ?g WHERE { GRAPH ?g {?s a ?t} }')
        results = sparql.query().convert()['results']['bindings']
        print('# of graphs:', len(results))
        for r in results:
            graphName = r['g']['value']
            print(graphName, self.queryGraphCount(graphName=graphName))
            dbGraphs.append(graphName)
        return dbGraphs


    def deleteGraph(self, graphName, force=False):
        if force:
            q = f"DROP SILENT GRAPH <{graphName}>"
        else:
            q = f"DROP GRAPH <{graphName}>"
        print(q)

        try:
            sparql = self._getSparql(graphName=graphName, update=True)
            sparql.setQuery(q)
            results = sparql.query()
        except Exception as e:
            print('deleteGraph exception %s' % e)


    def createGraph(self, graphName):
        try:
            sparql = self._getSparql(graphName=graphName, update=True)
            q = f"CREATE GRAPH <{graphName}>"
            print(q)
            sparql.setQuery(q)
            results = sparql.query()
        except Exception as e:
            print('createGraph exception %s' % e)


    def loadSchema(self):
        # delete all schema graphs before loading
        self.deleteGraph(self.Brick, force=True)
        self.loadFileViaURL(self.Brick)
        self.deleteGraph(self.BrickFrame, force=True)
        self.loadFileViaURL(self.BrickFrame)
        self.deleteGraph(self.BrickUse, force=True)
        self.loadFileViaURL(self.BrickUse)
        self.deleteGraph(self.BrickTag, force=True)
        self.loadFileViaURL(self.BrickTag)


    def __setUpdate(self):
        print('set update')
        self.sparql.setMethod(POST)


    def loadFileViaURL(self, graphFile, graphName=None):
        graph = graphName if graphName else graphFile
        try:
            sparql = self._getSparql(graphName=graph, update=True)
            q = f"LOAD <{graphFile}> INTO <{graph}>"
            print(q)
            sparql.setQuery(q)
            results = sparql.query()
        except Exception as e:
            print('load file via URL exception %s' % e)


    def queryGraphCount(self, graphName=None):
        nTriples = None

        sparql = self._getSparql(graphName=graphName)

        # cheap op: get count
        q = 'SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o . }'
        sparql.setQuery(q)
        ret = sparql.query().convert()
        for r in ret['results']['bindings']:
            nTriples = r['count']['value']
            break
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
        q = f"WITH <{graphName}> INSERT {{\n"
        for (s, p, o) in g:
            q += ' '.join([term.n3() for term in (s, p, o)]) + ' .\n'
        q += '}'
        sparql.setQuery(q)
        results = sparql.query()

        self.queryGraphCount()

    def execQuery(self, q, graphName):
        sparql = getSparql(graphName)
        sparql.setQuery(q)
        results = sparql.query().convert()
        return results

# end of BrickEndpoint()

if __name__ == '__main__':
    endpoint = BrickEndpoint('http://localhost:8890/sparql',
                             '1.0.3',
                             'http://www.xyz.abc/default-graph',
                             loadSchema=False)
    ep.listGraphs()
    ep.loadFileViaURL(ep.Brick)
    ep.deleteGraph(ep.Brick)

    # load all schema files
    ep.loadSchema()
    ep.listGraphs()

    ep.createGraph('http://abc.efg')
    ep.loadFileViaURL(ep.Brick, graphName='http://abc.efg')
    ep.listGraphs()
    ep.deleteGraph('http://abc.efg')
    ep.listGraphs()
    exit()
