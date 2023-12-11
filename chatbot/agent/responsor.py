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
            print(f"entity_dict: {entity_dict}")
            print(f"relation_dict: {relation_dict}")
        except Exception as exception:
            print(f"Identify Error: {type(exception).__name__}")
            return f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"

        # Example:
        # message: Given that I like The Lion King, Pocahontas, and The Beauty and the Beast, can you recommend some movies? 
        # ent_dict = {
        #  'movie_ner_entities': 
        #    {0: {'entity': 'The Lion King, Pocahontas, and The Beauty and the Beast', 'type': 'TITLE', 'begin': 18, 'end': 72, 'matched_lbl': 'Enchanted Tale of Beauty and the Beast', 'score': 66.66666666666667}}, 
        #  'token_ner_entities': 
        #    {0: {'entity': 'The Lion King', 'type': 'MISC', 'begin': 18, 'end': 30, 'matched_lbl': 'The Lion King', 'score': 100.0}, 
        #     1: {'entity': 'Pocahontas', 'type': 'ORG', 'begin': 33, 'end': 42, 'matched_lbl': 'Pocahontas', 'score': 100.0}, 
        #     2: {'entity': 'The Beauty and the Beast', 'type': 'MISC', 'begin': 49, 'end': 72, 'matched_lbl': 'Beauty and the Beast', 'score': 90.9090909090909}
        #    }
        # }

        # use matched_lbl in token_ner_entities
        # ent_lbl = [entity_dict[k]["matched_lbl"] for k in entity_dict.keys()]
        ent_lbl = [v['matched_lbl'] for v in entity_dict['token_ner_entities'].values()]
        rel_lbl = [v["relation"] for v in relation_dict.values()]
        token_count = len(ent_lbl)
        per_entities = [entity['matched_lbl'] for entity in entity_dict['token_ner_entities'].values() if entity['type'] == 'PER']
        per_count = len(per_entities)

        print(f"ent_lbl: {ent_lbl}")
        print(f"rel_lbl: {rel_lbl}")
        print(f"token_count: {token_count}")
        print(f"per_entities: {per_entities}")
        print(f"per_count: {per_count}")

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
                    use_sparql = False
                    use_embedding = False
                    use_crowdsource = True
                    use_image = False
                    use_recommendation = False


            if use_crowdsource:
                ent_identifier = self.emb_calculator.get_entity_identifier(ent_lbl[0])
                rel_identifier = self.emb_calculator.get_relation_identifier(rel_lbl[0])
                s = str(ent_identifier.split("/")[-1])
                p = str(rel_identifier)
                crowd_fix = self.crowdsource.search_crowdsource(s, p)
                if crowd_fix is not None:
                    o = crowd_fix["object"]
                    if str(o).startswith("Q"):
                        o = self.emb_calculator.ent2lbl[self.emb_calculator.WD[o]]
                    support_votes = crowd_fix["support_votes"]
                    reject_votes = crowd_fix["reject_votes"]
                    kappa = crowd_fix["kappa"]
                    template = random.choice(crowdsource_response_templates)
                    response_text += "\n"
                    response_text += template.format(o, support_votes, reject_votes, kappa)
                else:
                    print("use crowdsource fails, use sparql")
                    use_sparql = True

            if use_sparql:
                sparql_result = self.sparql_querier(ent_lbl, rel_lbl)
                if bool(sparql_result):
                    answer = sparql_result
                    template = random.choice(sparql_response_templates)
                    response_text = template.format(''.join(rel_lbl), ''.join(ent_lbl), answer)
                else:
                    print("use sparql fails, use embedding")
                    use_embedding = True

            if use_embedding:
                labels = ent_lbl + rel_lbl
                try:
                    emb_results = self.emb_calculator.get_most_likely_results(labels, 10)
                except Exception as exception:
                    print(f"Embedding Error: {type(exception).__name__}")
                    return f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"
                top_labels = [result['Label'] for result in emb_results[:3]]
                template = random.choice(embedding_response_templates)
                response_text = template.format(', '.join(top_labels))


            if use_image:

               if per_count == 0:
                    try:
                        image_url, image_type = self.image_process.get_image_movie(self.emb_calculator.get_entity_identifier(entity['matched_lbl']).split('/')[-1])
                    except Exception as exception:
                        print(f"Image Error: {type(exception).__name__}")
                        return f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"
               else:
                    humans_id = [self.emb_calculator.get_entity_identifier(human).split('/')[-1] for human in per_entities]
                    try:
                        image_url, image_type = self.image_process.get_image_human(humans_id)
                    except Exception as exception:
                        print(f"Image Error: {type(exception).__name__}")
                        return f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"
               response_text = ''.join('image:' + image_url.replace(".jpg", ""))
               print(f"image_url: {image_url}, image_type: {image_type}")



            if use_recommendation:

                if token_count >= 2 and per_count == 0:
                    try:
                        recommendation = self.recommend.get_recommendation_movies(ent_lbl)[:10]
                        recommendation = random.sample(recommendation, 3)
                        template = random.choice(recommendation_response_templates)
                    except Exception as exception:
                        print(f"Recommendation Error: {type(exception).__name__}")
                        return f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"
                elif token_count == 1:
                    if per_count == 0:
                        try:
                            recommendation = self.recommend.get_recommendation_single_movie(ent_lbl[0])
                            recommendation = random.sample(recommendation, 3)
                            template = random.choice(recommendation_response_templates)
                        except Exception as exception:
                            print(f"Recommendation Error: {type(exception).__name__}")
                            return f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"
                    else:
                        try:
                            recommendation = self.recommend.get_recommendation_humans(ent_lbl[0])
                            template = random.choice(recommendation_response_templates)
                        except Exception as exception:
                            print(f"Recommendation Error: {type(exception).__name__}")
                            return f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"
                elif token_count == 2 and per_count == 1:
                     human = per_entities[0]
                     movie = list(set(ent_lbl) - set(per_entities))[0]
                     try:
                        recommendation = self.recommend.get_recommendation_human_movie(human, movie)
                        template = random.choice(recommendation_response_templates)
                     except Exception as exception:
                        print(f"Recommendation Error: {type(exception).__name__}")
                        return f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"
                else:
                    return f"Sorry I don't understand the question: '{message_text}'. Could you please rephrase it?"

                response_text = template.format(', '.join(recommendation))


        return response_text


