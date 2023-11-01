from pathlib import Path
import random
from chatbot.parser.parser import MessageParser
from chatbot.embedding.embedding_calculator import EmbeddingCalculator
from chatbot.knowledge_graph.knowledge_graph import KnowledgeGraph
import json
from pandas import DataFrame
from chatbot import cache

KG = KnowledgeGraph().graph
path = Path(__file__).parents[2].joinpath("data", "property.json")

label_flags = {
    "MPAA film rating": {"use_embedding": True, "use_sparql": False},
    "publication date": {"use_embedding": False, "use_sparql": True},
    "box office": {"use_embedding": False, "use_sparql": True},
    "IMDb ID": {"use_embedding": False, "use_sparql": True},
    "image": {"use_embedding": False, "use_sparql": True}
}

sparql_response_templates = [
    "The answer from sparql: {}",
    "According to sparql, the answer is: {}",
    "Sparql suggests that the answer could be: {}",
]

embedding_response_templates = [
    "The answer from embeddings: {}",
    "According to embeddings, the answer is: {}",
    "Embeddings suggest that the answer could be: {}",
]


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

    def sparql_querier(self, ent_lbl, rel_lbl):
        rel_id = self.lbl2prop[rel_lbl[0]]
        print(f"rel_id: {rel_id}")
        print(type(rel_id))
        ent_lbl = ''.join(ent_lbl)
        rel_lbl = ''.join(rel_lbl)
        rel_lbl = self.change_lbl_type(rel_lbl)
        if rel_lbl == "releaseDate":
            q = '''
                PREFIX ddis: <http://ddis.ch/atai/>
                PREFIX wd: <http://www.wikidata.org/entity/>
                PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                PREFIX schema: <http://schema.org/>

                SELECT ?releaseDate WHERE {{
                ?movie rdfs:label "{}"@en .
                ?movie wdt:P31 wd:Q11424 . 
                ?movie wdt:P577 ?releaseDate .
                    }}'''.format(ent_lbl)
            
        else:
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
        try:
            q_result = self.graph.query(q)
        except Exception as exception:
            print(f"Error: {type(exception).__name__}")
            return None
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

    def change_lbl_type(self, lbl):
        if lbl == "MPAA film rating":
            return "rating"
        elif lbl == "publication date":
            return "releaseDate"
        elif lbl == "box office":
            return "boxOffice"
        else:
            return lbl

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
            try:
                entity_dict, relation_dict = self.parser.parse_entity_relation(message_text)
            except Exception as exception:
                print(f"Error: {type(exception).__name__}")
                return f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"
            print(f"entity_dict: {entity_dict}")
            print(f"relation_dict: {relation_dict}")
            ent_lbl = [entity_dict[k]["matched_lbl"] for k in entity_dict.keys()]
            rel_lbl = [v["relation"] for v in relation_dict.values()]
            print(f"ent_lbl: {ent_lbl}")
            print(f"rel_lbl: {rel_lbl}")
            for lbl in rel_lbl:
                if lbl in label_flags:
                    use_embedding = label_flags[lbl]["use_embedding"]
                    use_sparql = label_flags[lbl]["use_sparql"]

            if use_sparql:
                sparql_result = self.sparql_querier(ent_lbl, rel_lbl)
                if bool(sparql_result):
                    answer = sparql_result
                    template = random.choice(sparql_response_templates)
                    return template.format(answer)
                else:
                    use_sparql = False
                    use_embedding = True

            if use_embedding:
                labels = ent_lbl + rel_lbl
                try:
                    emb_results = self.emb_calculator.get_most_likely_results(labels, 10)
                except Exception as exception:
                    print(f"Error: {type(exception).__name__}")
                    return f"Someting went wrong with the embeddings. Please try again."
                top_labels = [result['Label'] for result in emb_results[:3]]
                template = random.choice(embedding_response_templates)
                response_text = template.format(', '.join(top_labels))
            else:
                response_text = f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"
        return response_text

if __name__ == "__main__":
    responsor = Responsor()
    questions = [
        # "Who is the screenwriter of The Masked Gang: Cyprus?",
        # "What is the MPAA film rating of Weathering with You?",

        'When was "The Gofather" released?',

        # "Who is the director of Star Wars: Epode VI - Return of the Jedi?",
        # "Who is the director of Good Will Huntin? ",
        # 'Who directed The Bridge on the River Kwai?',
        #
        # "What is the genre of Good Neighbors?",


        # "What is the box office of The Princess and the Frog? ",
        # 'Can you tell me the publication date of Tom Meets Zizou? ',
        # 'Who is the executive producer of X-Men: First Class? '

    ]
    for question in questions:
        answer = responsor.response(question)
        print(question)
        print(answer)