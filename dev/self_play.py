#!/usr/bin/python
import sys
import dill
import time
from .MCTS import *
from collections import OrderedDict


def run_epoch(game_obj, mcts_operator_p, mcts_operator_q, p_configs, q_configs, max_game_length = 62, prior_nodes_repo_size=300):

	# read parameters
	memory_p       = p_configs['memory']
	allowed_time_p = p_configs['allowed_time']
	memory_q       = q_configs['memory']
	allowed_time_q = q_configs['allowed_time']

	# start
	trace = []
	DATA_p = []
	DATA_q = []

	# in-simulation simluation re-use
	#prior_nodes_repo = OrderedDict(enumerate(range(prior_nodes_repo_size)))
	prior_nodes_repo = OrderedDict()
	node_sizes = [0]

	# actual play
	_iter = 0
	det_pass = {1: False, -1: False} # check if any move is possible or not
	while True:

		########################################################################
		########################################################################
		########################################################################
		# emergency stop
		_iter += 1
		if _iter > max_game_length:
			break
		# end if
		print("===============")
		print(" Game turn: %d" % _iter)
		print("===============")

		print("Player B turn")
		# mcts_operator_p's turn
		# (1) select last n steps
		last_states = game_obj.states[-memory_p:]
		# (2) feed to agent
		mcts_operator_p.feed(last_states)

		# (2.5) find if node has been sampled before
		_key = make_node_key(last_states)
#		print('A:', _key)
		prior_node = prior_nodes_repo.get(_key)

		# (3) agent run mcts
		print(" = start MCTS")
		updated_node, sampled_nodes = mcts_operator_p.start_mcts(
			allowed_time=allowed_time_p,
			prior_node=prior_node
		) # end start

		# (3.5) store sampled nodes for re-use
		for _node in sampled_nodes:
			key = make_node_key(_node.data['states']) # assume str represenation is unique
#			print('B:', key)
			prior_nodes_repo.update({key:  _node})
		# end for
#		print ('prior node repo size [%d]: %d' % (_iter, len(prior_nodes_repo)) )
		node_sizes.append(len(prior_nodes_repo))
		# control the size of repo
		excess_n = len(prior_nodes_repo) - prior_nodes_repo_size
		for _counter in range(excess_n):
			prior_nodes_repo.popitem(last=False)
		# end for

		# (4) record the MCTS run (first layer)
		print(' = collect MCTS data')
		mcts_probs = mcts_operator_p.get_mcts_probs()
		DATA_p.append({'states': last_states, 'probs': mcts_probs})
		# (5) select move
		move_node = mcts_operator_p.select_move()

		# check surrender or pass
		if   move_node == (-1, 0): # surrender
			winner = -cur_player
			break
		elif move_node == (-1, 1): # pass
			print(' - PASS')
			det_pass[cur_player] = True
			if det_pass[-cur_player] == True: # opponent also no move, end game
				break
			# end if
		# end if

		# (6) record move
		cur_player = last_states[-1][1]
		move = move_node.data['move']
		_confidence = mcts_operator_p.max_confidence
		print(' - PLAYS %s (confidence: %4.1f%%)' % (str(move), _confidence*100))
		trace.append({'player': cur_player, 'move': move, 'confidence': _confidence})

		# actually transit into the next state
		move_state = move_node.data['states'][-1]
		game_obj.set_state(move_state)
		det_pass[ cur_player] = False
		det_pass[-cur_player] = False

		########################################################################
		########################################################################
		########################################################################
		# emergency stop
		_iter += 1
		if _iter > max_game_length:
			break
		# end if
		print("===============")
		print(" Game turn: %d" % _iter)
		print("===============")

		print("Player W turn")

		# mcts_operator_q's turn
		# (1) select last n steps
		last_states = game_obj.states[-memory_q:]
		# (2) feed to agent
		mcts_operator_q.feed(last_states)

		# (2.5) find if node has been sampled before
		_key = make_node_key(last_states)
#		print('R:', _key)
		prior_node = prior_nodes_repo.get(_key)
#		if prior_node is not None:
#			print('hit previous node')
#		else:
#			print('no hit')
#		# end if

		# (3) agent run mcts
		print(" = start MCTS")
		updated_node, sampled_nodes = mcts_operator_q.start_mcts(
			allowed_time=allowed_time_q,
			prior_node=prior_node
		) # end start

		# (3.5) store sampled nodes for re-use
		for _node in sampled_nodes:
			key = make_node_key(_node.data['states']) # assume str represenation is unique
