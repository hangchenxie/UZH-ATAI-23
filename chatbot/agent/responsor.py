from pathlib import Path
import random
from chatbot.parser.parser import MessageParser
from chatbot.embedding.embedding_calculator import EmbeddingCalculator
from chatbot.knowledge_graph.knowledge_graph import KnowledgeGraph
from chatbot.image.image_process import ImageProcess
from chatbot.entity.entity_recognizer import EntityRecognizer
from chatbot.recommend.recommend import Recommend
from chatbot.crowdsource.crowdsource import CrowdSource
import json
from pandas import DataFrame
from chatbot import cache

KG = KnowledgeGraph().graph
path = Path(__file__).parents[1].joinpath("data", "property.json")

label_flags = {
    "MPAA film rating": {"use_embedding": True, "use_sparql": False, "use_image": False, "use_recommendation": False, "use_crowdsource": False},
    "publication date": {"use_embedding": False, "use_sparql": True, "use_image": False, "use_recommendation": False, "use_crowdsource": False},
    "IMDb ID": {"use_embedding": False, "use_sparql": True, "use_image": False, "use_recommendation": False, "use_crowdsource": False},
    "image": {"use_embedding": False, "use_sparql": False, "use_image": True, "use_recommendation": False, "use_crowdsource": False},
    "recommend": {"use_embedding": False, "use_sparql": False, "use_image": False, "use_recommendation": True, "use_crowdsource": False},
    "executive producer": {"use_embedding": False, "use_sparql": False, "use_image": False, "use_recommendation": False, "use_crowdsource": True},
    "box office": {"use_embedding": False, "use_sparql": False, "use_image": False, "use_recommendation": False, "use_crowdsource": True},
}

sparql_response_templates = [
    "I think the {} of {} is {}. (The answer from sparql)",
    "I guess the {} of {} is {}. (According to sparql)",
    "I think the answer to the {} of {} is {}. (Sparql suggests that the answer)",
]

embedding_response_templates = [
    "I would guess the answer could be one of them in {} . (The answer from embeddings)",
    "I would say one of {} might be a correct answer. (According to embeddings)",
    "I suggest that the answer could be: {}. (Embeddings)",
]

recommendation_response_templates = [
    "Similar movies are : {}",
    "You will probably like : {}",
    "I would recommend you to watch: {}",
]

crowdsource_response_templates = [
    "According to crowdsource, the answer is: {}, the support votes are: {}, the reject votes are: {}, the inter-rater agreement is: {} ",
    "The answer from crowdsource: {}, the support votes are: {}, the reject votes are: {}, the inter-rater agreement is: {} ",
    "Crowdsource suggests that the answer could be: {}, the support votes are: {}, the reject votes are: {}, the inter-rater agreement is: {} "
]






