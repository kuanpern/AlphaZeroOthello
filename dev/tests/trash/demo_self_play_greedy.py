# import libraries
import dill
import hashlib
import numpy as np
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


#######################
## Initialize Agents ##
#######################
# predictor object must provide a "predict" method that takes in game's state and return a list of ranked action
class GreedyPredictor:
	def __init__(self, Game, rand_factor=0.3):
		self.Game = Game
		self.rand_factor = rand_factor
	# end def

	def get(self, state):
		nexts = self.Game.list_nexts(state)
		if len(nexts) > 1:
			# random 
			if random.random() < self.rand_factor:
				return random.choice(nexts).action
			# end if

			# greedy
			sorter = []
			for item in nexts:
				value = sum(item.state[-1].data.flatten())
				value = value*state[-1].player
				sorter.append([value, random.random(), item.action])
			# end for
			sorter.sort()
			return sorter[-1][-1]
		else:
			return nexts[0].action
		# end if
	# end def
# end class

# read and parse input
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--outfile", type=str, help="output file name (*.dill)", required=True)
parser.add_argument("--rand", type=float, help="random factor", default=0.3)
parser.add_argument("--depth", type=int, help="simulation tree depth", default=3)
parser.add_argument("--time", type=float, help="simulation time", default=10.0)
args = vars(parser.parse_args())

outfile      = args['outfile']
rand_factor  = args['rand']
tree_depth   = args['depth']
allowed_time = args['time']

# initalize agent
rand_predictor = GreedyPredictor(OthelloGame, rand_factor=rand_factor)
greedy_agent = Agent(OthelloGame, rand_predictor)
agent_p = greedy_agent
agent_q = greedy_agent

##################################
## Simulation parameter setting ##
##################################
configs_p = {'tree_depth':tree_depth, 'allowed_time': allowed_time}
configs_q = {'tree_depth':tree_depth, 'allowed_time': allowed_time}

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