if __name__ == "__main__":
    responsor = Responsor()
    questions = [


        "Who is the screenwriter of The Masked Gang: Cyprus?",
        "What is the MPAA film rating of Weathering with You?",
        "What is the country of citizenship of Olivier Schatzky?",

        "When was The Gofather released?",
        "Can you tell me the publication date of Tom Meets Zizou? ",#the answer is 2010-10-01 which is different from the answer from crowdsource which is 2011-01-01

        "Who is the director of Star Wars: Epode VI - Return of the Jedi?",
        "Who is the director of Good Will Huntin? ",
        "Who directed The Bridge on the River Kwai?",

        "What is the genre of Good Neighbors?",

        "What is the box office of The Princess and the Frog? ",
        "Who is the executive producer of X-Men: First Class? ",
        "What is the birthplace of Christopher Nolan? ",

        "Given that I like The Lion King, Pocahontas, and The Beauty and the Beast, can you recommend some movies? ",
        "Recommend movies like Nightmare on Elm Street, Friday the 13th, and Halloween. "
        "Recommend movies similar to Halmlet and Othello. ",
        "I really like Wes Anderson, what should I watch",
        "Can you recommend me some movies with Charlie Chaplin given that I liked The Great Dictator? ",
        "What should I watch after watching Snakes on a Train? ",
        "I liked the movie Kung Fu Panda, can you recommend 3 similar movies?   ",
        "Can you recommend me 3 movies similar to Forest Gump and The Lord of the Rings: The Fellowship of the Ring.",
        "Show me a picture of Halle Berry. ",
        " Show me a picture of Tom Cruise. ",
        "What does Julia Roberts look like? ",
        "Let me know what Sandra Bullock looks like. "

    ]
    for question in questions:
        answer = responsor.response(question)
        print(question)
        print(answer)