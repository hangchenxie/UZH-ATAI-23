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
            ?movie rdfs:label "{}"@en .
            ?movie wdt:{} ?{} .
            ?{} rdfs:label ?lbl .
                }}'''.format(ent_lbl, rel_id, rel_lbl, rel_lbl)
        print(f"q: {q}")
        q_result = self.graph.query(q)
        if q_result is None:
            return None
        else:
            q_result = DataFrame(q_result,columns=q_result.vars)
            print(f"q_result: {q_result}")
            lens = q_result.shape[0]
            items = q_result.iloc[:,0].tolist()
            if lens > 1:
                last_item = items.pop()
                result = ', '.join(items) + ' and ' + last_item
            elif items:
                 result = items[0]
            else:
                result = None
        return result

    def change_type(self, type):
        type = str(type)
        if type == 'TITLE':
            return 'movie'
        else:
            type.lower()
            return type

    def convert_type(term):
        return int(term) if term.datatype == 'http://www.w3.org/2001/XMLSchema#integer' else str(term)


    def response(self, message_text):


            c = self.classify(message_text)

            if c == "SPARQL":
                try:
                    answer = [[self.convert_type(t) for t in s] for s in self.graph.query(message_text)]
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
                        if bool(sparql_result):
                            answer = sparql_result
                            resonse_text = f"The answer from sparql: {answer}"
                        else:
                            use_sparql = False
                            use_embedding = True
                if use_embedding:
                    labels = ent_lbl + rel_lbl
                    emb_results = self.emb_calculator.get_most_likely_results(labels, 10)
                    top_labels = [result['Label'] for result in emb_results[:3]]
                    resonse_text = f"The answer from embeddings: {', '.join(top_labels)}"
            else:
                resonse_text = f"Sorry I don't understand the question: '{message_text}'. Could you please rephase it?"

            return resonse_text

if __name__ == "__main__":
    responsor = Responsor()
    questions = [
        "Who is the director of Star Wars: Epode VI - Return of the Jedi?",
        "Who is the director of Good Will Huntin? ",
        'Who directed The Bridge on the River Kwai?',
        "Who is the screenwriter of The Masked Gang: Cyprus?",
        "What is the genre of Good Neighbors?",
        # "What is the box office of The Princess and the Frog? ",
        # 'Can you tell me the publication date of Tom Meets Zizou? ',
        # 'Who is the executive producer of X-Men: First Class? '
        # 'When was "The Gofather" released?',
        # "What is the MPAA film rating of Weathering with You?",
    ]
    for question in questions:
        answer = responsor.response(question)
        print(question)
        print(answer)