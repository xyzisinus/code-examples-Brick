import logging
from rdflib import Graph, compare
from graph_db_wrapper.brickEndpoint import BrickEndpoint

log = logging.getLogger()
log.setLevel(logging.DEBUG)

def test_basic():
    defaultGraph = 'http://www.xyz.abc/test_basic'
    ep = BrickEndpoint('http://localhost:8890/sparql',
                       '1.0.3',
                       defaultGraph)
    ep.listGraphs()
    ep.loadFileViaURL(ep.Brick)
    ep.dropGraph(ep.Brick, force=True)

    # load all schema files
    ep.loadSchema()
    ep.listGraphs()

    ep.createGraph('http://abc.efg')
    ep.loadFileViaURL(ep.Brick, graphName='http://abc.efg')
    ep.listGraphs()
    ep.dropGraph('http://abc.efg')
    ep.dropGraph(defaultGraph, force=True)
    ep.listGraphs()


def test_loadAndCompare():
    defaultGraph = 'http://www.xyz.abc/test_loadAndCompare'
    ep = BrickEndpoint('http://localhost:8890/sparql',
                       '1.0.3',
                       defaultGraph)

    g = Graph()
    g.parse('tests/data/sample_graph.ttl', format='turtle')
    ep.loadGraph(g, defaultGraph)
    resultG = ep.queryGraph(defaultGraph, verbose=True)
    assert compare.isomorphic(g, resultG), 'loaded graph and query result not match'

    ep.dropGraph(defaultGraph, force=True)
    ep.listGraphs()
