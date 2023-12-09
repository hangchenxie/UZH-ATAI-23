import csv
import numpy as np
from pathlib import Path
import rdflib
import json
import pandas as pd
from difflib import get_close_matches
from sklearn.metrics import pairwise_distances
from chatbot.embedding.embedding_calculator import EmbeddingCalculator
import re

movies_path = Path(__file__).parents[1].joinpath("data", "entity_movie.csv")
movies_df = pd.read_csv(movies_path)
movies_df = movies_df[movies_df['Movie'].notna()]
# genres_path = Path(__file__).parents[1].joinpath("data", "movies_genres.csv")
# genres_df = pd.read_csv(genres_path)

class Recommend(EmbeddingCalculator):

    def get_recommendation_movies(self, entities):
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

    def get_recommendation_humans(self, entity):
        entity_id = self.get_entity_identifier(entity).split('/')[-1]
        q = f"""
            PREFIX ddis: <http://ddis.ch/atai/>
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX schema: <http://schema.org/>
            SELECT ?lbl WHERE {{
                    ?movie wdt:P31 wd:Q11424 .
                    ?movie rdfs:label ?lbl .
                    {{
                        ?movie wdt:P57 wd:{entity_id} .
                    }} UNION {{
                        ?movie wdt:P161 wd:{entity_id} .
                    }}
                }}
            """
        print(q)
        try:
            q_result = self.graph.query(q)
        except Exception as exception:
            print(f"Query Error: {type(exception).__name__}")
            return None
        if q_result is None:
            return None
        else:
            q_result = pd.DataFrame(q_result,columns=q_result.vars)
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


    def get_recommendation_human_movie(self, human, movie):
        human_id = self.get_entity_identifier(human).split('/')[-1]
        movie_id = self.get_entity_identifier(movie).split('/')[-1]

        # First, get the genre of the movie
        genre_query = f"""
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            SELECT ?genre WHERE {{
                wd:{movie_id} wdt:P136 ?genre .
            }}
        """
        print(genre_query)
        try:
            genre_result = self.graph.query(genre_query)
        except Exception as exception:
            print(f"Query Error: {type(exception).__name__}")
            return None

        if genre_result is None:
            return None
        else:
            genre_result = pd.DataFrame(genre_result, columns=genre_result.vars)
            genre_id = genre_result.iloc[0, 0].split('/')[-1]
            print(f'genre: {genre_id}')

        # Then, query for other movies in the same genre that the human entity is involved in
        q = f"""
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            SELECT ?lbl WHERE {{
                ?movie wdt:P31 wd:Q11424 .
                ?movie rdfs:label ?lbl .
                ?movie wdt:P136 wd:{genre_id} .
                {{
                    ?movie wdt:P57 wd:{human_id} .
                }} UNION {{
                    ?movie wdt:P161 wd:{human_id} .
                }}
            }}
        """
        try:
            q_result = self.graph.query(q)
        except Exception as exception:
            print(f"Query Error: {type(exception).__name__}")
            return None

        if q_result is None:
            return None
        else:
            q_result = pd.DataFrame(q_result, columns=q_result.vars)
            print(f"q_result: {q_result}")
            lens = q_result.shape[0]
            items = q_result.iloc[:, 0].tolist()
            items_set = set(items)
            if movie in items_set:
                items_set.remove(movie)
            items = list(items_set)
            if lens > 1:
                last_item = items.pop()
                result = ', '.join(items) + ' and ' + last_item
            elif items:
                result = items[0]
            else:
                result = None

        return result





if __name__ == "__main__":
    test = Recommend()
    # entities = ['The Lion King', 'Pocahontas', ' The Beauty and the Beast']
    # entities = ['Nightmare on Elm Street', 'Friday the 13th', 'Halloween']
    # result = test.get_recommendation(entities)
    # print(result)
    # entity = ['Wes Anderson']
    # for e in entity:
    #     print(test.get_recommendation_humans(e))
    human = 'Charlie Chaplin'
    movie = 'The Great Dictator'
    print(test.get_recommendation_human_movie(human, movie))
