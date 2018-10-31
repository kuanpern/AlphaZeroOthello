import pandas as pd
import numpy as np
import dill
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from Othello_self_play_main import *


import yaml
import argparse

# parse inputs
parser = argparse.ArgumentParser(description='Plot confidence level during the game')
parser.add_argument('--input_path', help="MCTS output binary file (.dill)", type=str, required=True)
parser.add_argument('--out_fig',  help="output figure (.png)", type=str, required=True)
pars = vars(parser.parse_args())

# read and parse input
infilename = pars['input_path']
outfigname = pars['out_fig']

# parse data
data = dill.load(open(infilename, 'rb'))
df = pd.DataFrame(data['trace'])
df['index'] = np.arange(len(df)) + 1


# start plotting
sel_df = df[df['player'] ==  1]
x = sel_df[     'index'].values
y = sel_df['confidence'].values
p1 = plt.bar(x, y, width=1, color='grey')

sel_df = df[df['player'] == -1]
x = sel_df[     'index'].values
y = sel_df['confidence'].values
p2 = plt.bar(x, y, width=1, color='paleturquoise')

# horizont al line
plt.axhline(0.5, ls='--', color='pink', lw=2)

# labelling
plt.xlabel('Turns')
plt.ylabel('Confidence of winnig')
plt.legend([p1, p2], ['Black', 'White'])

# save output
plt.gcf().set_size_inches(9, 4)
plt.savefig(outfigname)
