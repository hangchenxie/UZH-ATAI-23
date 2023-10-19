import csv
import numpy as np
import os
import rdflib
import pandas as pd
from sklearn.metrics import pairwise_distances
from rdflib import Namespace



class Embedding:

    def __init__(self, graph):
        self.WD = Namespace('http://www.wikidata.org/entity/')
        self.WDT = Namespace('http://www.wikidata.org/prop/direct/')
        self.SCHEMA = Namespace('http://schema.org/')
        self.DDIS = Namespace('http://ddis.ch/atai/')
        self.RDFS = Namespace.RDFS
        self.graph = graph
        self.entity_emb = np.load(os.path.join('data', 'entity_embeds.npy'))
        self.relation_emb = np.load(os.path.join('data', 'relation_embeds.npy'))
        self.entity_file = os.path.join('data', 'entity_ids.del')
        self.relation_file = os.path.join('data', 'relation_ids.del')

        with open(self.entity_file, 'r') as ifile:
            self.ent2id = {rdflib.term.URIRef(ent): int(idx) for idx, ent in csv.reader(ifile, delimiter='\t')}
            self.id2ent = {v: k for k, v in self.ent2id.items()}
        with open(self.relation_file, 'r') as ifile:
            self.rel2id = {rdflib.term.URIRef(rel): int(idx) for idx, rel in csv.reader(ifile, delimiter='\t')}
            self.id2rel = {v: k for k, v in self.rel2id.items()}

        self.ent2lbl = {ent: str(lbl) for ent, lbl in graph.subject_objects(self.RDFS.label)}
        self.lbl2ent = {lbl: ent for ent, lbl in self.ent2lbl.items()}

    def get_entity_embedding(self, entity):
        if entity in self.ent2id:
            self.movie_id = self.ent2id[entity]
            distances = pairwise_distances(self.entity_emb[self.movie_id].reshape(1, -1), self.entity_emb, metric='cosine').flatten()
            most_likely = np.argsort(distances)
        return most_likely, distances


    def get_relation_embedding(self, relation):
        if relation in self.rel2id:
            relation_id = self.rel2id[relation]
            movie_emb = self.entity_emb[self.movie_id]
            genre = self.relation_emb[relation_id]
            lhs = movie_emb + genre
            distances = pairwise_distances(lhs.reshape(1, -1), self.entity_emb).reshape(-1)
            most_likely = np.argsort(distances)
        return most_likely, distances


    def get_likely_entities(self, most_likely, distances):
        for rank, idx in enumerate(most_likely[:3]):
            rank += 1
            ent = self.id2ent[idx]
            q_id = ent.split('/')[-1]
            lbl = self.ent2lbl[ent]
            dist = distances[idx]

            print(f'{rank:2d}. {dist:.3f} {q_id:10s} {lbl}')
