import os
import dill
import matplotlib.pyplot as plt
from Othello_self_play_main import *
import argparse

# parse inputs
parser = argparse.ArgumentParser(description='Plot the game play')
parser.add_argument('--input_path', help="MCTS output binary file (.dill)", type=str, required=True)
parser.add_argument('--out_dir',  help="output directory", type=str, required=True)
pars = vars(parser.parse_args())

# read and parse input
infilename = pars['input_path']
outdir = pars['out_dir']
os.makedirs(outdir)

# read and parse data
data = dill.load(open(infilename, 'rb'))

index = -2
for i in range(len(data['data_p'])):
	index += 2
	_board, _player = data['data_p'][i]['states'][-1]
	Othello.OthelloGame.print_board(_board, outfilename = outdir + os.sep + str(index).zfill(2)+'.png')
# end for

index = -1
for i in range(len(data['data_q'])):
	index += 2
	_board, _player = data['data_q'][i]['states'][-1]
	Othello.OthelloGame.print_board(_board, outfilename = outdir + os.sep + str(index).zfill(2)+'.png')
# end for

