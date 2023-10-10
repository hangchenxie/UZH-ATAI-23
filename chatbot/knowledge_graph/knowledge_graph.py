import pickle
from rdflib.namespace import Namespace, RDF, RDFS, XSD
import os
from rdflib.term import URIRef, Literal
import csv
import json
import networkx as nx
import pandas as pd
import rdflib
from collections import defaultdict, Counter


prefixes = dict(
        WD = Namespace('http://www.wikidata.org/entity/'),
        WDT = Namespace('http://www.wikidata.org/prop/direct/'),
        SCHEMA = Namespace('http://schema.org/'),
        DDIS = Namespace('http://ddis.ch/atai/'),
    )


class KnowledgeGraph:
    def __init__(
            self, 
            graph_path, 
            # cache_path, 
            prefixes=prefixes
        ):
        self.prefixes = prefixes
        self.graph = self.load_or_parse_graph(graph_path)


    def load_or_parse_graph(self, graph_path):
        graph = rdflib.Graph()
        graph.parse(graph_path, format='turtle')

        return graph    


    def query(self, q):
        return self.graph.query(q)