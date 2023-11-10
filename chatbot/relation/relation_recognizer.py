from pathlib import Path
import re
from rapidfuzz import fuzz
import warnings
import json
from chatbot import cache

rel_lbl_path = Path(__file__).parents[1].joinpath("data", "my_property.json")

with open(rel_lbl_path, 'rb') as file:
    property = json.load(file)
lbl2relation = {item: values[0] for values in property.values() for item in values}


class RelationRecognizer:
    def __init__(self):
        self.lbl2relation = lbl2relation

    def match_rel_label(self, text):
        if text in self.lbl2relation: return self.lbl2relation[text], 100.
        else:
            matched_rel_lbl, r = None, 0
            ratio_list = {}
            for e in self.lbl2relation:
                ratio = fuzz.ratio(e, text.lower())
                ratio_list[e] = float(ratio)
            # print("ratio_list:", ratio_list)
            desired_ratio = max(ratio_list.values())
            # Get the key (keyword) corresponding to the maximum ratio
            desired_key = [key for key, value in ratio_list.items() if value == desired_ratio][0]
            matched_rel_lbl, r = self.lbl2relation[desired_key], desired_ratio
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
        'Show me a picture of Halle Berry.',
        'What does Julia Roberts look like?',
        'Let me know what Sandra Bullock looks like.'
    ]
    for question in questions:
        print(question)
        print(f'relation:{rr.get_relation(question)}')
