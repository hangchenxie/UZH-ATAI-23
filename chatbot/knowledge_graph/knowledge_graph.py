from rdflib.namespace import Namespace, RDF, RDFS, XSD
import os
from rdflib.term import URIRef, Literal
import csv
import json
import networkx as nx
import pandas as pd
import rdflib
from collections import defaultdict, Counter
from pathlib import Path


prefixes = dict(
        WD = Namespace('http://www.wikidata.org/entity/'),
        WDT = Namespace('http://www.wikidata.org/prop/direct/'),
        SCHEMA = Namespace('http://schema.org/'),
        DDIS = Namespace('http://ddis.ch/atai/'),
    )

data_path = Path(__file__).parents[2].joinpath("data", "14_graph.nt")

class KnowledgeGraph:
    def __init__(self, graph=None, path=data_path):
        if graph is None:
            self.graph = rdflib.Graph()
            self.graph.parse(path, format='turtle')
        else:
            self.graph = graph
        self.prefixes = prefixes

    def query(self, q):
        return self.graph.query(q)