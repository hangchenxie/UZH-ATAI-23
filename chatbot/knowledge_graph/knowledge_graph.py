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
from chatbot import cache


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




if __name__ == "__main__":
    kg = KnowledgeGraph()
    # # imdb_rel = WDT.P345
    # # ent = WD.Q2680
    # id = [str(s.imdb_id) for s in kg.query('''
    # PREFIX ddis: <http://ddis.ch/atai/>
    # PREFIX wd: <http://www.wikidata.org/entity/>
    # PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    # PREFIX schema: <http://schema.org/>
    #
    # SELECT ?imdb_id WHERE {
    #     wd:Q2680 wdt:P345 ?imdb_id .
    #
    # }
    # ''')]
    #
    # print(type(id))

    import csv

    # Your SPARQL query to get the movies and their genres
    results = [[str(s), str(lbl)] for s, lbl in kg.query('''
    PREFIX ddis: <http://ddis.ch/atai/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX schema: <http://schema.org/>
    
    SELECT ?movie ?lbl WHERE {
    ?movie wdt:P31 wd:Q11424 .
    ?movie rdfs:label ?lbl .
    }
    ''')]

    # Write the results into a CSV file
    with open('movies_genres.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Entity", "Label"])
        for result in results:
            writer.writerow(result)
