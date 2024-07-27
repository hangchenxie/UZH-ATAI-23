from pathlib import Path
import re
from rapidfuzz import fuzz
import warnings
import json
from chatbot import cache
from chatbot.sparknlp_pipeline.sparknlp_pipeline import spark, relation_pipeline
import pyspark.sql.functions as F
from sklearn.metrics import pairwise_distances
import numpy as np


rel_lbl_path = Path(__file__).parents[1].joinpath("data", "my_property.json")

with open(rel_lbl_path, 'rb') as file:
    my_property = json.load(file)
lbl2relation = {item: values[0] for values in my_property.values() for item in values}
my_property_flat = [item for sublist in list(my_property.values()) for item in sublist]

class RelationRecognizer:
    def __init__(self):
        self.lbl2relation = lbl2relation
        self.pipeline = relation_pipeline
        self.property_embeds = self.generate_sentence_embeddings(my_property_flat)


    def generate_sentence_embeddings(self, sentences):
        # conver the input list to a 2-d array like [sentence_0], [sentence_1], [sentence_2]
        sentence_array = [[item] for item in sentences]
        df = spark.createDataFrame(sentence_array).toDF("text")
        model = relation_pipeline.fit(df)
        result = model.transform(df)
        result_df = result.select(F.explode(F.arrays_zip(result.sentence.result, 
                        result.sentence_bert_embeddings.embeddings)).alias("cols")) \
                        .select(F.expr("cols['0']").alias("sentence"),
                                F.expr("cols['1']").alias("embeddings"))
        # sentence = result_df.select('sentence').collect()
        embeddings = result_df.select('embeddings').collect()
        embeds_array = [np.array(embeddings[i]['embeddings']) for i in range(len(embeddings))]
        return embeds_array


    def find_most_similar_properties(self, text, property_labels, property_embeds, top_n):
    
        text_embeds = self.generate_sentence_embeddings([text])
        distances = pairwise_distances(text_embeds, property_embeds).reshape(-1)
        similarity = 100*(1-(distances-np.min(distances))/(np.max(distances)-np.min(distances)))
        most_likely = np.argsort(distances)[: top_n].tolist()
        
        most_likely_labels = [property_labels[i] for i in most_likely]
        most_likely_similarity = [similarity[i] for i in most_likely]

        print(f'text: {text}')
        print(f'most_likely_labels: {most_likely_labels}')
        print(f'most_likely_similarity: {most_likely_similarity}')

        return most_likely_labels, most_likely_similarity

    def match_rel_label(self, text):
        if text in self.lbl2relation: return self.lbl2relation[text], 100.
        else:
            # matched_rel_lbl, r = None, 0
            # ratio_list = {}
            # for e in self.lbl2relation:
            #     ratio = fuzz.ratio(e, text.lower())
            #     ratio_list[e] = float(ratio)
            # # print("ratio_list:", ratio_list)
            # desired_ratio = max(ratio_list.values())
            # # Get the key (keyword) corresponding to the maximum ratio
            # desired_key = [key for key, value in ratio_list.items() if value == desired_ratio][0]

            # TODO: use sentence embedding to find the most similar property
            most_likely_labels, most_likely_similarity = self.find_most_similar_properties(text, my_property_flat, self.property_embeds, 5)

            # matched_rel_lbl, r = self.lbl2relation[desired_key], desired_ratio
            matched_rel_lbl, r = self.lbl2relation[most_likely_labels[0]], most_likely_similarity[0]

            return matched_rel_lbl, r
        
        
    def get_relation(self, text):
        relation, score = self.match_rel_label(text)
        return {"relation": relation, "score": score}


if __name__ == '__main__':
    rr = RelationRecognizer()
    questions = [
        # "Who is the director of Star Wars: Episode VI - Return of the Jedi?",
        # "Who is the director of Star Wars: Episde VI - Return of the Jedi?",
        # "Who is the director of Good Will Hunting? ",
        # 'Who directed The Bridge on the River Kwai?',
        # "Who is the screenwriter of The Masked Gang: Cyprus?",
        # "What is the MPAA film rating of Weathering with You?",
        # "What is the genre of Good Neighbors?",
        # "What is the box office of The Princess and the Frog? ",
        # 'Can you tell me the publication date of Tom Meets Zizou? ',
        # 'Who is the executive producer of X-Men: First Class? '
        # 'When was "The Godfather" released?'
        # 'Show me a picture of Halle Berry.',
        # 'What does Julia Roberts look like?',
        # 'Let me know what Sandra Bullock looks like.'
        # "Given that I like The Lion King, Pocahontas, and The Beauty and the Beast, can you recommend some movies? ",
        # "Recommend movies like Nightmare on Elm Street, Friday the 13th, and Halloween. "
        'MPAA film rating'
    ]
    for question in questions:
        print(question)
        print(f'relation:{rr.get_relation(question)}')
