import csv
import numpy as np
from pathlib import Path
import rdflib
import json
import pandas as pd
from difflib import get_close_matches
from sklearn.metrics import pairwise_distances
from chatbot.embedding.embedding_calculator import EmbeddingCalculator

movies_path = Path(__file__).parents[1].joinpath("data", "entity_movie.csv")
movies_df = pd.read_csv(movies_path)
movies_df = movies_df[movies_df['Movie'].notna()]
# genres_path = Path(__file__).parents[1].joinpath("data", "movies_genres.csv")
# genres_df = pd.read_csv(genres_path)

class Recommend(EmbeddingCalculator):
    def get_recommendation(self, entities):
        movie_lbls = movies_df['Movie'].tolist()
        movies_list = [get_close_matches(ent.strip(), movie_lbls)[0] for ent in entities]
        print("movies_list:", movies_list)
        # genres_list = [genres_df.loc[genres_df['title'] == movie, 'genres'].values[0].split('|') for movie in movies_list]
        # genres_list = [genres_df.loc[genres_df['title'] == movie, 'genres'].values[0].split('|') if not genres_df.loc[genres_df['title'] == movie, 'genres'].empty else [] for movie in movies_list]
        movies_id = [self.ent2id[self.lbl2ent[movie]] for movie in movies_list]
        print("movies_id:", movies_id)
        movies_emb = np.array([self.ent_emb[i] for i in movies_id])
        avg = np.average(movies_emb, axis=0)
        dist = pairwise_distances(avg.reshape(1, -1), self.ent_emb).reshape(-1).argsort()
        most_likely_results_df = pd.DataFrame([
            (self.id2ent[idx][len(self.WD):], self.ent2lbl[self.id2ent[idx]], dist[idx], rank+1)
            for rank, idx in enumerate(dist[:20])
            if self.ent2lbl[self.id2ent[idx]] not in movies_list and
               "Sony Pictures Universe of Marvel Characters" not in self.ent2lbl[self.id2ent[idx]]],
            columns=('Entity', 'Label', 'Score', 'Rank'))
        # most_likely_results_df = most_likely_results_df[most_likely_results_df['Genre'].isin(genres_list)]
        most_likely_results = most_likely_results_df.to_dict('records')
        print("most_likely_results:", most_likely_results)
        recommended_movies = [result['Label'] for result in most_likely_results]
        return recommended_movies


if __name__ == "__main__":
    test = Recommend()
    # entities = ['The Lion King', 'Pocahontas', ' The Beauty and the Beast']
    entities = ['Nightmare on Elm Street', 'Friday the 13th', 'Halloween']
    result = test.get_recommendation(entities)
    print(result)
