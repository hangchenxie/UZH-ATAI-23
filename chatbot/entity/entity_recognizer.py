import json
import pandas as pd
from chatbot.sparknlp_pipeline.sparknlp_pipeline import spark, movie_ner_pipeline, token_ner_pipeline
from chatbot import cache
from pathlib import Path
import re
from rapidfuzz import fuzz



ent_lbl_path = Path(__file__).parents[1].joinpath("data", "ent_lbl.json")

with open(ent_lbl_path, 'rb') as file:
    ent_lbl = json.load(file)


class EntityRecognizer:

    def __init__(self):
        self.movie_pipeline = movie_ner_pipeline
        self.token_pipeline = token_ner_pipeline


    def match_entity_label(self, entity, ent_lbl):
        if entity in ent_lbl: 
          return entity, 100.
        else:
            matched_ent_lbl, r = None, 0
            for e in ent_lbl:
                ratio = fuzz.ratio(e.lower(), entity.lower())
                if ratio > r: matched_ent_lbl, r = e, ratio
            return matched_ent_lbl, r


    def get_entities(self, message):

        text = spark.createDataFrame(pd.DataFrame({'text': [message,]}))
        movie_result = self.movie_pipeline.fit(text).transform(text)
        token_result = self.token_pipeline.fit(text).transform(text)
        # result.select("text", "entities").show(truncate=False)

        movie_ent_dict = {}
        movie_ent_rows = movie_result.select("entities").collect()[0][0]

        i = 0
        for row in movie_ent_rows:
            movie_ent_dict[i] = {}
            movie_ent_dict[i]['entity'] = row['result']
            movie_ent_dict[i]['type'] = row['metadata']['entity']
            movie_ent_dict[i]['begin'] = row['begin']
            movie_ent_dict[i]['end'] = row['end']
            match_ent_lbl = self.match_entity_label(row['result'], ent_lbl)
            movie_ent_dict[i]["matched_lbl"], movie_ent_dict[i]["score"] = match_ent_lbl[0], match_ent_lbl[1]
            i += 1

        token_ent_dict = {}
        token_ent_rows = token_result.select("entities").collect()[0][0]
        i = 0
        for row in token_ent_rows:
            if i > 0 and (\
                (row['begin'] - token_ent_dict[i-1]['end'] == 2 and message[row['begin']-1] == " ") or \
                (row['begin'] - token_ent_dict[i-1]['end'] == 3 and message[row['begin']-2] == ".") or \
                (row['begin'] - token_ent_dict[i-1]['end'] == 3 and message[row['begin']-2] == ":") \
            ):
                token_ent_dict[i-1]['entity'] = message[token_ent_dict[i-1]['begin']:row['end']+1]
                token_ent_dict[i-1]['end'] = row['end']
                token_ent_dict[i-1]['type'] = row['metadata']['entity']
                match_ent_lbl = self.match_entity_label(token_ent_dict[i-1]['entity'], ent_lbl)
                token_ent_dict[i-1]["matched_lbl"], token_ent_dict[i-1]["score"] = match_ent_lbl[0], match_ent_lbl[1]
            else:
                token_ent_dict[i] = {}
                token_ent_dict[i]['entity'] = row['result']
                token_ent_dict[i]['type'] = row['metadata']['entity']
                token_ent_dict[i]['begin'] = row['begin']
                token_ent_dict[i]['end'] = row['end']
                match_ent_lbl = self.match_entity_label(row['result'], ent_lbl)
                token_ent_dict[i]["matched_lbl"], token_ent_dict[i]["score"] = match_ent_lbl[0], match_ent_lbl[1]
                i += 1

        return {"movie_ner_entities": movie_ent_dict, "token_ner_entities": token_ent_dict}



if __name__ == "__main__":
    entity_recognizer = EntityRecognizer()
    text_list = 'Given that I like The Lion King, Pocahontas, and The Beauty and the Beast, can you recommend some movies? '

    entities_in_text = entity_recognizer.get_entities(text_list)
    print(entities_in_text)



