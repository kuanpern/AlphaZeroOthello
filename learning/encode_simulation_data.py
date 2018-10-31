import numpy as np
import sys
import dill
import uuid
import argparse
from Othello_self_play_main import *

###################################################
################## INPUT ENCODING #################
###################################################
# using AlphaGo encoding system here - not optimal for Othello, but anyways ..
# if mine then 1, else then 0
def encode_input_state(unit_in, min_length=3):
	
	# fix min_length issue (i.e. first n moves)
	missed_n = min_length - len(unit_in)
	if missed_n == 0:
		unit = copy.deepcopy(unit_in)
	else:
		# duplicate the first and prepend
		unit = [unit_in[0]] * missed_n + unit_in
	# end if
	
	stack = []
	for item in unit:
		state, player = item

		# black
		p = np.zeros_like(state)
		p[np.where(state ==  1)] = 1

		# white
		q = np.zeros_like(state)
		q[np.where(state == -1)] = 1

		stack.append(p)
		stack.append(q)
	# end for

	# 1 if black, 0 if white
	cur_player = unit[-1][1]
	if cur_player == 1: 
		r = np.ones_like(state)
	else:
		r = np.zeros_like(state)
	# end if
	stack.append(r)
	stack = np.array(stack)
	
	return stack
# end def
###################################################
###################################################



###################################################
################# TARGET ENCODING #################
###################################################
def encode_output_vector(probs, winner, init_state = np.zeros([8, 8]), rounding=3, pseudocount=0.05):
	B = copy.deepcopy(init_state)

	# pseudocount
	v = sum([item.data['visits'] for item in probs])
	d = v*pseudocount / len(probs)

	for item in probs:
		_move = item.data['move']
		success = item.data['success']
		visits  = item.data['visits']

		B[_move] = (d + success) / (d + visits)
	# end for

	tgt_probs = B.flatten() / B.sum()
	tgt_probs = tgt_probs.round(rounding) # optional
		
	temp = tgt_probs.tolist()
	temp.append(winner)
	tgt_probs = np.array(temp)
	return tgt_probs
# end def
###################################################
###################################################


###################################################
############### PLOTTING SUBROUTINE ###############
###################################################
def plot_instance(_state, _probs, outfilename=None):
	plt.clf()
	m = plt.imshow(_probs, cmap=plt.cm.YlOrRd)

	x, y = np.where(_state == -1)
	plt.scatter(y, x, c='palegreen', s=200, edgecolors='black')

	x, y = np.where(_state == 1)
	plt.scatter(y, x, c='black', s=200, edgecolors='black')
	
	p, q = np.shape(_probs)
	for i in range(p+1):
		plt.axhline(i-0.5, color='black', lw=1)
	for i in range(q+1):
		plt.axvline(i-0.5, color='black', lw=1)
	
	plt.colorbar(m)
	
	plt.tight_layout()
	if outfilename is not None:
		plt.savefig(outfilename)
	# end def
# end def
###################################################
###################################################


# parse inputs
parser = argparse.ArgumentParser(description='Encode MCTS game-play data for machine learning')
parser.add_argument('--label',    help="game label", type=str, required=True)
parser.add_argument('--outfig',   help="output search vector figure (.png)", type=str, required=False, default=None)
parser.add_argument('--infile' ,  help="input game-play file (.dill)", type=str, required=True)
parser.add_argument('--outfile' , help="output file name (.json)", type=str, required=True)
pars = vars(parser.parse_args())

game_label = pars['label']
infile     = pars['infile']
outfile    = pars['outfile']
outfig     = pars['outfig']

# load the game play data
gameplay = dill.load(open(infile, 'rb'))

###################################################
############## ACTUALLY ENCODING DATA #############
###################################################
training_data = []
for _player in ['data_p', 'data_q']:
	for epoch_data in gameplay[_player]:
		_label = str(uuid.uuid4())
		input_stack = encode_input_state  (epoch_data['states'])
		target_vec  = encode_output_vector(epoch_data['probs'], epoch_data['winner'])
		if target_vec is None:
			continue
		# end if

		training_data.append({
			'game_label': game_label, 
			'state_label': _label, 
			'input': input_stack.tolist(), 
			'target': target_vec.tolist()}
		) # end append

		# plotting (optional)
		if outfig is not None:
			outfigname = str(_label+'.png')
			_state = epoch_data['states'][-1][0]
			_probs = target_vec[:-1].reshape(8, 8)
			plot_instance(_state, _probs, outfig)
		# end if
	# end for
# end for
###################################################
###################################################


###################################################
################# WRITE TO OUTPUT #################
###################################################
import json
with open(outfile, 'w') as fout:
	json.dump(training_data, fout)
# end with
###################################################
###################################################
