from rdflib import Namespace
class Query:
    def __init__(self, graph):
        self.WD = Namespace('http://www.wikidata.org/entity/')
        self.WDT = Namespace('http://www.wikidata.org/prop/direct/')
        self.SCHEMA = Namespace('http://schema.org/')
        self.DDIS = Namespace('http://ddis.ch/atai/')
        self.graph = graph



    def execute(self):
        pass

    def get_result(self):


    def get_result_as_df(self):
