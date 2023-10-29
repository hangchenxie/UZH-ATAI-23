from pathlib import Path

from chatbot.parser.parser import MessageParser
from chatbot.embedding.embedding_calculator import EmbeddingCalculator
from chatbot.knowledge_graph.knowledge_graph import KnowledgeGraph
import json
from pandas import DataFrame
from chatbot import cache

KG = KnowledgeGraph().graph
path = Path(__file__).parents[2].joinpath("data", "property.json")



class Responsor:

    def __init__(self):
        self.patterns = {}
        self.parser = MessageParser()
        self.emb_calculator = EmbeddingCalculator()
        self.graph = KG
        with open(path,"r",encoding="utf-8") as f:
            self.prop2lbl = json.load(f)
        self.lbl2prop = {lbl: prop for prop, lbl in self.prop2lbl.items()}


    # TODO: classify message_text by patterns
    def classify(self, message_text):
        m = message_text
        if m.startswith("PREFIX"):
            return "SPARQL"
        elif m.startswith("Wh"):
            return "Wh- question"
        elif m.startswith("How"):
            return "How- question"
        elif "highest" in m:
            return "rank question"
        elif "recommend" in m:
            return "recommendation"
        else:
            return "other"

    def sparql_querier(self, ent_lbl, rel_lbl, ent_type):
        rel_id = self.lbl2prop[rel_lbl[0]]
        print(f"rel_id: {rel_id}")
        print(type(rel_id))
        ent_lbl = ''.join(ent_lbl)
        rel_lbl = ''.join(rel_lbl)
        q ='''
            PREFIX ddis: <http://ddis.ch/atai/>
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX schema: <http://schema.org/>
        
            SELECT ?lbl WHERE {{
            ?{} rdfs:label "{}"@en .
            ?{} wdt:{} ?{} .
            ?{} rdfs:label ?lbl .
                }}'''.format(ent_type, ent_lbl,ent_type, rel_id, rel_lbl, rel_lbl)
        print(f"q: {q}")
        q_result = [str(s) for s in self.graph.query(q)]
        if q_result is None:
            return None
        else:
            result = q_result
            print(f"result: {result}")
        # print(f"q_result: {q_result}")
        # q_result = DataFrame(q_result,columns=q_result.vars)
        # print(f"q_result: {q_result}")
        # if q_result.shape[0]==0:
        #     print(f"The {rel_lbl} of {ent_lbl} isn't in the KG")
        #     return None
        # else:
        #     lens = q_result.shape[0]
        #     items = q_result.iloc[:,0].tolist()
        #     if lens > 1:
        #         last_item = items.pop()
        #         result = ', '.join(items) + ' and ' + last_item
        #     elif items:
        #          result = items[0]
        #     else:
        #         result = None
        return result

    def change_type(self, type):
        type = str(type)
        if type == 'TITLE':
            return 'movie'


    def response(self, message_text):
        
        def convert_type(term):
                return int(term) if term.datatype == 'http://www.w3.org/2001/XMLSchema#integer' else str(term)

        c = self.classify(message_text)

        if c == "SPARQL":
            try:
                answer = [[convert_type(t) for t in s] for s in self.graph.query(message_text)]
                resonse_text = f"{answer}"
            except Exception as exception:
                resonse_text = f"Error: {type(exception).__name__}"
        elif c in ["Wh- question", "How- question", "rank question", "recommendation", "other"]:
            use_embedding = False
            use_sparql = True
            entity_dict, relation_dict = self.parser.parse_entity_relation(message_text)
            print(f"entity_dict: {entity_dict}")
            print(f"relation_dict: {relation_dict}")
            ent_lbl = [entity_dict[k]["matched_lbl"] for k in entity_dict.keys()]
            rel_lbl = [v["relation"] for v in relation_dict.values()]
            print(f"ent_lbl: {ent_lbl}")
            print(f"rel_lbl: {rel_lbl}")
            ent_type = self.change_type((entity_dict[list(entity_dict.keys())[0]]["type"]))
            print(f"ent_type: {ent_type}")
            for lbl in ["box office", "publication date", "IMDb ID", "image"]:
                if lbl in rel_lbl: 
                    use_embedding = False
                    use_sparql = True
                elif use_sparql:
                    # TODO: use a sparql_querier class
                    sparql_result = self.sparql_querier(ent_lbl, rel_lbl, ent_type)
                    if sparql_result is not None:
                        resonse_text = f"The answer from sparql: {sparql_result}"
                    if sparql_result is None:
                        use_sparql = False
                        use_embedding = True
            if use_embedding:
                labels = ent_lbl + rel_lbl
                emb_results = self.emb_calculator.get_most_likely_results(labels, 10)
                resonse_text = f"The answer from embeddings: {emb_results}"
        else:
            resonse_text = f"Sorry I don't understand the question: '{message_text}'. Could you please rephase it?"
        
        return resonse_text

if __name__ == "__main__":
    responsor = Responsor()
    while True:
        try:
            print('Enter your question:')
            message_text = input()
            answer = responsor.response(message_text)
            print(answer)
        except KeyboardInterrupt:
            break