import pandas as pd

starters_by_position = {
    "QB": 1,
    "RB": 2.5,
    "WR": 2.5,
    "TE": 1,
    "DST": 1,
    "K": 1
}

league_teams = 12
draft_budget = 200
# target_points = 1500 #Used for points based calculation that doesn't account for replacement level
#target_above_repl = 500 #Used for value based with replacement level. Testing this
#These are strategy dependent and could ultimately be encoded in strategy profiles
risk_factor = 0.1
pos_bonus = 1.1
pos_disc = 0.91

player_df = pd.read_csv("data/fantasypros/fp_projections.csv")
player_df.rename(columns = {'Unnamed: 0':'Pos Rank'}, inplace = True)
player_df["Pos Rank"] = player_df["Pos Rank"] + 1

proj_points_df = player_df[["Player", "Pos Rank", "Team", "Pos", "FantasyPoints"]]
proj_points_df['Pos Starters'] = proj_points_df["Pos"].map(starters_by_position)*league_teams
proj_points_df['Replacement'] = proj_points_df["Pos"].map(starters_by_position)*league_teams*2

points_by_pos_df = proj_points_df.groupby("Pos").FantasyPoints.agg(['count','mean','median','std'])
replacement_players_df = proj_points_df.loc[(proj_points_df["Pos Rank"]> proj_points_df['Pos Starters']) & (proj_points_df["Pos Rank"] <= proj_points_df['Replacement'])]
starters_df = proj_points_df.loc[(proj_points_df["Pos Rank"] <= proj_points_df['Pos Starters'])]
repl_points_by_pos_df = replacement_players_df.groupby("Pos").FantasyPoints.agg(['count','mean','median','std'])
starters_points_by_pos_df = starters_df.groupby("Pos").FantasyPoints.agg(['count','mean','median','std'])

exp_repl_team_val = sum(repl_points_by_pos_df.index.map(starters_by_position) * repl_points_by_pos_df['median'])
exp_starters_team_val = sum(starters_points_by_pos_df.index.map(starters_by_position) * starters_points_by_pos_df['mean'])
win_factor = 130
target_points = exp_starters_team_val + win_factor
target_above_repl = target_points - exp_repl_team_val

print("Expected Replacement Team Value:", exp_repl_team_val)
print("Expected Average Team Value:", exp_starters_team_val)
print("Expected Contention Value:", target_points)
print("Points Above Replacement Needed:", target_above_repl)

proj_points_df = pd.merge(proj_points_df,repl_points_by_pos_df['median'], left_on='Pos', right_on='Pos')
proj_points_df.rename(columns = {'median':'Repl Med'}, inplace = True)
proj_points_df = pd.merge(proj_points_df,starters_points_by_pos_df['mean'], left_on='Pos', right_on='Pos')
proj_points_df.rename(columns = {'mean':'Star Mean'}, inplace = True)
proj_points_df["PAR"] = proj_points_df["FantasyPoints"] - proj_points_df['Repl Med']
proj_points_df["PAS"] = proj_points_df["FantasyPoints"] - proj_points_df['Star Mean']
proj_points_df = proj_points_df.sort_values('PAR', ascending=False)

proj_points_df["1st Pick Value"] = round(proj_points_df["PAR"] * (draft_budget / target_above_repl) * (1-risk_factor) * (pos_bonus), 2)
proj_points_df["Starter Value"] = round(proj_points_df["PAR"] * (draft_budget / target_above_repl) * (1-risk_factor) * (pos_disc), 2)
proj_points_df["Inc 1st Pick"] = round(proj_points_df["1st Pick Value"] - proj_points_df["Starter Value"],2)
draft_values_df = proj_points_df[['Player','Team','Pos','1st Pick Value','Starter Value', 'Inc 1st Pick','PAR','PAS','FantasyPoints']]


draft_values_df.to_csv('output/Draft_Values.csv')


