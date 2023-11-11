from pathlib import Path
import re
import warnings
import json
from chatbot import cache
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

    def get_image(self, entity):
        entity = ''.join(entity)
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
        self.id = [str(s.imdb_id) for s in self.graph.query(f)]
        print("id:", self.id)
        best_image_info = None
        best_type = None
        type_preferences = ['poster']
        for entry in self.images:
            if self.id[0] in entry['cast'] and len(entry['cast'])==1:
                if best_image_info is None or entry['type'] in type_preferences and entry['type'] != 'still_frame':
                    best_image_info = entry['img']
                    best_type = entry['type']
        return best_image_info, best_type

if __name__ == "__main__":
    image_process = ImageProcess()
    entity = "Q2680"
    url, types = image_process.get_image(entity)
    print(url)
    print(types)


