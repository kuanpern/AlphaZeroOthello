# import libraries
import sys
import dill
import hashlib
import queue
import threading
import numpy
import logging
from collections import OrderedDict
from MCTS.utils import *
from MCTS.Agent import *
from MCTS.MCTS import *

# setup logging facility
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


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

#################################
## Socket input implementation ##
#################################
def sock2action(user_input):
	action = tuple(map(int, user_input.split()))
	return action
# end def

def is_user_action_valid(Game, state, action):
	nexts = Game.list_nexts(state)
	det = action in [item.action for item in nexts]
	return det
# end def
############################


# Run MCTS in a background thread
def background_run(control_Q, result_Q, runner, configs, sel_node, prior_node):
	sampled_nodes_repo = {}

	# re-run until stopped
	while True:
		# check termination
		while control_Q.empty() is False:
			signal = control_Q.get()
			if signal == 'END':
				return
			# end if
		# end while

		# Set runner to initial state
		runner.set_state(sel_node.state)

		# Start MCTS simulation to the node
		sampled_node = runner.start_mcts(prior_node=prior_node, **configs)

		# Get the child nodes
		child_nodes = sampled_node.children

		# Update to the repo
		new_prior_nodes = {_node.str_encode(): _node for _node in child_nodes}
		sampled_nodes_repo.update(new_prior_nodes)

		result_Q.put(sampled_nodes_repo)
		logger.debug('queue size: %d' % (result_Q.qsize()))
		sel_node = sampled_node 
	# end while
# end def


# A game epoch
def run_epoch(init_state, runner_p, runner_q, configs_p, configs_q, manual_flags=[], max_game_length=60, prior_repo_max_size=300, name=None):

	# Initialize a game record
	game_record = GameRecord(name=name)
	# Initialize repo to store simulated nodes
	prior_nodes_repo = OrderedDict()
	prior_node = None

	# record the init state
	game_record.append(None, init_state)

	#########################################
	#### Actually start playing sequence ####
	#########################################

	runner_flag  = -1
	runner_dict  = {1:  runner_p, -1:  runner_q}
	configs_dict = {1: configs_p, -1: configs_q}

	# for code symmetry
	sel_node = runner_p.Node(None)
	sel_node.state = init_state

	_iter = 0
	while True:
		_iter += 1
		# emergency break
		if _iter > max_game_length:
			break
		# end if

		# pass to opponent runner
		runner_flag = -runner_flag
		runner  =  runner_dict[runner_flag]
		configs = configs_dict[runner_flag]

		logger.debug('iteration: %d' % (_iter,))
		logger.debug('player: %d' % (runner_flag,))

		# prepare the queues
		control_Q = queue.Queue() 
		sample_Q  = queue.LifoQueue()

		# See whether this node has been sampled before
		key = sel_node.str_encode()
		prior_node = prior_nodes_repo.get(key, None) 

		# start background run
		logger.debug('start background run')
		args = (control_Q, sample_Q, runner, configs, sel_node, prior_node,)
		prc_mcts = threading.Thread(target=background_run, args=args)
		prc_mcts.start()

		# ===== USER INTERACTION HERE ==== #
		if runner_flag in manual_flags:
			while True:
#				(user_input, addr) = UDPSock_IN.recvfrom(buf)
				print(sel_node.state[-1].data)
				nexts = runner.agent.Game.list_nexts(sel_node.state)
				print([_.action for _ in nexts])
				user_input = input('Input: ')
				action = sock2action(user_input)
				if is_user_action_valid(runner.agent.Game, sel_node.state, action):
					break
				else:
					print('invalid action:', action)
				# end if
			# end while
		else:
			action = 'AUTOPILOT'
		# end if
		_scenario = {'player': sel_node.player, 'state': sel_node.state}

		# get the samples from background run and put to repo 
		if action == 'AUTOPILOT':
			time.sleep(configs['allowed_time']+0.1)
		# end if
		# ensure at least one MCTS done
		while True:
			if sample_Q.qsize() >= 1:
				break
			else:
				time.sleep(0.2)
			# end if
		# end while

		child_nodes = sample_Q.get_nowait()
		prior_nodes_repo.update(child_nodes)
		# send signal through queue to end the background process
		control_Q.put('END')

		# control the size of repo
		excess_n = max(0, len(prior_nodes_repo) - prior_repo_max_size)
		for __iter in range(excess_n):
			prior_nodes_repo.popitem(last=False)
		# end for

		# select node to transit into
		if action == 'AUTOPILOT': # let runner decides
			logger.debug('AUTOPILOT choosing')
			logger.debug('selection size: %d' % (len(child_nodes),))
			sel_node = runner.choose_node(child_nodes.values())
			logger.debug('chosen: %s' % str(sel_node.action))
		else: # player's move
			new_state = runner.agent.Game.transform(sel_node.state, action)
			sel_node = runner.Node(None, player=-runner_flag)
			sel_node.state  = new_state
			sel_node.action = action
			# if the user's node has been sampled before
			key = sel_node.str_encode()
			_node = prior_nodes_repo.get(key, None)
			if _node is not None:
				sel_node = _node
			else:
				logger.warning('not sampled before')
			# end if
		# end if

		#################
		#### summary ####
		#################
		if sel_node.visits != 0:
			confidence = sel_node.success / sel_node.visits
			mcts_prob  = {node.action: node.success / node.visits for node in child_nodes.values()}
		else:
			confidence = numpy.nan
			mcts_prob  = None
		# end if

		# Record the action-state info to record-book
		game_record.append(sel_node.action, sel_node.state, {'scenario': _scenario, 'prob': mcts_prob})

		# See if end-game has been reached
		winner = runner.agent.Game.get_winner(game_record)
		if winner is not None:
			break
		# end if
	# end while
	return game_record
# end def


#######################
## Initialize Agents ##
#######################
rand_predictor = RandomPredictor(OthelloGame)
rand_agent = Agent(OthelloGame, rand_predictor)
agent_p = rand_agent
agent_q = rand_agent

##################################
## Simulation parameter setting ##
##################################
configs_p = {'tree_depth':3, 'allowed_time': 3}
configs_q = {'tree_depth':3, 'allowed_time': 3}

# Initialize MCTS runners
runner_p = MCTS_Runner(OthelloDataNode, agent=agent_p)
runner_q = MCTS_Runner(OthelloDataNode, agent=agent_q)

# Initialize and initial state
state_memory_n = 3
new_board = OthelloHelper.new_board()
init_state = [stateType(data=new_board, player=1) for _ in range(state_memory_n)]

if __name__ == '__main__':
	game_record = run_epoch(
	  init_state = init_state,
	  runner_p   = runner_p,
	  runner_q   = runner_q,
	  configs_p  = configs_p,
	  configs_q  = configs_q,
	  manual_flags = [],
	  max_game_length = 70,
	  prior_repo_max_size = 300,
	  name = None
	)
	with open('test_game_record.dill', 'wb') as fout:
		dill.dump(game_record, fout)
	# end with
# end if
