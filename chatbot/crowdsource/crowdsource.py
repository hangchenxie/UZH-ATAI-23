import pandas as pd
from statsmodels.stats.inter_rater import fleiss_kappa, aggregate_raters
from pathlib import Path

# Check if filtered data exists
# filtered_data_path = Path(__file__).parents[1].joinpath("data", "filter_crowd.csv")
# if filtered_data_path.exists():
#     print("Filtered data already exists, skipping filtering process")
#     filtered_data = pd.read_csv(filtered_data_path)
# else:
    # If filtered data doesn't exist, filter the raw data
raw_data_path = Path(__file__).parents[1].joinpath("data", "crowd_data_Corrected.tsv")
with open(raw_data_path, 'r', encoding='utf-8') as f:
    raw_data = pd.read_csv(f, sep='\t')

filtered_data = raw_data[(raw_data['WorkTimeInSeconds'] > 30) & (raw_data['LifetimeApprovalRate'] > '40%')]

# kappas = filtered_data.groupby('HITTypeId').apply(lambda x: fleiss_kappa(aggregate_raters(pd.crosstab(x['WorkerId'], x['AnswerLabel']))[0]))
kappas = filtered_data.groupby('HITTypeId').apply(
    lambda x: fleiss_kappa(pd.crosstab(x['HITId'], x['AnswerLabel']))
)
filtered_data = filtered_data.assign(
    kappa = filtered_data['HITTypeId'].apply(lambda x: kappas[x])
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

filtered_data = pd.DataFrame(data, columns=['HITId', 'Subject', 'Predicate', 'Object', 'SupportVotes', 'RejectVotes', 'FixPosition', 'FixValue','Kappa'])
# print(filtered_data.head())
# filtered_data.to_csv('filter_crowd.csv', index=False)
crowd_answers = filtered_data.loc[
    (~filtered_data["FixPosition"].isna()) &
    (~filtered_data["FixValue"].isna())
]
# crowd_answers.to_csv('crowd_answers.csv', index=False)

class CrowdSource:

    def __init__(self):
        # self.crowd_data = filtered_data
        self.crowd_answers = crowd_answers

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


    def merge_crowdsource(self, s, p):
        pass

if __name__ == '__main__':
    crowd = CrowdSource()
    # print(crowd.search_crowdsource('wd:Q11621', 'wdt:P2142'))
    print(crowd.search_crowdsource('wd:Q16911843', 'wdt:P577')) # 2014-02-18