import re
import json
from difflib import get_close_matches
import os
from pathlib import Path
from chatbot.entity.entity_recognizer import EntityRecognizer
from chatbot.parser.parser import MessageParser
from chatbot import cache
from rapidfuzz import fuzz

class Relation:

    def __init__(self, question):
        self.question = question
        self.parser = MessageParser()
        self.patterns =[
            "(Who|What|who|what|When) (is|are|was|were) the( .*?) of ([A-Z].*)",
            "(who|what)(.)the ([a-z].*[a-z]) of ([A-Z].*) (is|are)",
            "(who|Who)(.)([a-z]*) ([A-Z].*)",
            "(?:.*)(?:Tell|tell)(?: me)?(?: about)?(.*)(?:of|in|from|for)(.*)"
        ]
        self.property_file = os.path.join(Path(__file__).parents[1],'data', 'my_property.json')
        with open(self.property_file, 'r', encoding="utf-8") as f:
            self.property = json.load(f)
        # self.lbl2relation = {lbl: prop for prop, lbl in self.property.items()}
        self.lbl2relation = {item: values[0] for values in self.property.values() for item in values}
        print("lbl2relation:", self.lbl2relation)
        self.entity_dict, self.relation_dict = self.parser.parse_entity_relation(self.question)
        self.entity = ''.join([self.entity_dict[k]["matched_lbl"] for k in self.entity_dict.keys()])
        print("entity:", self.entity)
        self.relation = None



    def get_relation(self):
        if self.entity is not None:
           self.question = re.sub(self.entity, "", self.question, flags=re.IGNORECASE)
        for old, new in [(r"Who|What|When|How many|Tell me|is|are|\bthe\b|\bof\b|\?","")]:
            self.question = re.sub(old, new, self.question, flags=re.IGNORECASE)
        self.question = self.question.strip().replace('"', '')
        print("parsed_question:", self.question)
        if self.question in self.lbl2relation:
            return self.lbl2relation[self.question], 100.
        else:
            matched_rel_lbl, r = None, 0
            ratio_list = {}
            for e in self.lbl2relation:
                ratio = fuzz.ratio(e, self.question.lower())
                ratio_list[e] = float(ratio)
            desired_ratio = max(ratio_list.values())
            # Get the key (keyword) corresponding to the maximum ratio
            desired_key = [key for key, value in ratio_list.items() if value == desired_ratio][0]
            matched_rel_lbl, r = self.lbl2relation[desired_key], desired_ratio
            return matched_rel_lbl, r





    # matched_rel_lbl, r = None, 0
    # for e in self.lbl2relation:
    #     ratio = fuzz.ratio(e, self.question.lower())
    #     if ratio > 0: matched_rel_lbl, r = self.lbl2relation[e], ratio
    # return matched_rel_lbl, r



        # for pattern in self.patterns:
        #     match = re.match(pattern, self.question, re.IGNORECASE)
        #     if match is None:
        #         continue
        #     else:
        #         for group in match.groups():
        #             if group is None:
        #                 continue
        #             else:
        #                 relation = group.strip()
        #                 break
        #         print("original relation:", relation)
        #         matches = get_close_matches(relation, self.lbl2relation.keys())
        #         if matches:
        #             self.relation = matches[0]
        #             print("matched relation:", self.relation)
        #             return self.relation
        #         else:
        #             return None





if __name__ == "__main__":
    questions = [
        'When was "The Godfather" released?',
        "Who is the director of Star Wars: Episode VI - Return of the Jedi?",
        "Who is the director of Good Will Hunting? ",
        'Who directed The Bridge on the River Kwai?',
        "Who is the screenwriter of The Masked Gang: Cyprus?",
        "What is the MPAA film rating of Weathering with You?",
        "What is the genre of Good Neighbors?",
        "What is the box office of The Princess and the Frog? ",
        'Can you tell me the publication date of Tom Meets Zizou? ',
        'Who is the executive producer of X-Men: First Class? '
    ]
    for question in questions:
        answer = Relation(question)
        print(question)
        print(f'relation:{answer.get_relation()}')



