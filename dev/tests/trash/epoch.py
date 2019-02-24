def run_epoch(game_obj, mcts_operator_p, mcts_operator_q, p_configs, q_configs, max_game_length = 62, prior_nodes_repo_size=300):

	# report the new board
	_state = game_obj.states[-1][0]
	json_state = json.dumps(_state.tolist())
	UDPSock_BOARD.send(json_state)

	# read parameters
	tree_depth_p   = p_configs['tree_depth']
	memory_p       = p_configs['memory']
	allowed_time_p = p_configs['allowed_time']
	tree_depth_q   = q_configs['tree_depth']
	memory_q       = q_configs['memory']
	allowed_time_q = q_configs['allowed_time']

	# start
	trace = []
	DATA_p = []
#	DATA_q = []

	# in-simulation simluation re-use
	#prior_nodes_repo = OrderedDict(enumerate(range(prior_nodes_repo_size)))
	prior_nodes_repo = OrderedDict()

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
		rootLogger.info("===============\n")
		rootLogger.info(" Game turn: %d\n" % _iter)
		rootLogger.info("===============")

		rootLogger.info("Player B turn\n")
		# mcts_operator_p's turn
		# (1) select last n steps
		last_states = game_obj.states[-memory_p:]
		# (2) feed to agent
		mcts_operator_p.feed(last_states)

		# (2.5) find if node has been sampled before
#		rootLogger.info('last_states')
#		rootLogger.info(last_states)
		_key = make_node_key(last_states)
		prior_node = prior_nodes_repo.get(_key)

		# (3) agent run mcts
		rootLogger.info(" = start MCTS\n")
		results = mcts_operator_p.start_mcts(
			tree_depth=tree_depth_p, 
			allowed_time=allowed_time_p,
			prior_node=prior_node,
			logger=logger_p
		) # end start
		updated_node, sampled_nodes = results

		# (3.5) store sampled nodes for re-use
		for _node in sampled_nodes:
			key = make_node_key(_node.data['states'])
			prior_nodes_repo.update({key:  _node})
		# end for

		# control the size of repo
		excess_n = len(prior_nodes_repo) - prior_nodes_repo_size
		for _counter in range(excess_n):
			prior_nodes_repo.popitem(last=False)
		# end for

		# (4) record the MCTS run (first layer)
		rootLogger.info(' = collect MCTS data\n')
		mcts_probs = mcts_operator_p.get_mcts_probs()
		DATA_p.append({'states': last_states, 'probs': mcts_probs})
		# (5) select move
		move_node = mcts_operator_p.select_move()

		# check surrender or pass
		if   move_node == (-1, 0): # surrender
			winner = -cur_player
			break
		elif move_node == (-1, 1): # pass
			rootLogger.info(' - PASS\n')
			det_pass[cur_player] = True
			if det_pass[-cur_player] == True: # opponent also no move, end game
				break
			# end if
		# end if

		# (6) record move
		cur_player = last_states[-1][1]
		move = move_node.data['move']
		_confidence = mcts_operator_p.max_confidence
		rootLogger.info(' - PLAYS %s (confidence: %4.1f%%)\n' % (str(move), _confidence*100))

		# send confidence value
		UDPSock_MISC.send(_confidence)
		trace.append({'player': cur_player, 'move': move, 'confidence': _confidence})

		# actually transit into the next state
		move_state = move_node.data['states'][-1]
		game_obj.set_state(move_state)

		# report the new board
		_state = game_obj.states[-1][0]
		json_state = json.dumps(_state.tolist())
		UDPSock_BOARD.send(json_state)

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
		rootLogger.info("===============\n")
		rootLogger.info(" Game turn: %d\n" % _iter)
		rootLogger.info("===============\n")

		rootLogger.info("Player W turn\n")

		# mcts_operator_q's turn
		# (1) select last n steps
		last_states = game_obj.states[-memory_q:]
		# (2.5) find if node has been sampled before
		_key = make_node_key(last_states)
		prior_node = prior_nodes_repo.get(_key)
		# start background run
		control_Q = queue.Queue() 
		sample_Q  = queue.LifoQueue() # keep only last two run (in fact need last one only)
		sample_Q.put({})
		args = (control_Q, sample_Q, mcts_operator_q, last_states, prior_node, make_node_key, tree_depth_q, allowed_time_q, logger_q,)
		prc_mcts = Process(target=mcts_background_run, args=args)
		prc_mcts.start()
		rootLogger.info(' = start background MCTS process\n')

		# ===== USER INTERACTION HERE ==== #	
		# find all legal moves
		nexts = game_obj.get_all_legal_moves(last_states)
		if len(nexts) == 0:
			rootLogger.info('No legal moves for player\n')
			rootLogger.info('No more possible moves. Click any empty cell to continue.\n')
			(user_input, addr) = UDPSock_IN.recvfrom(buf)
			move_node  = (-1, 1)
			input_move = (-1, 1)
		else:
			legal_moves = {item['move']: item for item in nexts}
			# read input from player	
			while True:
				try:
					rootLogger.info('  = legal moves: %s\n' % str(list(legal_moves.keys())))
					rootLogger.info(' = waiting for player to respond\n')
