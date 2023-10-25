from pathlib import Path
from .. import cache
from ..parser.parser import MessageParser
from ..embedding.embedding_calculator import EmbeddingCalculator


class Responsor:

    def __init__(self):
        self.patterns = {}
        self.parser = MessageParser()
        self.emb_calculator = EmbeddingCalculator()

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
            use_embedding = True
            use_sparql = False
            entity_dict, relation_dict = self.parser.parse_entity_relation(message_text)
            print(f"entity_dict: {entity_dict}")
            print(f"relation_dict: {relation_dict}")
            ent_lbl = [entity_dict[k]["matched_lbl"] for k in entity_dict.keys()]
            rel_lbl = [v["relation"] for v in relation_dict.values()]
            for lbl in ["box office", "publication date", "IMDb ID", "image"]:
                if lbl in rel_lbl: 
                    use_embedding = False
                    use_sparql = True
            if use_embedding:
                labels = ent_lbl + rel_lbl
                emb_results = self.emb_calculator.get_most_likely_results(labels, 10)
                resonse_text = f"The answer from embeddings: {emb_results}"
            elif use_sparql:
                
                # TODO: use a sparql_querier class
                # resonse_text = self.sparql_querier(message_text)
                resonse_text = "I need to use sparql queries to answer this question."
        else:
            resonse_text = f"Sorry I don't understand the question: '{message_text}'. Could you please rephase it?"
        
        return resonse_text