import csv
import numpy as np
from pathlib import Path
import rdflib
import json
import pandas as pd


from difflib import get_close_matches
from sklearn.metrics import pairwise_distances
from rdflib import Namespace
from chatbot.knowledge_graph.knowledge_graph import KnowledgeGraph

embeds_path = Path(__file__).parents[1].joinpath("data", "embeds")
entity_emb = np.load(embeds_path.joinpath('entity_embeds.npy'))
relation_emb = np.load(embeds_path.joinpath('relation_embeds.npy'))
entity_file = embeds_path.joinpath('entity_ids.del')
relation_file = embeds_path.joinpath('relation_ids.del')
lbl2rel_file = embeds_path.joinpath('rel2lbl.json')

with open(entity_file, 'r') as ifile:
    ent2id = {rdflib.term.URIRef(ent): int(idx) for idx, ent in csv.reader(ifile, delimiter='\t')}
    id2ent = {v: k for k, v in ent2id.items()}
with open(relation_file, 'r') as ifile:
    rel2id = {rdflib.term.URIRef(rel): int(idx) for idx, rel in csv.reader(ifile, delimiter='\t')}
    id2rel = {v: k for k, v in rel2id.items()}
with open(lbl2rel_file, 'r', encoding= 'utf-8') as ifile:
    rel2lbl = json.load(ifile)
    lbl2rel = {lbl: rel for rel, lbl in rel2lbl.items()}

KG = KnowledgeGraph().graph
WD = rdflib.Namespace('http://www.wikidata.org/entity/')
WDT = rdflib.Namespace('http://www.wikidata.org/prop/direct/')
DDIS = rdflib.Namespace('http://ddis.ch/atai/')
RDFS = rdflib.namespace.RDFS
SCHEMA = rdflib.Namespace('http://schema.org/')


class EmbeddingCalculator:

    def __init__(self):
        self.graph = KG
        self.ent2lbl = {ent: str(lbl) for ent, lbl in self.graph.subject_objects(RDFS.label)}
        self.lbl2ent = {lbl: ent for ent, lbl in self.ent2lbl.items()}
        self.lbl2rel = dict(lbl2rel)
        self.rel2lbl = dict(rel2lbl)
        self.id2ent = id2ent
        self.ent2id = ent2id
        self.ent_emb = entity_emb
        self.WD = WD
        self.movie_ent2lbl = {}
        self.movie_ent2id = {}


    def get_embedding(self, label):
        print(f"label: {label}")
        if label in self.lbl2rel.keys():
            return relation_emb[rel2id[WDT[self.lbl2rel[label]]]]
        elif label in self.lbl2ent.keys():
            return entity_emb[ent2id[self.lbl2ent[label]]]
        else:
            return np.zeros(256)

    def get_entity_identifier(self, label):
        if label in self.lbl2ent.keys():
            return self.lbl2ent[label]
        else:
            return None


    def get_relation_identifier(self, label):
        if label in self.lbl2rel.keys():
            return self.lbl2rel[label]
        else:
            return None


    def get_most_likely_results(self, labels, N):
        lhs = np.zeros(256)
        for l in labels:
            l_emb = self.get_embedding(l)
            lhs = lhs + l_emb
        distances = pairwise_distances(lhs.reshape(1, -1), entity_emb).reshape(-1).argsort()
        most_likely_results_df = pd.DataFrame([
            (id2ent[idx][len(WD):], self.ent2lbl[id2ent[idx]], distances[idx], rank+1)
            for rank, idx in enumerate(distances[:N])],
            columns=('Entity', 'Label', 'Score', 'Rank'))
        most_likely_results = most_likely_results_df.to_dict('records')

        return most_likely_results


    # def get_recommendation(self, entities):
    #     getAllMovies = [[str(s), str(lbl)] for s, lbl in self.graph.query('''
    #     PREFIX ddis: <http://ddis.ch/atai/>
    #     PREFIX wd: <http://www.wikidata.org/entity/>
    #     PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    #     PREFIX schema: <http://schema.org/>
    #
    #     SELECT ?movie ?lbl WHERE {
    #             ?movie wdt:P31 wd:Q11424 .
    #             ?movie rdfs:label ?lbl .
    #         }
    #     ''')]
    #     movie_lbls = [lbl for s, lbl in getAllMovies]
    #     movies_list = [get_close_matches(ent.strip(), movie_lbls)[0] for ent in entities]
    #     print("movies_list:", movies_list)
    #     movies_id = [ent2id[self.lbl2ent[movie]] for movie in movies_list]
    #     print("movies_id:", movies_id)
    #     movies_emb = np.array([entity_emb[i] for i in movies_id])
    #     avg = np.average(movies_emb, axis=0)
    #     dist = pairwise_distances(avg.reshape(1, -1), entity_emb).reshape(-1).argsort()
    #     most_likely_results_df = pd.DataFrame([
    #         (id2ent[idx][len(WD):], self.ent2lbl[id2ent[idx]], dist[idx], rank+1)
    #         for rank, idx in enumerate(dist[:20])
    #         if self.ent2lbl[id2ent[idx]] not in movies_list and
    #            "Sony Pictures Universe of Marvel Characters" not in self.ent2lbl[id2ent[idx]]],
    #         columns=('Entity', 'Label', 'Score', 'Rank'))
    #     # most_likely_results_df = most_likely_results_df[most_likely_results_df['Genre'].isin(genres_list)]
    #     most_likely_results = most_likely_results_df.to_dict('records')
    #     print("most_likely_results:", most_likely_results)
    #     recommended_movies = [result['Label'] for result in most_likely_results]
    #     return recommended_movies







if __name__ == "__main__":
    test_emb_calculator = EmbeddingCalculator()
    # entities = ['The Lion King', 'Pocahontas', ' The Beauty and the Beast']
    # entities = ['Nightmare on Elm Street', 'Friday the 13th', 'Halloween']
    # result = test_emb_calculator.get_recommendation(entities)
    # print(result)
    # labels = ["Bruce Willis"]
    # # test_results = test_emb_calculator.get_most_likely_results(labels, 3)
    # test_results = test_emb_calculator.get_entity_identifier(labels[0])
    # print(test_results)
    # ent_identifier = test_results.split("/")[-1]
    # print(ent_identifier)
    test= test_emb_calculator.ent2lbl[WD['Q457180']]
    print(test)