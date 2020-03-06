from graph_db_wrapper.brickEndpoint import BrickEndpoint

defaultGraph = 'http://www.xyz.abc/graph'

def test_xxx():
    print("in test")
    ep = BrickEndpoint('http://localhost:8890/sparql',
                       '1.0.3',
                       defaultGraph,
                       loadSchema=False)
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
    ep.listGraphs()

    return

    g = Graph()
    g.parse('sample_graph.ttl', format='turtle')
    ep.loadGraph(g, defaultGraph)
    resultG = ep.queryGraph(defaultGraph, verbose=True)
    ep.dropGraph(defaultGraph, force=True)
    ep.listGraphs()
