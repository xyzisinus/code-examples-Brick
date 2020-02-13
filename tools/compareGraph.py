from rdflib import RDFS, RDF, OWL, Namespace, Graph, Literal, BNode, URIRef, compare
from argparse import ArgumentParser

parser = ArgumentParser(description="Compare two graph file.")
parser.add_argument("g1", metavar="g1", help="a turtle file")
parser.add_argument("g2", metavar="g2", help="a turtle file")
args = parser.parse_args()

print('parse', args.g1)
g1 = Graph()
g1.parse(args.g1, format='turtle')
print(len(g1))
print('parse', args.g2)
g2 = Graph()
g2.parse(args.g2, format='turtle')
print(len(g1))
print('compare', args.g1, args.g2)
print(f"{args.g1} and {args.g2} are isomorphic:", compare.isomorphic(g1, g2))
