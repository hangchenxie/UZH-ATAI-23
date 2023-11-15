import pandas as pd
from sklearn.metrics import cohen_kappa_score
from pathlib import Path

path = Path(__file__).parents[1].joinpath("data", "crowd_data_Corrected.tsv")
with open(path, 'r', encoding='utf-8') as f:
    crowd_data = pd.read_csv(f, sep='\t')

filtered_data = crowd_data[(crowd_data['WorkTimeInSeconds'] > 30) & (crowd_data['LifetimeApprovalRate'] > '70%')]

majority_vote = filtered_data.groupby('HITId')['AnswerLabel'].agg(lambda x: x.value_counts().index[0])

kappas = filtered_data.groupby('HITTypeId').apply(lambda x: cohen_kappa_score(x['WorkerId'], x['AnswerLabel']))

user_stats = crowd_data.groupby('WorkerId')['AssignmentStatus'].value_counts()

data = []
for hitId, group in filtered_data.groupby('HITId'):
    s = group['Input1ID'].iloc[0]
    p = group['Input2ID'].iloc[0]
    o = group['Input3ID'].iloc[0]
    votes = group['AnswerLabel'].value_counts()
    support_votes = votes.get('CORRECT', 0)
    reject_votes = votes.get('INCORRECT', 0)
    kappa = kappas.get(hitId, None)
    data.append([hitId, s, p, o, support_votes, reject_votes, kappa])

result_df = pd.DataFrame(data, columns=['HITId', 'Subject', 'Predicate', 'Object', 'SupportVotes', 'RejectVotes', 'Kappa'])


result_df.to_csv('filter_crowd.csv', index=False)

class CrowdSource:

    def __init__(self):
        self.crowd_data = crowd_data


    # def merge_data(self, graph):
    #     WD = Namespace('http://www.wikidata.org/entity/')
    #     WDT = Namespace('http://www.wikidata.org/prop/direct/')
    #     DDIS = Namespace('http://ddis.ch/atai/')
    #     RDFS = rdflib.namespace.RDFS
    #     grouped = self.crowd_data.groupby('HITId')
    #     for hitId, group in grouped:
    #         hit = group.iloc[0]
    #         votes = group['AnswerLabel'].value_counts().to_frame('count').reset_index()
    #         s = URIRef(WD[re.sub("wd:", "", hit['Input1ID'])])
    #         p_value = hit['Input2ID']
    #         p = URIRef(DDIS[re.sub("ddis:", "", p_value)]) if re.search("ddis:", p_value) else URIRef(WDT[re.sub("wdt:", "", p_value)])
    #         o_value = hit['Input3ID']
    #         o = URIRef(WD[re.sub("wd:", "", o_value)]) if re.search("wd:", o_value) else Literal(o_value, datatype=XSD.date) if re.search(r'(\d+-\d+-\d+)', o_value) else Literal(o_value)
    #         if not (s, p, o) in graph:
    #             graph.add((s, p, o))

    def search_crowdsource(self, s, p, o):
        df = self.crowd_data
        crowd_answers = df.loc[(df['Subject'] == s) & (df["Predicate"] == p) & (df["Object"] == o)]
        if crowd_answers.empty:
            return None
        else:
            kappa = crowd_answers['Kappa'].iloc[0]
            support_votes = crowd_answers['SupportVotes'].iloc[0]
            reject_votes = crowd_answers['RejectVotes'].iloc[0]
            return support_votes, reject_votes, round(kappa, 2)
