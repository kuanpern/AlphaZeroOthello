import copy
import numpy
from MCTS.utils import *

###############################################
######## DEFINE OTHELLO GAME HERE #############
###############################################
class OthelloGame(Game):

	###################################
	######## Required Methods #########
	###################################

	@staticmethod
	def list_nexts(state):
		"""Return a list of legal actions available from this state_i."""
		state_i = state[-1]
		board  = state_i.data
		player = state_i.player

		output = []
		p, q = board.shape
		for i in range(p):
			for j in range(q):
				action = (i, j)
				next_state = OthelloGame.transform(state=state, action=action)
				if next_state is not None:
					_next = stateActionType(state=next_state, action=action)
					output.append(_next)
				# end if
			# end for
		# end for

		# special case = PASS
		if output == []:
			action = 'PASS'
			mem = len(state)
			next_state = copy.deepcopy(state)
			# - copy the last state instance but change the player
			next_state_i = stateType(
				data  = state[-1].data, 
				player=-state[-1].player
			) # end next_state_i
			next_state.append(next_state_i)
			next_state = next_state[-mem:]
			output = [stateActionType(state=next_state, action=action)]
		# end if
		return output
	# end def

	@staticmethod
	def get_winner(state):
		def cur_winner(state):
			return numpy.sign(state[-1].data.sum())
		# end def

		# all filled up
		if 0 not in state[-1].data.flatten().tolist():
			# end game is True, winner 
			return cur_winner(state)
		# end if

		# both sides have to pass
		if OthelloGame.list_nexts(state) == ['PASS']:
			mem = len(state)
			next_state = copy.deepcopy(state)
			# - copy the last state instance but change the player
			next_state_i = stateType(
				data  = state[-1].data, 
				player=-state[-1].player
			) # end next_state_i
			next_state.append(next_state_i)
			next_state = next_state[-mem:]
	
			if OthelloGame.list_nexts(next_state) == ['PASS']:
				return cur_winner(state)
			# end if
		# end if
		return None
	# end def

	@staticmethod
	def transform(state, action):

		# special case of "PASS"
		if action == 'PASS':
			mem = len(state)
			next_state = copy.deepcopy(state)
			# - copy the last state instance but change the player
			next_state_i = stateType(
				data  = state[-1].data, 
				player=-state[-1].player
			) # end next_state_i
			next_state.append(next_state_i)
			next_state = next_state[-mem:]
			return next_state
		# end if

		# get the last state instance
		board  = state[-1].data
		player = state[-1].player

		board = numpy.copy(board)
		p, q = numpy.shape(board)
		r0, s0 = action
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
			trace = [action]
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

		# no change possible, illegal action
		if len(traces) == 0:
			return None
		# end if

		for trace in traces:
			r, s = trace
			board[r, s] = player
		# end for

		# generate next state
		next_state_i = stateType(data=board, player=-player)
		next_state = state[1:]
		next_state.append(next_state_i)

		return next_state
	# end def

# end class


# Other helper functions ...
class OthelloHelper:
	@staticmethod
	def new_board(board_size = (8, 8)):
		board = numpy.zeros(board_size, dtype=int)
		cur_player = 1

		p, q = int(board_size[0]/2), int(board_size[1]/2)
		board[p-1, q-1] = -1
		board[p-1, q  ] =  1
		board[p  , q-1] =  1
		board[p  , q  ] = -1

		return board
	# end def

	@staticmethod
	def print_board(state, title="", highlight=None, outfilename=None):
		import matplotlib.pyplot as plt
		board  = state.data
		player = state.player
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

		if highlight is not None:
			if highlight != 'PASS':
				i, j = highlight
				_ = plt.Circle((i*step, j*step), step/2.*0.9, facecolor='None', edgecolor='red')
				ax.add_artist(_)
			# end if
		# end if

		plt.xlim(0-step/2., 1-step/2.)
		plt.ylim(0-step/2., 1-step/2.)
		plt.gcf().set_size_inches(8, 8)
		plt.title(title)
		if outfilename is not None:
			plt.savefig(outfilename)
		# end if
	# end def
# end class