class Responsor:

    def __init__(self):
        self.patterns = {}
        self.parser = MessageParser()
        self.emb_calculator = EmbeddingCalculator()
        self.graph = KG
        self.image_process = ImageProcess()
        self.ent_recognizer = EntityRecognizer()
        self.recommend = Recommend()
        self.crowdsource = CrowdSource()
        with open(path,"r",encoding="utf-8") as f:
            self.rel2lbl = json.load(f)
        self.lbl2rel = {lbl: prop for prop, lbl in self.rel2lbl.items()}


    # TODO: classify message_text by patterns
    def classify(self, message_text):
        m = message_text
        if m.startswith("PREFIX"):
            return "SPARQL"
        else:
            return "other"

    def sparql_querier(self, ent_lbl, rel_lbl):
        rel_id = self.lbl2rel[rel_lbl[0]]
        print(f"rel_id: {rel_id}")
        print(type(rel_id))
        ent_lbl = ''.join(ent_lbl)
        rel_lbl = ''.join(rel_lbl)
        # rel_lbl = self.change_lbl_type(rel_lbl)
        if rel_lbl == "publication date":
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
            print(f"Factual Error: {type(exception).__name__}")
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

    # def change_lbl_type(self, lbl):
    #     if lbl == "MPAA film rating":
    #         return "rating"
    #     elif lbl == "publication date":
    #         return "releaseDate"
    #     else:
    #         return lbl

    def convert_type(term):
        return int(term) if term.datatype == 'http://www.w3.org/2001/XMLSchema#integer' else str(term)


    def response(self, message_text):
        c = self.classify(message_text)
        response_text = ""
        try:
            entity_dict, relation_dict = self.parser.parse_entity_relation(message_text)
        except Exception as exception:
            print(f"Identify Error: {type(exception).__name__}")
            return f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"

        ent_lbl = [entity_dict[k]["matched_lbl"] for k in entity_dict.keys()]
        rel_lbl = [v["relation"] for v in relation_dict.values()]

        if c == "SPARQL":
            try:
                answer = [[self.convert_type(t) for t in s] for s in self.graph.query(message_text)]
                response_text = f"{answer}"
            except Exception as exception:
                response_text = f"Sparql Error: {type(exception).__name__}"
        else:

            for lbl in rel_lbl:
                if lbl in label_flags:
                    use_embedding = label_flags[lbl]["use_embedding"]
                    use_sparql = label_flags[lbl]["use_sparql"]
                    use_crowdsource = label_flags[lbl]["use_crowdsource"]
                    use_image = label_flags[lbl]["use_image"]
                    use_recommendation = label_flags[lbl]["use_recommendation"]
                else:
                    use_sparql = True
                    use_embedding = False
                    use_crowdsource = False
                    use_image = False
                    use_recommendation = False



            if use_sparql:
                sparql_result = self.sparql_querier(ent_lbl, rel_lbl)
                if bool(sparql_result):
                    answer = sparql_result
                    template = random.choice(sparql_response_templates)
                    response_text = template.format(''.join(rel_lbl), ''.join(ent_lbl), answer)
                else:
                    print("use sparql fails, use crowdsource")
                    use_crowdsource = True
            if use_crowdsource:
                ent_identifier = self.emb_calculator.get_entity_identifier(ent_lbl[0])
                rel_identifier = self.emb_calculator.get_relation_identifier(rel_lbl[0])
                s = "wd:" + str(ent_identifier.split("/")[-1])
                p = "wdt:" + str(rel_identifier)
                if bool(self.crowdsource.search_crowdsource(s, p)):
                    o,support_votes, reject_votes, kappa = self.crowdsource.search_crowdsource(s, p)
                    if o.startswith("wd:"):
                        o = o.replace("wd:", "")
                        o = self.emb_calculator.ent2lbl[self.emb_calculator.WD[o]]
                    template = random.choice(crowdsource_response_templates)
                    response_text = template.format(o, support_votes, reject_votes, kappa)
                else:
                    print("use crowdsource fails, use embedding")
                    use_embedding = True
            if use_embedding:
                labels = ent_lbl + rel_lbl
                try:
                    emb_results = self.emb_calculator.get_most_likely_results(labels, 10)
                except Exception as exception:
                    print(f"Error: {type(exception).__name__}")
                    return f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"
                top_labels = [result['Label'] for result in emb_results[:3]]
                template = random.choice(embedding_response_templates)
                response_text = template.format(', '.join(top_labels))


            if use_image:
                ent_identifier = self.emb_calculator.get_entity_identifier(ent_lbl[0])
                try:
                    image_url, image_type = self.image_process.get_image(ent_identifier.split("/")[-1])
                except Exception as exception:
                    print(f"Image Error: {type(exception).__name__}")
                    return f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"
                response_text = 'image:' + image_url.replace(".jpg", "")

            if use_recommendation:
                entities = ', '.join(entity for entity in entity_dict.keys())
                entities = entities.replace(", and", ", ")
                entities = [entity for entity in entities.split(", ")]
                try:
                    recommendation = self.recommend.get_recommendation(entities)[:10]
                    recommendation = random.sample(recommendation, 3)
                    template = random.choice(recommendation_response_templates)
                except Exception as exception:
                    print(f"Recommendation Error: {type(exception).__name__}")
                    return f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"
                response_text = template.format(', '.join(recommendation))

        return response_text


if __name__ == "__main__":
    responsor = Responsor()
    questions = [
        "Who is the screenwriter of The Masked Gang: Cyprus?",
        "What is the MPAA film rating of Weathering with You?",
        "What is the country of citizenship of Olivier Schatzky?",

        'When was "The Gofather" released?',
        'Can you tell me the publication date of Tom Meets Zizou? ',#the answer is 2010-10-01 which is different from the answer from crowdsource which is 2011-01-01

        "Who is the director of Star Wars: Epode VI - Return of the Jedi?",
        "Who is the director of Good Will Huntin? ",
        'Who directed The Bridge on the River Kwai?',

        "What is the genre of Good Neighbors?",

        "What is the box office of The Princess and the Frog? ",
        "Who is the executive producer of X-Men: First Class? ",
        "What is the birthplace of Christopher Nolan? ",

        "Given that I like The Lion King, Pocahontas, and The Beauty and the Beast, can you recommend some movies? ",
        "Recommend movies like Nightmare on Elm Street, Friday the 13th, and Halloween. "

        'Show me a picture of Halle Berry. ',
        'Show me a picture of Tom Cruise. ',
        'What does Julia Roberts look like? ',
        'Let me know what Sandra Bullock looks like. '

    ]
    for question in questions:
        answer = responsor.response(question)
        print(question)
        print(answer)