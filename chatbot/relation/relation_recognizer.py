from pathlib import Path
import re
from rapidfuzz import fuzz
import warnings
import json

rel_lbl_path = Path(__file__).parents[1].joinpath("data", "rel_lbl.json")

with open(rel_lbl_path, 'rb') as file:
    rel_lbl = json.load(file)


class RelationRecognizer:
    def __init__(self):
        pass

    def match_rel_label(self, text):
        if text in rel_lbl: return text, 1.
        else:
            matched_rel_lbl, r = None, 0
            for e in rel_lbl:
                ratio = fuzz.ratio(e, text.lower())
                if ratio > r: matched_rel_lbl, r = e, ratio
            return matched_rel_lbl, r
        
    def get_relation(self, text):
        relation, score = self.match_rel_label(text)
        return {"relation": relation, "score": score}