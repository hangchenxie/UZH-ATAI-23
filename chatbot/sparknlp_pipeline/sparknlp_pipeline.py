import sparknlp
import pyspark.sql.functions as F
from pyspark.ml import Pipeline
from pyspark.sql import SparkSession
from sparknlp.annotator import *
from sparknlp.base import *
from sparknlp.pretrained import PretrainedPipeline
from pyspark.sql.types import StringType, IntegerType


spark = sparknlp.start()


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

movie_ner_model = NerDLModel.pretrained(
    'ner_mit_movie_simple_distilbert_base_cased', 'en') \
.setInputCols(['document', 'token', 'embeddings']) \
.setOutputCol('ner')

token_ner_model = (
    BertForTokenClassification.pretrained("bert_base_token_classifier_conll03", "en")
    .setInputCols(["document", "token"])
    .setOutputCol("ner")
)

ner_converter = NerConverter() \
.setInputCols(['document', 'token', 'ner']) \
.setOutputCol('entities')

sentence = SentenceDetector() \
                .setInputCols(["document"]) \
                .setOutputCol("sentence")

embeddings_sentence = BertSentenceEmbeddings.pretrained("sent_small_bert_L2_128") \
                .setInputCols(["sentence"]) \
                .setOutputCol("sentence_bert_embeddings")\
                .setCaseSensitive(True) \
                .setMaxSentenceLength(512)


movie_ner_pipeline = Pipeline(stages=[
    document_assembler, 
    tokenizer,
    embeddings,
    movie_ner_model,
    ner_converter
])

token_ner_pipeline = Pipeline(stages=[
    document_assembler,
    tokenizer,
    token_ner_model,
    ner_converter
])

relation_pipeline = Pipeline(stages=[
    document_assembler,
    sentence,
    embeddings_sentence
])