#					user_input = input('Enter your move: ')
					while True:
						(user_input, addr) = UDPSock_IN.recvfrom(buf)
						print(' = receive input:', user_input)
						break
					# end while

					input_move = tuple(map(int, user_input.split()[:2]))
					if input_move not in legal_moves:
						err_msg = 'Invalid move'
						UDPSock.sendto(err_msg.encode(), ('localhost', output_socket_post))
						raise(Exception(err_msg))
					# end if
					move_state = legal_moves[input_move]['state']
					break
				except Exception as e:
					rootLogger.info('Error: %s\n' % str(e))
				# end try
			# end while
		# end if
		
		# get the samples from background run and put to repo 
		_repo = sample_Q.get_nowait()
		prior_nodes_repo.update(_repo)

		# send signal through queue to end the background process
		control_Q.put('END')
#		control_Q.put('END')
#		prc_mcts.terminate()
#		for i in range(20):
#			rootLogger.info ('killed background process')

		# control the size of repo
		excess_n = len(prior_nodes_repo) - prior_nodes_repo_size
		for _counter in range(excess_n):
			prior_nodes_repo.popitem(last=False)
		# end for

		# (4) record the MCTS run (first layer)
		# note: optional in interactive play
		rootLogger.info(' = collect MCTS data\n')
#		mcts_probs = mcts_operator_q.get_mcts_probs()
#		DATA_q.append({'states': last_states, 'probs': mcts_probs})


		# (5) select move
#		move_node = mcts_operator_q.select_move()
		# (6) record move
		cur_player = last_states[-1][1]
#		move = move_node.data['move']

		# confidence is undefined in interactive mode
#		_confidence = mcts_operator_q.max_confidence
#		rootLogger.info(' - PLAYS %s (confidence: %4.1f%%)' % (str(move), _confidence*100))
#		trace.append({'player': cur_player, 'move': move, 'confidence': _confidence})
		trace.append({'player': cur_player, 'move': input_move})

		# check surrender or pass
		if   move_node == (-1, 0): # surrender
			winner = -cur_player
			break
		elif move_node == (-1, 1): # pass
			rootLogger.info(' - PASS\n')
			det_pass[cur_player] = True
			if det_pass[-cur_player] == True: # opponent also no move, end game
				break
			# end if
		# end if

		# actually transit into the next state
#		move_state = move_node.data['states'][-1]
		game_obj.set_state(move_state)

		# report the new board
		_state = game_obj.states[-1][0]
		json_state = json.dumps(_state.tolist())
		UDPSock_BOARD.send(json_state)


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
#	for item in DATA_q:
#		item['winner'] = winner
#	# end for

#	return {'data_p': DATA_p, 'data_q': DATA_q, 'trace': trace, 'game_obj': game_obj}
	return {'data_p': DATA_p, 'trace': trace, 'game_obj': game_obj}
# end def

