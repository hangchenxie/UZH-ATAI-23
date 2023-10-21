import csv
import numpy as np
import os
from pathlib import Path
import rdflib
import pandas as pd
from sklearn.metrics import pairwise_distances
from rdflib import Namespace




class Embedding:

    def __init__(self, graph, entity, relation):


        # Define namespaces as global constants
        self.WD = Namespace('http://www.wikidata.org/entity/')
        self.WDT = Namespace('http://www.wikidata.org/prop/direct/')
        self.SCHEMA = Namespace('http://schema.org/')
        self.DDIS = Namespace('http://ddis.ch/atai/')
        self.RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')

        self.graph = graph
        self.entity = self.WD[entity]
        self.relation = self.WDT[relation]

        # Initialize embeddings and ID mappings as None
        self.entity_emb = None
        self.relation_emb = None
        self.ent2id = None
        self.id2ent = None
        self.rel2id = None
        self.id2rel = None

    def load_data(self):
        # Load data only when needed
        if self.entity_emb is None:
            self.entity_emb = np.load(os.path.join(Path(__file__).parents[2],'data', 'entity_embeds.npy'))
            self.relation_emb = np.load(os.path.join(Path(__file__).parents[2],'data', 'relation_embeds.npy'))
            entity_file = os.path.join(Path(__file__).parents[2],'data', 'entity_ids.del')
            relation_file = os.path.join(Path(__file__).parents[2],'data', 'relation_ids.del')

            with open(entity_file, 'r') as ifile:
                self.ent2id = {rdflib.term.URIRef(ent): int(idx) for idx, ent in csv.reader(ifile, delimiter='\t')}
                self.id2ent = {v: k for k, v in self.ent2id.items()}
            with open(relation_file, 'r') as ifile:
                self.rel2id = {rdflib.term.URIRef(rel): int(idx) for idx, rel in csv.reader(ifile, delimiter='\t')}
                self.id2rel = {v: k for k, v in self.rel2id.items()}

            self.ent2lbl = {ent: str(lbl) for ent, lbl in graph.subject_objects(self.RDFS.label)}
            self.lbl2ent = {lbl: ent for ent, lbl in self.ent2lbl.items()}

    def get_entity_embedding(self):
        # Load data if not already loaded
        self.load_data()

        if self.entity in self.ent2id:
            movie_id = self.ent2id[self.entity]
            distances = pairwise_distances(self.entity_emb[movie_id].reshape(1, -1), self.entity_emb, metric='cosine').flatten()
            most_likely = np.argsort(distances)
            prediction = []
            for rank, idx in enumerate(most_likely[:3]):
                rank = rank + 1
                ent = self.id2ent[idx]
                q_id = ent.split('/')[-1]
                lbl = self.ent2lbl[ent]
                prediction.append(lbl)
                dist = distances[idx]
                print(f"{rank}. {lbl} ({q_id}) - {dist}")
            return prediction[:3]
        else:
            raise ValueError(f"Entity {self.entity} not found in data.")

    def get_relation_embedding(self):
        # Load data if not already loaded
        self.load_data()

        if self.relation in self.rel2id:
            relation_id = self.rel2id[self.relation]
            movie_id = self.ent2id[self.entity]
            movie_emb = self.entity_emb[movie_id]
            genre = self.relation_emb[relation_id]
            lhs = movie_emb + genre
            distances = pairwise_distances(lhs.reshape(1, -1), self.entity_emb, metric='cosine').flatten()
            most_likely = np.argsort(distances)
            prediction = []
            for rank, idx in enumerate(most_likely[:3]):
                rank = rank + 1
                ent = self.id2ent[idx] # eg: http://www.wikidata.org/entity/Q132863
                q_id = ent.split('/')[-1] # to convert 'http://www.wikidata.org/entity/Q132863' to 'Q132863'
                lbl = self.ent2lbl[ent] # eg: 'Finding Nemo'
                prediction.append(lbl)
                dist = distances[idx] # eg: 0.0
                print(f"{rank}. {lbl} ({q_id}) - {dist}")
            return prediction[:3]
        else:
            raise ValueError(f"Relation {self.relation} not found in data.")




if __name__ == "__main__":

    graph = rdflib.Graph()

    graph.parse(os.path.join(Path(__file__).parents[2],'data', '14_graph.nt'), format='turtle')

    entity = 'Q7750525'  # replace with your actual entity
    relation = 'P58' # replace with your actual relation

    emb = Embedding(graph, entity, relation)

    # Test get_entity_embedding method
    most_likely = emb.get_entity_embedding()
    print("Most likely entities for given entity:")
    print(most_likely)


    # Test get_relation_embedding method
    label = emb.get_relation_embedding()
    print("Most likely entities for given relation:")
    print(label)

