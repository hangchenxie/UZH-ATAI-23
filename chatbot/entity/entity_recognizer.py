import json
import pandas as pd
import numpy as np

import sparknlp
import pyspark.sql.functions as F
from pyspark.ml import Pipeline
from pyspark.sql import SparkSession
from sparknlp.annotator import *
from sparknlp.base import *
from sparknlp.pretrained import PretrainedPipeline
from pyspark.sql.types import StringType, IntegerType
from flask_caching import Cache

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
        entities = result.select("text", "entities").toPandas()

        return entities


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
        "What is the box office of The Princess and the Frog? ",
        'Can you tell me the publication date of Tom Meets Zizou? ',
        'Who is the executive producer of X-Men: First Class? '
        "Who is the director of Good Will Hunting? ",
        'Who directed The Bridge on the River Kwai?',
        "Who is the director of Star Wars: Episode VI - Return of the Jedi?",
        "Who is the screenwriter of The Masked Gang: Cyprus?",
        "What is the MPAA film rating of Weathering with You?",
        "What is the genre of Good Neighbors?",
        "What is the box office of The Princess and the Frog? ",
        'Can you tell me the publication date of Tom Meets Zizou? ',
        'Who is the executive producer of X-Men: First Class? '
    ]
    entities_in_text = entity_recognizer.get_entities(text_list)
    print(entities_in_text)


