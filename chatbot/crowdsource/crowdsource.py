import pandas as pd
from statsmodels.stats.inter_rater import fleiss_kappa, aggregate_raters
from pathlib import Path
from chatbot.knowledge_graph.knowledge_graph import graph
import rdflib
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, OWL, XSD

WD = rdflib.Namespace('http://www.wikidata.org/entity/')
WDT = rdflib.Namespace('http://www.wikidata.org/prop/direct/')
DDIS = rdflib.Namespace('http://ddis.ch/atai/')
RDFS = rdflib.namespace.RDFS
SCHEMA = rdflib.Namespace('http://schema.org/')

raw_data_path = Path(__file__).parents[1].joinpath("data", "crowd_data_Corrected.tsv")
with open(raw_data_path, 'r', encoding='utf-8') as f:
    raw_data = pd.read_csv(f, sep='\t')

filtered_data = raw_data[(raw_data['WorkTimeInSeconds'] > 30) & (raw_data['LifetimeApprovalRate'] > '40%')]

kappas = filtered_data.groupby('HITTypeId').apply(
    lambda x: fleiss_kappa(pd.crosstab(x['HITId'], x['AnswerLabel']))
)
filtered_data = filtered_data.assign(
    kappa=filtered_data['HITTypeId'].apply(lambda x: kappas[x])
)

data = []
for hitId, group in filtered_data.groupby('HITId'):
    s = group['Input1ID'].iloc[0]
    p = group['Input2ID'].iloc[0]
    o = group['Input3ID'].iloc[0]
    votes = group['AnswerLabel'].value_counts()
    support_votes = votes.get('CORRECT', 0)
    reject_votes = votes.get('INCORRECT', 0)
    fixpos = group['FixPosition'].value_counts().idxmax() if len(group['FixPosition'].value_counts()) == 1 else "NA"
    fixval = group['FixValue'].value_counts().idxmax() if len(group['FixValue'].value_counts()) == 1 else "NA"
    # kappa = kappas.get(hitId, None)
    kappa = group['kappa'].iloc[0]
    data.append([hitId, s, p, o, support_votes, reject_votes, fixpos, fixval, kappa])

# filtered_data = pd.DataFrame(data, columns=['HITId', 'Subject', 'Predicate', 'Object', 'SupportVotes', 'RejectVotes',
#                                             'FixPosition', 'FixValue', 'Kappa'])

# crowd_answers = filtered_data.loc[
#     (~filtered_data["FixPosition"].isna()) &
#     (~filtered_data["FixValue"].isna())
#     ]


def merge_crowdsource_to_graph(crowd_answers, graph):
    for index, row in crowd_answers.iterrows():
        subject = WD[row['Subject'].replace('wd:', '')]
        predicate = WDT[row['Predicate'].replace('wdt:', '')] if row['Predicate'].startswith(
            'wdt:') else DDIS.indirectSubclassOf
        object = WD[row['Object'].replace('wd:', '')] if row['Object'].startswith('wd:') else Literal(row['Object'])
        graph.remove(subject, predicate, object)
        if row['FixPosition'] == 'Subject':
            graph.add(WD[row['FixValue']], predicate, object)
        elif row['FixPosition'] == 'Object':
            object_fix = WD[row['FixValue'].replace('wd:', '')] if row['FixValue'].startswith('wd:') else Literal(
                row['FixValue'])
            graph.add(subject, predicate, object_fix)
        else:
            graph.add(subject, WDT[row['FixValue']], object)
    return graph


# graph = merge_crowdsource_to_graph(crowd_answers, graph)

processed_data_path = Path(__file__).parents[1].joinpath("data", "filtered.csv")
filtered_data = pd.read_csv(processed_data_path)



class CrowdSource:

    def __init__(self):
        # self.crowd_data = filtered_data
        #self.crowd_answers = crowd_answers
        self.crowd_answers = filtered_data

    def search_crowdsource(self, s, p):
        # df = self.crowd_data
        # crowd_answers = df.loc[(df['Subject'] == s) & (df["Predicate"] == p)]
        crowd_answer = self.crowd_answers.loc[
            (self.crowd_answers['Subject'] == s) &
            (self.crowd_answers["Predicate"] == p)
            ]
        if crowd_answer.empty:
            return None
        else:
            crowd_fix = {
                "subject": s,
                "predicate": p,
                "object": crowd_answer['Object'].iloc[0],
                "support_votes": crowd_answer['SupportVotes'].iloc[0],
                "reject_votes": crowd_answer['RejectVotes'].iloc[0],
                "fix_position": crowd_answer['FixPosition'].iloc[0],
                "fix_value": crowd_answer['FixValue'].iloc[0],
                "kappa": round(crowd_answer['Kappa'].iloc[0], 3)
            }
            # return o,support_votes, reject_votes, round(kappa, 3)
            return crowd_fix


if __name__ == '__main__':
    #
    # crowd = CrowdSource()
    # print(crowd.search_crowdsource('Q11621', 'P2142'))
    # crowd.crowd_answers.to_csv('crowd_answers.csv', index=False)
    # import pandas as pd
    # from chatbot.embedding.embedding_calculator import EmbeddingCalculator
    #
    # emb_calculator = EmbeddingCalculator()
    #
    df = pd.read_csv('crowd_answers.csv')
    #
    # # Iterate over each row in the DataFrame
    # for i, row in df.iterrows():
    #     # Check the FixPosition value
    #     if row['FixPosition'] == 'Subject':
    #         # Replace the Subject value with the FixValue
    #         df.loc[i, 'Subject'] = row['FixValue']
    #     elif row['FixPosition'] == 'Predicate':
    #         # Replace the Predicate value with the FixValue
    #         df.loc[i, 'Predicate'] = row['FixValue']
    #     elif row['FixPosition'] == 'Object':
    #         # Replace the Object value with the FixValue
    #         df.loc[i, 'Object'] = row['FixValue']
    # #
    #
    # # Check if 'wd:' or 'wdt:' exists in 'Subject', 'Predicate', and 'Object' columns before removing
    df['Subject'] = df['Subject'].apply(lambda x: x.replace('wd:', '') if x.startswith('wd:') else x)
    df['Predicate'] = df['Predicate'].apply(lambda x: x.replace('wdt:', '') if x.startswith('wdt:') else x)
    df['Object'] = df['Object'].apply(lambda x: str(x).replace('wd:', '') if str(x).startswith('wd:') else x)

    df.to_csv('filtered.csv', index=False)
