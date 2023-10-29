


class Answer:

    def __init__(self):
        pass

    def fuctualAnswer(self,relation,movie):
        try:
            # rel = get_close_matches(relation,self.lbl2prop.keys())[0]
            rel_code = self.lbl2prop[relation]
            q = f"""
    PREFIX ddis: <http://ddis.ch/atai/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX schema: <http://schema.org/>

    SELECT ?answerLbl
    WHERE {{
            ?movie rdfs:label "{movie}"@en;
                    wdt:{rel_code} ?answer.
            ?answer rdfs:label ?answerLbl.
    }}
    """
            q_result = self.graph.query(q)
            q_result = DataFrame(q_result,columns=q_result.vars)
            if q_result.shape[0]==0:
                print(f"The {relation} of {movie} isn't in the KG")
                return None
            else:
                return self.__wOfAnswerTemplate(q_result,relation,movie)
        except Exception as e:
            print(e)
            return None

