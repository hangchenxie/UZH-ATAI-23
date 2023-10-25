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
from pathlib import Path
from .. import cache


graph_path = Path(__file__).parents[1].joinpath("data", "14_graph.nt")
graph = rdflib.Graph()
graph.parse(graph_path, format='turtle', encoding='utf-8')

prefixes = dict(
        WD = Namespace('http://www.wikidata.org/entity/'),
        WDT = Namespace('http://www.wikidata.org/prop/direct/'),
        SCHEMA = Namespace('http://schema.org/'),
        DDIS = Namespace('http://ddis.ch/atai/'),
    )


class KnowledgeGraph:
    def __init__(self):
        self.prefixes = prefixes
        self.graph = graph

    def query(self, q):
        return self.graph.query(q)