#			print('B:', key)
			prior_nodes_repo.update({key:  _node})
		# end for
#		print ('prior node repo size [%d]: %d' % (_iter, len(prior_nodes_repo)) )
		node_sizes.append(len(prior_nodes_repo))
		# control the size of repo
		excess_n = len(prior_nodes_repo) - prior_nodes_repo_size
		for _counter in range(excess_n):
			prior_nodes_repo.popitem(last=False)
		# end for

		# (4) record the MCTS run (first layer)
		print(' = collect MCTS data')
		mcts_probs = mcts_operator_q.get_mcts_probs()
		DATA_q.append({'states': last_states, 'probs': mcts_probs})
		# (5) select move
		move_node = mcts_operator_q.select_move()
		# (6) record move
		cur_player = last_states[-1][1]
		move = move_node.data['move']
		_confidence = mcts_operator_q.max_confidence
		print(' - PLAYS %s (confidence: %4.1f%%)' % (str(move), _confidence*100))
		trace.append({'player': cur_player, 'move': move, 'confidence': _confidence})

		# check surrender or pass
		if   move_node == (-1, 0): # surrender
			winner = -cur_player
			break
		elif move_node == (-1, 1): # pass
			print(' - PASS')
			det_pass[cur_player] = True
			if det_pass[-cur_player] == True: # opponent also no move, end game
				break
			# end if
		# end if

		# actually transit into the next state
		move_state = move_node.data['states'][-1]
		game_obj.set_state(move_state)
		det_pass[ cur_player] = False
		det_pass[-cur_player] = False
	# wnd while

	# determine winner
	final_state = game_obj.states[-1]
	winner = game_obj.get_winner(final_state)

	# decorate the data
	for item in DATA_p:
		item['winner'] = winner
	# end for
	for item in DATA_q:
		item['winner'] = winner
	# end for

	return {'data_p': DATA_p, 'data_q': DATA_q, 'trace': trace, 'game_obj': game_obj}
# end def


def cmd_interface(DataNode, Agent_P, Agent_Q, game_obj):
	import yaml
	import argparse

	# parse inputs
	parser = argparse.ArgumentParser(description='Othello self-play single run')
	parser.add_argument('--agent_p',    help="Agent P binary file (.dill)", type=str, required=True)
	parser.add_argument('--agent_q',    help="Agent Q binary file (.dill)", type=str, required=True)
	parser.add_argument('--config_p',   help="Agent P config file (.yaml)", type=str, required=True)
	parser.add_argument('--config_q',   help="Agent Q config file (.yaml)", type=str, required=True)
	parser.add_argument('--max_length', help="Maximum game length", type=int, default=500)
	parser.add_argument('--repo_size',  help="Sampled nodes to keep in memory", type=int, default=1000)
	parser.add_argument('--outfile',    help="output directory (.dill)", type=str, required=True)
	pars = vars(parser.parse_args())

	# read inputs
	pars_p_filename = pars['agent_p']
	pars_q_filename = pars['agent_q']
	outfilename     = pars['outfile']
	max_game_length = pars['max_length']
	prior_nodes_repo_size = pars['repo_size']
	p_configs = yaml.load(open(pars['config_p'], 'rb'))
	q_configs = yaml.load(open(pars['config_q'], 'rb'))

	# read parameter file for agent p and q
	pars_p = dill.load(open(pars_p_filename, 'rb'))
	pars_q = dill.load(open(pars_q_filename, 'rb'))

	# initialize the agents
	agent_p = Agent_P(pars_p['model_bin'])
	agent_q = Agent_Q(pars_q['model_bin'])
	# initialize MCTS operator with the respective agent
	mcts_operator_p = MCTS_operator(Node=DataNode, agent=agent_p)
	mcts_operator_q = MCTS_operator(Node=DataNode, agent=agent_q)

	# run a game
	output_data = run_epoch(game_obj, mcts_operator_p, mcts_operator_q, p_configs, q_configs, max_game_length, prior_nodes_repo_size)

	# write output
	with open(outfilename, 'wb') as fout:
		dill.dump(output_data, fout)
	# end with
# end def
