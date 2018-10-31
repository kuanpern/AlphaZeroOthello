import numpy as np
import copy

class MCTS_Agent(object):
	def playout(self, states0, max_steps=np.inf, max_memory=10):
#		print 'start playout'
		_iter = 0
		# set up game from states0
		game_obj = self.Game()
		game_obj.set_states(copy.copy(states0))

		det_pass = {1: False, -1: False} # check if any move is possible or not
		while True:
#			raw_input('Enter')
#			print det_pass
			########################
			#### emergency stop ####
			########################
			_iter += 1
			if _iter > max_steps:
				break
			# end if
			########################

			########################
			## legal moves checks ##
			########################
#			print 'state:'
#			print game_obj.states[-1]
			nexts = game_obj.get_all_legal_moves(game_obj.states[-max_memory:])
			legal_moves = [item['move'] for item in nexts]
#			print len(legal_moves), ' legal moves available:', legal_moves
			if (legal_moves == [(-1, 1)]): # no valid move, pass to opponent
				pass_state = nexts[0]['state']
				cur_player = pass_state[1]

				det_pass[cur_player] = True
				if det_pass[-cur_player] is True: # opponent also no move, end game
					break
				# end if
				
				game_obj.set_state(pass_state)

#				print 'Player %s passed' % cur_player
#				pass_state[1] = -cur_player # pass to opponent
#				game_obj.set_state(pass_state)
				continue
			else: # refresh
				for key in det_pass.keys():
					det_pass[key] = False
				# end for
			# end if
			########################


			########################
			#### actual playout ####
			########################
			# (1) select last n steps
			last_states = game_obj.states[-max_memory:]
			# (2) predict the next move
			probs = self.predictor.predict(last_states)
			ranked_moves = self.rank_moves(probs)
			for _move in ranked_moves:
				if _move in legal_moves:
#					print _move, legal_moves
#					print 'choose to play at', _move
					game_obj.play_move(_move)
					break
				# end if
			# end for
			########################
		# end while
		final_state = game_obj.states[-1]
		winner = game_obj.get_winner(final_state)
		return winner
	# end def


	# implementation of how to choose a move (random etc)
	@staticmethod
	def rank_moves(probs, rw=0.2):
		probs = np.array(probs)
		probs = probs / probs.sum()
		diffs = probs - rw*np.random.rand(*np.shape(probs))
		p, q = np.shape(diffs)
		rankings = []
		for i in range(p):
			for j in range(q):
				rankings.append( (-diffs[i, j], (i, j)) )
			# end for
		# end for
		rankings.sort()
		# pos = np.unravel_index(diffs.argmax(), diffs.shape)
		return list(zip(*rankings))[1]
	# end def

# end class

