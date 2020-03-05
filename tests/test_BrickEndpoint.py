from graph_db_wrapper.brickEndpoint import BrickEndpoint

def test_xxx():
    print("in test")
    defaultGraph = 'http://www.xyz.abc/graph'
    ep = BrickEndpoint('http://localhost:8890/sparql',
                       '1.0.3',
                       defaultGraph,
                       loadSchema=False)
    ep.listGraphs()
