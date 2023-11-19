import pandas as pd
from statsmodels.stats.inter_rater import fleiss_kappa, aggregate_raters
from pathlib import Path

# Check if filtered data exists
filtered_data_path = Path(__file__).parents[1].joinpath("data", "filter_crowd.csv")
if filtered_data_path.exists():
    print("Filtered data already exists, skipping filtering process")
    filtered_data = pd.read_csv(filtered_data_path)
else:
    # If filtered data doesn't exist, filter the raw data
    raw_data_path = Path(__file__).parents[1].joinpath("data", "crowd_data_Corrected.tsv")
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        raw_data = pd.read_csv(f, sep='\t')

    filtered_data = raw_data[(raw_data['WorkTimeInSeconds'] > 30) & (raw_data['LifetimeApprovalRate'] > '40%')]

    kappas = filtered_data.groupby('HITTypeId').apply(lambda x: fleiss_kappa(aggregate_raters(pd.crosstab(x['WorkerId'], x['AnswerLabel']))[0]))

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
        self.crowd_data = filtered_data

    def search_crowdsource(self, s, p):
        df = self.crowd_data
        crowd_answers = df.loc[(df['Subject'] == s) & (df["Predicate"] == p)]
        if crowd_answers.empty:
            return None
        else:
            o = crowd_answers['Object'].iloc[0]
            kappa = crowd_answers['Kappa'].iloc[0]
            support_votes = crowd_answers['SupportVotes'].iloc[0]
            reject_votes = crowd_answers['RejectVotes'].iloc[0]
            return o,support_votes, reject_votes, round(kappa, 3)


    def merge_crowdsource(self, s, p):
        pass

if __name__ == '__main__':
    crowd = CrowdSource()
    print(crowd.search_crowdsource('wd:Q11621', 'wdt:P19'))