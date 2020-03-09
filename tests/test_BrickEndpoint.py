import os
import logging
import requests
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


def test_loadGraph():
    defaultGraph = 'http://www.xyz.abc/test_loadGraph'
    ep = BrickEndpoint('http://localhost:8890/sparql',
                       '1.0.3',
                       defaultGraph)

    g = Graph()
    g.parse('tests/data/sample_graph.ttl', format='turtle')
    ep.loadGraph(g, defaultGraph)
    resultG = ep.queryGraph(defaultGraph, verbose=True)
    assert compare.isomorphic(g, resultG), 'loaded graph and query result not match'

    ep.dropGraph(defaultGraph, force=True)


def test_loadFileViaURL():
    defaultGraph = 'http://www.xyz.abc/test_loadFileViaURL'
    ep = BrickEndpoint('http://localhost:8890/sparql',
                       '1.0.3',
                       defaultGraph)

    ep.loadFileViaURL(ep.Brick, graphName=defaultGraph)
    resultG = ep.queryGraph(defaultGraph)

    # download the file and read in to compare
    r = requests.get(ep.Brick, allow_redirects=True)
    open('Brick.ttl', 'wb').write(r.content)
    g = Graph()
    g.parse('Brick.ttl', format='turtle')
    assert compare.isomorphic(g, resultG), 'loaded graph and query result not match'

    ep.dropGraph(defaultGraph, force=True)
    os.remove('Brick.ttl')
