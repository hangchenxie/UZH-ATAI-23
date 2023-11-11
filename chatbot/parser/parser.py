import re
from chatbot.entity.entity_recognizer import EntityRecognizer
from chatbot.relation.relation_recognizer import RelationRecognizer
from chatbot import cache

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
        for old, new in [(r"Who|What|When|How many|can you|Tell me|given that|does|do|did|let|us|me|is|are|I like|movie like\bthe\b|\bof\b|\?","")]:
            t_rem = re.sub(old, new, t_rem, flags=re.IGNORECASE)
            t_rem = t_rem.strip().replace('"', '')
            print("parsed_question:", t_rem)
        rel_dict = {t_rem: self.relation_recognizer.get_relation(t_rem)}
        return ent_dict, rel_dict

if __name__ == "__main__":
    ms = MessageParser()
    questions = [
        # 'When was "The Gofather" released?',
        # "Who is the director of Star Wars: Epode VI - Return of the Jedi?",
        # "Who is the director of Good Will Huntin? ",
        # 'Who directed The Bridge on the River Kwai?',
        # "Who is the screenwriter of The Masked Gang: Cyprus?",
        # "What is the MPAA film rating of Weathering with You?",
        # "What is the genre of Good Neighbors?",
        # "What is the box office of The Princess and the Frog? ",
        # 'Can you tell me the publication date of Tom Meets Zizou? ',
        # 'Who is the executive producer of X-Men: First Class? '
        # 'Show me a picture of Halle Berry.',
        # 'What does Julia Roberts look like?',
        # 'Let me know what Sandra Bullock looks like.'
        "Given that I like The Lion King, Pocahontas, and The Beauty and the Beast, can you recommend some movies? ",
        "Recommend movies like Nightmare on Elm Street, Friday the 13th, and Halloween. "
    ]
    for question in questions:
        answer = ms.parse_entity_relation(question)
        print(question)
        ent_dict, rel_dict = answer
        print(f'ent_dict:{ent_dict}')
        print(f'rel_dict:{rel_dict}')