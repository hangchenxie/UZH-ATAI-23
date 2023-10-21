import pickle
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import sparknlp
import pyspark.sql.functions as F
from pyspark.ml import Pipeline
from pyspark.sql import SparkSession
from sparknlp.annotator import *
from sparknlp.base import *
from sparknlp.pretrained import PretrainedPipeline
from pyspark.sql.types import StringType, IntegerType
from flask_caching import Cache
from pathlib import Path


ent_lbl_path = Path(__file__).parents[0].joinpath("data", "ent_lbl.pickle")

with open(ent_lbl_path, 'rb') as file:
    ent_lbl = pickle.load(file)

spark = sparknlp.start()

class EntityRecognizer:

    def __init__(self, entities_in_graph):
        self.entities = entities_in_graph
        self.pipeline = self.create_pipeline()

    
    def create_pipeline(self):

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


    def get_entities(self, text_list):
        
        text = spark.createDataFrame(pd.DataFrame({'text': text_list}))
        result = self.pipeline.fit(text).transform(text)

        return result.select('entities').collect()

    
    def match_entity_to_label(self, entity, ent_lbl):
        
        if entity not in ent_lbl:
            vectorizer = TfidfVectorizer()
            phrase_vectors = vectorizer.fit_transform(ent_lbl + [entity])
            similarities = cosine_similarity(phrase_vectors[:-1], phrase_vectors[-1])
            most_similar_index = np.argmax(similarities)
            most_similar_phrase = ent_lbl[most_similar_index]
            similarity_score = similarities[most_similar_index][0]
            print(f"The most similar phrase to '{entity}' is \
                  '{most_similar_phrase}' with a similarity score \
                    of {similarity_score:.4f}")
            
            return most_similar_phrase



if __name__ == "__main__":
    entity_recognizer = EntityRecognizer(entities_in_graph=[])
    text_list = [
        "What is the most current movie featuring Mat Damon",
        "What films use the song zippity do da",
        "In what genre is the movie Par 6",
        "Is there a documentary about the sports agency industry",
        "Channing Tatum has played what starring roles",
        "List of actors A Beautiful Mind",
        "Find the Melissa Leo Movie about smuggling illegals across the border",
        "Tell me the director, rating and publication date of a Apocalypse Now",
        "Avatar came out when and what did it gross",
        "Who is the director of Star Wars: Episode VI - Return of the Jedi? ",
        "Who is the screenwriter of The Masked Gang: Cyprus? ",
        "When was 'The Godfather' released? ",
    ]
    entities_in_text = entity_recognizer.get_entities(text_list)
    print(entities_in_text)

    matched_entity = entity_recognizer.match_entity_to_label('harry potter', ent_lbl)


