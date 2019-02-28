import copy
import shlex
from anytree import Node, RenderTree
from anytree.dotexport import RenderTreeGraph

####################################
############### GAME ###############
####################################
class Game:
	# The following methods are used by the agents to determine valid moves
	@staticmethod
	def list_nexts(state): # think about continuous decision space also. (just discretize?)
		raise NotImplementedError
	# end def

	@staticmethod
	def get_winner(state):
		'''None if not end-game, 1 or -1 if end game'''
		raise NotImplementedError
	# end def

	@staticmethod
	def transform(state, action):
		raise NotImplementedError
	# end def

# end class

####################################


############################################
############# DATA STRUCTURE ###############
############################################

# implement tree structure
class TreeNode(Node):
	def __init__(self, name=None, player=1):
		self.name = name
		self.state = None
		self.player  = player
		self.visits  = 0
		self.success = 0
		self.data = {}
	# end def

	def print_tree(self, level=0):
		out_p = ' '*level+'-%s: %d/%d' % (self.name, self.success, self.visits,)
		for child in self.children:
			out_q = child.print_tree(level = level + 1)
			out_p = out_p + '\n' + out_q
		# end for
		return out_p
	# end def
# end class

class GameDataNode(TreeNode):
	def __init__(self, Game, name, player=1):
		super().__init__(name, player)
		self.Game   = Game
		self.state  = None
		self.action = None
		self.data = {}
	# end def

	def grow_branches(self):
		output = []
		# get the next state
		nexts = self.Game.list_nexts(self.state)
		for item in nexts:
			new_state = item.state
			action    = item.action

			# create a node for each next state
			node = self.__class__(Game=self.Game, name=action, player=-self.player)
			node.state  = new_state
			node.action = action

			output.append(node)
		# end for
		return output
	# end def

# end class


class ZeroDataNode(GameDataNode):
	def __init__(self, Game, name, player=1):
		super().__init__(Game, name, player)
		self.is_expanded = False
		self.child_dict = {}
	# end def

	def append_children(self, children):
		for child in children:
			child.parent = self
			name = child.action
			if name != 'PASS':
				self.child_dict[tuple(name)] = child
			else:
				self.child_dict[name] = child
			# end if
		# end for
		self.is_expanded = True

		# statistics to keep
		self.reset_stats(children)
		self.P = None # <- to be evaluated
	# end def

	def reset_stats(self, children=None):
		if children is None:
			children = self.children
		# end if
		_zeros = {child.action: 0 for child in children}
		self.N = copy.deepcopy(_zeros)
		self.W = copy.deepcopy(_zeros)
		self.Q = copy.deepcopy(_zeros)
	# end def

	def assign_probs(self, P):
		# select only valid moves and re-normalize probabilities
		# - we assume neuralnet doesn't know the rules at all
		actions = {child.action for child in self.children}
		P = {action: P[action] for action in actions}
		_sum = sum(P.values())
		self.P = {key: val/_sum for key, val in P.items()}
	# end def

	def backprob(self, v):
		'''back-propagation of v'''
		if self.parent is None:
			return
		# end if

		a = self.name
#		print ('name:', a)
#		print (self.parent.W.keys())
		self.parent.W[a] += v
		self.parent.N[a] += 1
		self.parent.Q[a] = self.parent.W[a] / self.parent.N[a]
		self.parent.backprob(v)

#		self.W += v
#		self.N += 1
#		self.Q = self.W / self.N
#		if self.parent is not None:
#			self.parent.backprob(v)
#		# end if
	# end def

	def print_tree(self):
		lines = self._print_tree().splitlines()
		lines = [line for line in lines if '@' not in line]
		lines = '\n'.join(lines)
		return lines
	# end def

	def _print_tree(self, level=0):
		if self.parent is None:
			out_p = '/'
		elif self.is_expanded is False:
			out_p = '@' # edge leaf node
		else: 
			out_p = ' '*level+'-%s: %4.2f' % (self.name, self.parent.Q[self.name],)
		# end if

		for child in self.children:
			out_q = child._print_tree(level = level + 1)
			out_p = out_p + '\n' + out_q
		# end for
		return out_p
	# end def

	def end_game(self):
		if hasattr(self, 'is_end_game') is False:
			self.is_end_game = self.Game.end_game(self.state)
		# end if
		return self.is_end_game
	# end def

	def expanded(self):
		return self.is_expanded
	# end def
# end class


# case classes
class stateType:
	def __init__(self, data=None, player=None):
		self.data   = data
		self.player = player
	# end def
# end class

class stateActionType:
	def __init__(self, state=None, action=None):
		self.state  = state
		self.action = action
	# end def
# end class

class GameRecord:
	def __init__(self, name=None):
		self.name = name
		self.action_trace = []
		self. state_trace = []
		self.data = []
	# end def

	def current_state(self):
		return self.state_trace[-1]
	# end def

	def append(self, action, state, data=None):
		self.action_trace.append(action)
		self. state_trace.append(state)
		self.data.append(data)
	# end def

	def trace_size(self):
		return len(self.state_trace)
	# end def

# end class


# UCT definition
def calculate_UCTs(nodes, c = 1.414):
	import numpy as np
	t = sum([node.visits for node in nodes])
	if t == 0:
		return [np.inf] * len(nodes)
	d = np.log(t)
	# calculate uct value for all nodes
	ucts = []
	for i in range(len(nodes)):
		node = nodes[i]
		n = node.visits
		w = node.success
		if n != 0:
			uct = w/n + c * np.sqrt(d/n)
		else:
			uct = np.inf # always visit un-visited node
		# end if
		ucts.append(uct)
	# end for
	return ucts
# end def

