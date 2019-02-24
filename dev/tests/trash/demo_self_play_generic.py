# import libraries
import numpy
import scipy
import sklearn
import tensorflow
import keras
import torch
import torch.nn
import dill
import random
import requests
import hashlib
from collections import OrderedDict
from MCTS.utils import *
from MCTS.Agent import *
from MCTS.MCTS import *
import matplotlib.pyplot as plt

######################
## Import game rule ##
######################
import rules.Othello as Othello
OthelloGame   = Othello.OthelloGame   # shorthand
OthelloHelper = Othello.OthelloHelper # shorthand

#####################################################
## import data structure and customize for Othello ##
#####################################################
class OthelloDataNode(GameDataNode):
	def __init__(self, name, Game=OthelloGame, player=1):
		super().__init__(Game=Game, name=name, player=player)
	# end def

	def str_encode(self):
		'''encode into a string representation'''
		temp = []
		for state in self.state:
			data_str = ' '.join(shlex.split(str(state.data)))
			temp.append(str({'data': data_str, 'player': self.player}))
		# end for
		return hashlib.md5(str(temp).encode()).hexdigest()
	# end def
# end class

################################################
## Import Agent class and inject Othello game ##
################################################
class OthelloAgent(Agent):
	def __init__(self, predictor):
		super().__init__(
			Game = OthelloGame,
			predictor = predictor
		) # end super
	# end def
# end class


def run_epoch(agent_p, agent_q, configs_p, configs_q, state_memory_n, max_game_length=60, prior_nodes_repo_size=300, name=None):
	# helper function
	def make_case_class(pars):
		class case_class:
			pass
		# end class
		obj = case_class()
		obj.__dict__.update({name: None for name in pars})
		return obj
	# end def

	# Initialize MCTS runners
	runner_p = MCTS_Runner(OthelloDataNode, agent=agent_p)
	runner_q = MCTS_Runner(OthelloDataNode, agent=agent_q)

	# Initialize a game record
	game_record = GameRecord(name=name)
	# Initialize repo to store simulated nodes
	prior_nodes_repo = OrderedDict()
	prior_node = None

	# Initialize and initial state
	new_board = OthelloHelper.new_board([6, 6])
	init_state = [stateType(data=new_board, player=1) for _ in range(state_memory_n)]
	# record the init state
	game_record.append(None, init_state)

	#########################################
	#### Actually start playing sequence ####
	#########################################
	# for code symmetry
	sel_node = make_case_class(['state'])
	sel_node.state = init_state
	runner_flag = -1
	runner_dict = {1: runner_p, -1: runner_q}

	_iter = 0
	while True:
		_iter += 1
		# emergency break
		if _iter > max_game_length:
			break
		# end if

		# pass to opponent runner
		runner_flag = -runner_flag
		runner = runner_dict[runner_flag]

		# Set runner to initial state
		runner.set_state(sel_node.state)

		# Start MCTS simulation to the node
		sampled_node = runner.start_mcts(prior_node=prior_node, **configs_p)

		# Get the child nodes
		child_nodes = sampled_node.children

		# Update to the repo
		new_prior_nodes = {_node.str_encode(): _node for _node in child_nodes}
		prior_nodes_repo.update(new_prior_nodes)
		# control the size of repo
		excess_n = max(0, len(prior_nodes_repo) - prior_nodes_repo_size)
		for __iter in range(excess_n):
			prior_nodes_repo.popitem(last=False)
		# end for

		# select node to transit into
		sel_node = runner.choose_node(child_nodes)

		#################
		#### summary ####
		#################
		confidence = sel_node.success / sel_node.visits
		mcts_prob = {node.action: node.success / node.visits for node in child_nodes}

		# Record the action-state info to record-book
		game_record.append(sel_node.action, sel_node.state, {'state': sampled_node.state, 'prob': mcts_prob})

		# See if end-game has been reached
		winner = OthelloGame.get_winner(game_record)
		if winner is not None:
			break
		# end if
	# end while
	return game_record
# end def


# read and parse input
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--outfile", type=str, help="output file name (*.dill)", required=True)
parser.add_argument("--predictor_p", type=str, help="predictor file for player P (*.dill)", required=True)
parser.add_argument("--predictor_q", type=str, help="predictor file for player Q (*.dill)", default=None)
parser.add_argument("--depth_p", type=int, help="simulation tree depth for player P", default=3)
parser.add_argument("--depth_q", type=int, help="simulation tree depth for player Q", default=None)
parser.add_argument("--time_p", type=float, help="simulation time for player P", default=10.0)
parser.add_argument("--time_q", type=float, help="simulation time for player Q", default=None)
args = vars(parser.parse_args())

outfile        = args['outfile']
predfile_p     = args['predictor_p']
tree_depth_p   = args['depth_p']
allowed_time_p = args['time_p']
predfile_q     = args['predictor_q']
tree_depth_q   = args['depth_q']
allowed_time_q = args['time_q']

# default values
if predfile_q is None:
	predfile_q = predfile_p
if tree_depth_q is None:
	tree_depth_q = tree_depth_p
if allowed_time_q is None:
	allowed_time_q = allowed_time_p

#######################
## Initialize Agents ##
#######################
with open(predfile_p, 'rb') as fin:
	predictor_p = dill.load(fin)
# end with
with open(predfile_q, 'rb') as fin:
	predictor_q = dill.load(fin)
# end with
agent_p = Agent(OthelloGame, predictor_p)
agent_q = Agent(OthelloGame, predictor_q)

##################################
## Simulation parameter setting ##
##################################
configs_p = {'tree_depth':tree_depth_p, 'allowed_time': allowed_time_p}
configs_q = {'tree_depth':tree_depth_q, 'allowed_time': allowed_time_q}

if __name__ == '__main__':
	game_record = run_epoch(
	  agent_p   = agent_p,
	  agent_q   = agent_q,
	  configs_p = configs_p,
	  configs_q = configs_q,
	  state_memory_n = 3,
	  max_game_length = 70,
	  prior_nodes_repo_size = 300,
	  name = None
	)
	with open(outfile, 'wb') as fout:
		dill.dump(game_record, fout)
	# end with
# end if
