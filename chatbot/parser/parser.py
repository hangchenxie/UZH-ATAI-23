import re
from ..entity.entity_recognizer import EntityRecognizer
from ..relation.relation_recognizer import RelationRecognizer

class MessageParser:
    def __init__(self):
        self.entity_recognizer = EntityRecognizer()
        self.relation_recognizer = RelationRecognizer()

    def parse_entity_relation(self, message_text):
        t = message_text
        ent_dict = self.entity_recognizer.get_entities(t)
        for ent in ent_dict.keys():
            t_rem = t.replace(ent, "")
        # TODO: use a relation extractor class
        for old, new in [(r"Who|What|When|How many|Tell me|is|are|\bthe\b|\bof\b|\?","")]:
            t_rem = re.sub(old, new, t_rem, flags=re.IGNORECASE)
            t_rem = t_rem.strip()
        rel_dict = {t_rem: self.relation_recognizer.get_relation(t_rem)}
        return ent_dict, rel_dict