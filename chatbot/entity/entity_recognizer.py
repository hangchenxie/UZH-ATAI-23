import json
import pandas as pd
import sparknlp
import pyspark.sql.functions as F
from pyspark.ml import Pipeline
from pyspark.sql import SparkSession
from sparknlp.annotator import *
from sparknlp.base import *
from sparknlp.pretrained import PretrainedPipeline
from pyspark.sql.types import StringType, IntegerType
from chatbot import cache
from pathlib import Path
import re
from rapidfuzz import fuzz



ent_lbl_path = Path(__file__).parents[1].joinpath("data", "ent_lbl.json")

with open(ent_lbl_path, 'rb') as file:
    ent_lbl = json.load(file)

spark = sparknlp.start()

# @cache.memoize(timeout=0)
def create_pipeline():

    document_assembler = DocumentAssembler() \
    .setInputCol('text') \
    .setOutputCol('document')

    tokenizer = Tokenizer() \
    .setInputCols(['document']) \
    .setOutputCol('token')

    embeddings = DistilBertEmbeddings\
    .pretrained('distilbert_base_cased', 'en')\
    .setInputCols(["token", "document"])\
    .setOutputCol("embeddings")

    ner_model = NerDLModel.pretrained('ner_mit_movie_simple_distilbert_base_cased', 'en') \
    .setInputCols(['document', 'token', 'embeddings']) \
    .setOutputCol('ner')

    ner_converter = NerConverter() \
    .setInputCols(['document', 'token', 'ner']) \
    .setOutputCol('entities')

    pipeline = Pipeline(stages=[
        document_assembler, 
        tokenizer,
        embeddings,
        ner_model,
        ner_converter
    ])
    return pipeline

class EntityRecognizer:

    def __init__(self):
        self.pipeline = create_pipeline()


    def match_entity_label(self, entity, ent_lbl):
        if entity in ent_lbl: return entity, 100.
        else:
            matched_ent_lbl, r = None, 0
            for e in ent_lbl:
                ratio = fuzz.ratio(e.lower(), entity.lower())
                if ratio > r: matched_ent_lbl, r = e, ratio
            return matched_ent_lbl, r
        # ratio_list = {}
        # for e in ent_lbl:
        #     ratio = fuzz.ratio(e.lower, entity.lower())
        #     if ratio > r:
        #         ratio_list[e] = float(ratio)
        # desired_ratio = max(ratio_list.values())
        # # Get the key (keyword) corresponding to the maximum ratio
        # desired_key = [key for key, value in ratio_list.items() if value == desired_ratio][0]
        # matched_rel_lbl, r = desired_key, desired_ratio
        # return matched_rel_lbl, r


    def get_entities(self, text):
        
        text = spark.createDataFrame(pd.DataFrame({'text': [text,]}))
        result = self.pipeline.fit(text).transform(text)
        ent_dict = {row["result"]: {"type": row["metadata"]["entity"]} for row in result.select("entities").collect()[0][0]}
        for ent in ent_dict.keys():
            ent_dict[ent]["matched_lbl"] = self.match_entity_label(ent, ent_lbl)[0]
            ent_dict[ent]["score"] = self.match_entity_label(ent, ent_lbl)[1]
        return ent_dict


if __name__ == "__main__":
    entity_recognizer = EntityRecognizer()
    text_list = 'Given that I like The Lion King, Pocahontas, and The Beauty and the Beast, can you recommend some movies? '

    entities_in_text = entity_recognizer.get_entities(text_list)
    print(entities_in_text)

    # matched_entity = entity_recognizer.match_entity_to_label('harry potter', ent_lbl)



