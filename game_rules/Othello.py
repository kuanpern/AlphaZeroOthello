import os
import numpy as np
import copy
import matplotlib.pyplot as plt
import time
import sys
import random
import uuid
from string import Template

class OthelloGame(object):
	def __init__(self, board_size = (8, 8)):
		self.board = np.zeros(board_size, dtype=int)
		self.cur_player = 1

		p, q = int(board_size[0]/2), int(board_size[1]/2)
		self.board[p-1, q-1] = -1
		self.board[p-1, q  ] =  1
		self.board[p  , q-1] =  1
		self.board[p  , q  ] = -1

		self.state = [self.board, self.cur_player]
		self.states = [self.state]
	# end def

	def set_state(self, state_in, append=True):
		self.state = state_in
		if append is True:
			self.states.append(self.state)
		# end if
	# end def

	def set_states(self, states_in):
		self.states = states_in
		self.state  = self.states[-1]
	# end def

	# The following methods are used by the agents to determine valid moves
	@staticmethod
	def get_all_legal_moves(states):
		"""Return a list of legal moves available from this state."""
		state = states[-1]
		board, player = state

		output = []
		p, q = len(board), len(board[0])
		for i in range(p):
			for j in range(q):
				next_state = OthelloGame.get_next_state([board, player], (i, j))
				if next_state is None:
					continue
				# end if
				output.append({'move': (i, j), 'state': next_state})
			# end for
		# end for

		# special case of PASS
		if output == []:
			output = [{'move': (-1, 1), 'state': [board, -player]}]
		# end if
		return output
	# end def

	def play_move(self, move): # surrender / pass
		next_state = OthelloGame.get_next_state(self.state, move)
		if next_state is None:
			print('Invalid move', move)
			return
		# end if
		self.set_state(next_state)
	# end def

	@staticmethod
	def get_next_state(state, move):
		board_in, player = state
		board = np.copy(board_in)
		p, q = np.shape(board)
		r0, s0 = move
		# must be empty slot
		if board[r0, s0] != 0:
			return None
		# end if

		# find valid directions to complete the line (adjacent opposite color)
		_dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
		traces = []
		valid_dirs = []
		for _dir in _dirs:
			dr, ds =  _dir
			r = r0 + dr; s = s0 + ds

			if r < 0 or s < 0 or r > p-1 or s > q-1: # out of board
				continue
			if board[r, s] == -player:
				valid_dirs.append(_dir)
			# end if
		# end for
		# search to complete the line
		for _dir in valid_dirs:
			trace = [move]
			dr, ds =  _dir
			r, s = r0, s0
			while True:
				r = r + dr; s = s + ds
				if r < 0 or s < 0 or r > p-1 or s > q-1: # out of board
					trace = []
					break
				elif board[r, s] == 0:
					trace = [] # not closing the line
					break
				elif board[r, s] == -player:
					trace.append(tuple([r, s]))
				elif board[r, s] ==  player:
					break
				else:
					raise Exception('invalid cell value')
				# end if
			# end while
			traces.extend(trace)
		# end for

		# no change possible, illegal move
		if len(traces) == 0:
			return None
		# end if

		for trace in traces:
			r, s = trace
			board[r, s] = player
		# end for
		return [board, -player]
	# end def

	@staticmethod
	def get_winner(state):
		return np.sign(state[0].sum())
	# end def

	@staticmethod
	def print_board(board, title="", outfilename=None):
		plt.cla()
		ax = plt.gca()
		ax.set_yticklabels([])
		ax.set_xticklabels([])
		plt.xlim(0, 1)
		plt.xlim(0, 1)

		ax.set_facecolor('green')
		step = 1. / 8
		for i in range(9):
			plt.axhline(step*i - step/2., color='black')
		for i in range(9):
			plt.axvline(step*i - step/2., color='black')

		for j in range(len(board)):
			for i in range(len(board)):
				if board[i, j] == 0:
					continue
				elif board[i, j] == 1:
					_ = plt.Circle((i*step, j*step), step/2.*0.9, facecolor="black")
					ax.add_artist(_)
				elif board[i, j] == -1:
					_ = plt.Circle((i*step, j*step), step/2.*0.9, facecolor='white')
					ax.add_artist(_)
				# end if
			# end for
		# end for

		plt.xlim(0-step/2., 1-step/2.)
		plt.ylim(0-step/2., 1-step/2.)
		plt.gcf().set_size_inches(6, 6)
		plt.title(title)
		if outfilename is None:
			outfilename = str(time.time())+'.png'
		plt.savefig(outfilename)
	# end def
# end class

player_names = {1: 'B', -1: 'W'}

if __name__ == '__main__':
	stime = time.time()
	game_obj = OthelloGame()
	# play a random game
	cur_player = 1
	while True:
		nexts = OthelloGame.get_all_legal_moves([game_obj.state])
		if len(nexts) == 0: # no possible move for this player
			print('No possible move for player %s' % player_names[cur_player])

			# test if opponent has move
			board, cur_player = game_obj.states[-1]
			_state = [board, -cur_player]
			if len(OthelloGame.get_all_legal_moves([_state])) == 0: # if no possible move for opponent also, end game
				print('No possible move for player %s' % player_names[-cur_player])
				print('End game.')
				break
			else:
				game_obj.set_state(_state)
			# end if
		else:
			chosen = random.choice(nexts)
			print('Player "%s" plays at %s' % (player_names[chosen['state'][1]], str(chosen['move']),))
			game_obj.set_state(chosen['state'])
		# end if
	# end while

	det = np.sign(OthelloGame.get_winner(game_obj.state[0]))
	if det == 0:
		print('Draw game')
	else:
		print('Player', player_names[det], 'Wins.')
	# end if
	etime = time.time()
	print('Game took %5.5f secs' % (etime-stime))


	tag = str(uuid.uuid4())
	os.makedirs(tag)
	print('Printing graphics in directory:', tag)
	for i in range(len(game_obj.states)):
		state = game_obj.states[i]
		_board, _player = state
		game_obj.print_board(_board, outfilename = tag + os.sep + str(i).zfill(2)+'.png')
	# end for
# end main


