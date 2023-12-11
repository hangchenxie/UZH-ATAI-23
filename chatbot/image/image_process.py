from pathlib import Path
import re
import warnings
import json
# from chatbot import cache
from chatbot.knowledge_graph.knowledge_graph import KnowledgeGraph


KG = KnowledgeGraph()

images_path = Path(__file__).parents[1].joinpath("data", "images.json")

with open(images_path, 'rb') as file:
    images = json.load(file)

# "P345": "IMDb ID",
# "P577": "publication date"
# "P161": "cast member",
# "P31": "instance of",
# "P136": "genre",
# "P279": "subclass of",
class ImageProcess:


    def __init__(self):
        self.graph = KG
        self.images = images

    def get_image_human(self, entities):

        type_preferences = ['poster', 'still_frame']
        ids = []

        for entity in entities:
            f = '''
            PREFIX ddis: <http://ddis.ch/atai/>
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX schema: <http://schema.org/>
            SELECT ?imdb_id WHERE {{
                wd:{} wdt:P345 ?imdb_id .
            }}
            '''.format(entity)
            print(f)
            imdb_id = [str(s.imdb_id) for s in self.graph.query(f)]

            if imdb_id:
                ids.append(imdb_id[0])

        best_image = None
        best_type = None

        for entry in self.images:
            if all(i in entry['cast'] for i in ids):
                if best_image is None or entry['type'] in type_preferences:
                    best_image = entry['img']
                    best_type = entry['type']
                if entry['type'] in type_preferences:
                    break
        return best_image, best_type


    def get_image_movie(self, movie):
        type_preferences = ['poster', 'still_frame']

        # Query the IMDb ID of the movie
        f = '''
        PREFIX ddis: <http://ddis.ch/atai/>
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX schema: <http://schema.org/>
        SELECT ?imdb_id WHERE {{
            wd:{} wdt:P345 ?imdb_id .
        }}
        '''.format(movie)
        imdb_id = [str(s.imdb_id) for s in self.graph.query(f)]

        best_image = None
        best_type = None

        # If the movie has an IMDb ID, find the best image for it
        if imdb_id:
            for entry in self.images:
                if imdb_id[0] in entry['movie']:
                    if best_image is None or entry['type'] in type_preferences:
                        best_image = entry['img']
                        best_type = entry['type']
                    if entry['type'] in type_preferences:
                        break

        return best_image, best_type



if __name__ == "__main__":
    image_process = ImageProcess()
    # entity = ['Q161916', ]  # list of entities
    # movie_id: "tt0286516", img: "1959/rm486709248.jpg" 
    # "cast" : ["nm1197165", "nm1196061", "nm0000420"] # Francesco Casisa (Q3749748), Filippo Pucillo (Q3071912), Valeria Golino (Q230710)
    entity = ['Q3749748', 'Q3071912', 'Q230710']  
    url, types = image_process.get_image_human(entity)
    # entity = 'Q3933460' # movie_id: "tt0286516", Respiro (Q3933460)
    url, types = image_process.get_image_movie(entity)
    print(url)
    print(types)


