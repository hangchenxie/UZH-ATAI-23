import json
import pandas as pd
from chatbot.sparknlp_pipeline.sparknlp_pipeline import spark, token_ner_pipeline, movie_ner_pipeline
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
        # if message[-1] in ["?", "."]:
        #     message = message[:-1]
        text = spark.createDataFrame(pd.DataFrame({'text': [message,]}))
        movie_result = self.movie_pipeline.fit(text).transform(text)
        # result.select("text", "entities").show(truncate=False)
        movie_ent_list = []
        movie_ent_rows = movie_result.select("entities").collect()[0][0]
        i = 0
        for row in movie_ent_rows:
            movie_ent_list.append({})
            movie_ent_list[i]['ner'] = "movie_ner"
            movie_ent_list[i]['entity'] = row['result']
            movie_ent_list[i]['type'] = row['metadata']['entity']
            movie_ent_list[i]['begin'] = row['begin']
            movie_ent_list[i]['end'] = row['end']
            match_ent_lbl = self.match_entity_label(row['result'], ent_lbl)
            movie_ent_list[i]["matched_lbl"], movie_ent_list[i]["score"] = match_ent_lbl[0], match_ent_lbl[1]
            i += 1

        token_result = self.token_pipeline.fit(text).transform(text)
        token_ent_list = []
        token_ent_rows = token_result.select("entities").collect()[0][0]
        i = 0
        for row in token_ent_rows:
            if i > 0 and (\
                (row['begin'] - token_ent_list[i-1]['end'] == 2 and message[row['begin']-1] == " ") or \
                (row['begin'] - token_ent_list[i-1]['end'] == 3 and message[row['begin']-2] == ".") or \
                (row['begin'] - token_ent_list[i-1]['end'] == 3 and message[row['begin']-2] == ":") or \
                (row['begin'] - token_ent_list[i-1]['end'] == 4 and message[row['begin']-2] == "-")  \
            ):
                token_ent_list[i-1]['entity'] = message[token_ent_list[i-1]['begin']:row['end']+1]
                token_ent_list[i-1]['end'] = row['end']
                token_ent_list[i-1]['type'] = row['metadata']['entity']
                match_ent_lbl = self.match_entity_label(token_ent_list[i-1]['entity'], ent_lbl)
                token_ent_list[i-1]["matched_lbl"], token_ent_list[i-1]["score"] = match_ent_lbl[0], match_ent_lbl[1]
            else:
                token_ent_list.append({})
                token_ent_list[i]['ner'] = "token_ner"
                token_ent_list[i]['entity'] = row['result']
                token_ent_list[i]['type'] = row['metadata']['entity']
                token_ent_list[i]['begin'] = row['begin']
                token_ent_list[i]['end'] = row['end']
                match_ent_lbl = self.match_entity_label(row['result'], ent_lbl)
                token_ent_list[i]["matched_lbl"], token_ent_list[i]["score"] = match_ent_lbl[0], match_ent_lbl[1]
                i += 1

        mixed_ent_list = []
        message_remain = message
        
        for movie_ent in movie_ent_list:
          if movie_ent['entity'] in message_remain and \
             movie_ent['score'] > 95 and \
             movie_ent['entity'] not in ['MPAA', 'PG', 'PG-13', 'R', 'G', 'NC-17', 'NR', 'UA',]:
            # check in token_ent_list if there is an entity 
            # with the same begain, equal or larger end, and higher score
            # if so, keep this token entity, and remove it from the message
            # then continue on the remaining part of the message
            token_ent_found = 0
            for token_ent in token_ent_list:
              if token_ent['begin'] == movie_ent['begin'] and \
                 token_ent['end'] >= movie_ent['end'] and \
                 token_ent['score'] >= movie_ent['score']:
                 
                 token_ent_found = 1
                 mixed_ent_list.append(token_ent)
                 message_remain = message_remain.replace(token_ent['entity'], "")
                 break
            if token_ent_found:
              continue 
            else:
              mixed_ent_list.append(movie_ent)
              message_remain = message_remain.replace(movie_ent['entity'], "")

        for token_ent in token_ent_list:
          if token_ent['entity'] in message_remain and \
             token_ent['entity'] not in ['MPAA', 'PG', 'PG-13', 'R', 'G', 'NC-17', 'NR', 'UA',]:
            mixed_ent_list.append(token_ent)

        ent_dict = {
            "movie_ner_entities": movie_ent_list, 
            "token_ner_entities": token_ent_list,
            "mixed_ner_entities": mixed_ent_list,
            }
        
        return ent_dict



if __name__ == "__main__":
    entity_recognizer = EntityRecognizer()
    text_list = 'Given that I like The Lion King, Pocahontas, and The Beauty and the Beast, can you recommend some movies? '

    entities_in_text = entity_recognizer.get_entities(text_list)
    print(entities_in_text)



