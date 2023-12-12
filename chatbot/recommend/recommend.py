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
from SPARQLWrapper import SPARQLWrapper, JSON

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


    def get_recommendation_single_movie(self, movie):

        df = pd.read_csv('../data/movies_genres.csv')

        # Filter the DataFrame to get the row that matches the given movie
        try:
            movie_row = df.loc[df['title'] == movie, 'genres'].values[0].split('|')
        except Exception as exception:
            print(f"CSV Error: {type(exception).__name__}")
            movie_row = None

        print(f'movie_row: {movie_row}')

        if movie_row:
            genre_set = movie_row
        else:
            movie_id = self.get_entity_identifier(movie).split('/')[-1]
            sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
            genre_query = f"""
                PREFIX wd: <http://www.wikidata.org/entity/>
                PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT ?genreLabel WHERE {{
                    wd:{movie_id} wdt:P136 ?genre .
                    ?genre rdfs:label ?genreLabel .
                    FILTER(LANG(?genreLabel) = "en")
                }}
            """
            sparql.setQuery(genre_query)
            sparql.setReturnFormat(JSON)
            try:
                genre_result = sparql.query().convert()
            except Exception as exception:
                print(f"Query Error: {type(exception).__name__}")
                return None

            genre_list = [result["genreLabel"]["value"] for result in genre_result["results"]["bindings"]]
            genre_set = set(genre_list)
            genre_set = [str(genre) for genre in genre_set if genre.endswith('film')]
            genre_set = [genre.replace(' film', '').capitalize() for genre in genre_set]




        if len(genre_set) > 3:
            genre_set = genre_set[:3]
        print(f'genre_set: {genre_set}')

        df['genres'] = df['genres'].apply(lambda x: x.split('|'))
        df['match_count'] = df['genres'].apply(lambda x: len(set(genre_set).intersection(set(x))))
        similar_movies = df[df['match_count'] > 0]
        similar_movies = similar_movies.sort_values(by='match_count', ascending=False)
        top_movies = similar_movies.head(10)
        #top_movie_titles = top_movies['title'].apply(lambda x: x.rsplit(' (', 1)[0])
        top_movie_titles = top_movies['title']

        return top_movie_titles.tolist()

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
            # if lens > 1:
            #     last_item = items.pop()
            #     result = ', '.join(items) + ' and ' + last_item
            # elif items:
            #     result = items[0]
            # else:
            #     result = None
        return items


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


        return items





if __name__ == "__main__":
    test = Recommend()
    # entities = ['The Lion King', 'Pocahontas', ' The Beauty and the Beast']
    # entities = ['Nightmare on Elm Street', 'Friday the 13th', 'Halloween']
    # result = test.get_recommendation(entities)
    # print(result)
    # entity = ['Wes Anderson']
    # for e in entity:
    #     print(test.get_recommendation_humans(e))
    # human = 'Charlie Chaplin'
    # movie = 'The Great Dictator'
    # print(test.get_recommendation_human_movie(human, movie))
    entities = ['Snakes on a Train', 'Kung Fu Panda']
    for e in entities:
        print(test.get_recommendation_single_movie(e))