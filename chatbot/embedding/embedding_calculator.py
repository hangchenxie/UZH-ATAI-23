import csv
import numpy as np
from pathlib import Path
import rdflib
import json
import pandas as pd
from sklearn.metrics import pairwise_distances
from rdflib import Namespace
from chatbot.knowledge_graph.knowledge_graph import KnowledgeGraph

embeds_path = Path(__file__).parents[1].joinpath("data", "embeds")
entity_emb = np.load(embeds_path.joinpath('entity_embeds.npy'))
relation_emb = np.load(embeds_path.joinpath('relation_embeds.npy'))
entity_file = embeds_path.joinpath('entity_ids.del')
relation_file = embeds_path.joinpath('relation_ids.del')
lbl2rel_file = embeds_path.joinpath('property.json')

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


if __name__ == "__main__":
    test_emb_calculator = EmbeddingCalculator()
    labels = ["Bruce Willis"]
    # test_results = test_emb_calculator.get_most_likely_results(labels, 3)
    test_results = test_emb_calculator.get_entity_identifier(labels[0])
    print(test_results)
    ent_identifier = test_results.split("/")[-1]
    print(ent_identifier)