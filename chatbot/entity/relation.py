import re
import json
from difflib import get_close_matches
import os
from pathlib import Path
from chatbot.entity.entity_recognizer import EntityRecognizer

class Relation:

    def __init__(self, question):
        self.question = question
        self.patterns =[
            "(Who|What|who|what) (is|are|was|were) the( .*?) of ([A-Z].*)",
            "(who|what)(.)the ([a-z].*[a-z]) of ([A-Z].*) (is|are)",
            "(who|Who)(.)([a-z]*) ([A-Z].*)",
            "(?:.*)(?:Tell|tell)(?: me)?(?: about)?(.*)(?:of|in|from|for)(.*)"
        ]
        self.property_file = os.path.join(Path(__file__).parents[2],'data', 'property.json')
        with open(self.property_file, 'r', encoding="utf-8") as f:
            self.property = json.load(f)
        self.lbl2relation = {lbl: prop for prop, lbl in self.property.items()}
        ER = EntityRecognizer(entities_in_graph=[])
        self.entity = ER.get_entities(self.question)[0][0][0]

    def get_relation(self):
        for pattern in self.patterns:
            match = re.match(pattern, self.question)
            if match is None:
                continue
            else:
                for group in match.groups():
                    if group is None or group == self.entity:
                        continue
                    else:
                        relation = group.strip()
                        break
                print("original relation:", relation)
                self.relation = get_close_matches(relation, self.lbl2relation.keys())[0]
                # print("matched relation:", self.relation)
                return self.relation
        return None




if __name__ == "__main__":
    questions = ["Who is the director of Good Will Hunting? ",
                 'Who directed The Bridge on the River Kwai?',
                 "Who is the director of Star Wars: Episode VI - Return of the Jedi?",
                 "Who is the screenwriter of The Masked Gang: Cyprus?",
                 "What is the MPAA film rating of Weathering with You?",
                 "What is the genre of Good Neighbors?",
                 "What is the box office of The Princess and the Frog? ",
                 'Can you tell me the publication date of Tom Meets Zizou? ',
                 'Who is the executive producer of X-Men: First Class? ']
    for question in questions:
        answer = Relation(question)
        print(question)
        print(f'relation:{answer.get_relation()}')



