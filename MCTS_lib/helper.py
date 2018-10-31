# main script for monte carlo tree search
import logging
logger = logging.getLogger(__name__)
from anytree import Node, RenderTree
from anytree.dotexport import RenderTreeGraph

# implement tree structure
class TreeNode(Node):
	def initialize(self):
		self.label = ''
		self.data = {
			'states' : [],
			'visits' : 0,
			'success': 0,
		} # end data
	# end def

	def grow_branches(self, pars, label=None): # grow_branches method specific to different games
		return []
	# end def

	def print_tree(self, level=0):
		print (' '*level, '-', self.label, ':', self.data['success'], '/', self.data['visits'])
		for child in self.children:
			child.print_tree(level = level + 1)
		# end for
	# end def

	def print_tree(self, level=0):
		out_p = (' '*level, '-', self.label, ':', self.data['success'], '/', self.data['visits'])
		out_p = ' '.join(list(map(str, out_p)))
		for child in self.children:
			out_q = child.print_tree(level = level + 1)
			out_p = out_p + '\n' + out_q
		# end for
		return out_p
	# end def

# end class

class GameDataNode(TreeNode):

	def cur_player(self):
		return self.data['states'][-1][1]
	# end def

	def grow_branches(self, pars, label=None):
		output = []
		# get the next states
		nexts = self.Game.get_all_legal_moves(self.data['states'])
		for item in nexts:
			new_state = item['state']
			move      = item['move']

			# create a node for each next state
			node = self.__class__(label)
			node.initialize()
			node.label = str(move)
			new_states = self.data['states'] + [new_state]
			node.data['states'] = new_states[1:]
			node.data['move']   = move
			output.append(node)
		# end for
		return output
	# end def
# end class

# UCT definition
def calculate_UCTs(nodes, c = 1.414):
	import numpy as np
	t = sum([node.data['visits'] for node in nodes])
	if t == 0:
		return [np.inf] * len(nodes)
	d = np.log(t)
	# calculate uct value for all nodes
	ucts = []
	for i in range(len(nodes)):
		node = nodes[i]
		n = node.data['visits']
		w = node.data['success']
		if n != 0:
			uct = w/n + c * np.sqrt(d/n)
		else:
			uct = np.inf # always visit un-visited node
		# end if
		ucts.append(uct)
	# end for
	return ucts
# end def

