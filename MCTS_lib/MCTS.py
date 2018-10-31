# main script for monte carlo tree search
import time
import copy
import logging
logger = logging.getLogger(__name__)
from .helper import calculate_UCTs

class MCTS_operator():
	def __init__(self, Node, agent):
		self.Node  = Node
		self.agent = agent
	# end def

	def feed(self, states):
		self.states = copy.deepcopy(states)
	# end def

	def build_tree(self, tree_depth=3, prior_node=None, logger=None):
		if logger is None:
			logger = logging.getLogger('')
		# end if

		# make root
		if prior_node is None: # from scratch
			root = self.Node("root")
			root.initialize()
			root.label = 'root'
			root.data['states'] = self.states
		else:
			root = copy.copy(prior_node) # or copy prior
#			print('prior node stats: [%d/%d]' % (root.data['success'], root.data['visits']))
		# end if

		layers = [[root]] # first layer consists of only root
		# SUBSEQUENT LAYERS
		logger.info('   - building search tree\n')
		for _level in range(tree_depth):
			new_layer = []
			for node in layers[-1]:
				if len(node.children) == 0:
					child_nodes = node.grow_branches({}) # grow_branches
					# set parent
					for child_node in child_nodes:
						child_node.parent = node
					# end for
				else:
					child_nodes = node.children
				# end if

				new_layer.extend(child_nodes) # attach nodes to new layer
			# end for
			layers.append(new_layer) # attach layer to tree
		# end for
		return root
	# end def

	def start_mcts(self, tree_depth=3, allowed_time=60, step=20, prior_node=None, logger=None):
		if logger is None:
			logger = logging.getLogger('')
		# end if
		stime = time.time()

		############################
		###### build the tree ######
		############################
		self.root = self.build_tree(tree_depth=tree_depth, prior_node=prior_node, logger=logger)
		############################


		############################
		###### MAIN MTCS HERE ######
		############################
		n_iter = 0
		logger.info('  = simulating: ')
		while True:
			logger.info(str(n_iter)+'.. ')
			# check for time out
			if time.time() - stime >= allowed_time:
				break
			for i in range(step):
				self.epoch_update(tree_depth=tree_depth)
				# estimate confidence
				_node = self.choose_most_visited(self.root.children)

				# compute confidence
				r = _node.data['success'] / _node.data['visits']
				if _node.cur_player() != self.root.cur_player():
					r = 1 - r # inverse of opponent
				# end if
				self.max_confidence = r
				n_iter += 1
			# end for
#			self.root.print_tree()
		# end while
		logger.info('\n')
		logger.info('  = %d games simulated\n' % (n_iter, ))
		logger.info(self.root.print_tree()+'\n')
#		raw_input('Enter')
		############################

		return self.root, self.root.children # return first layer
	# end def

	def epoch_update(self, tree_depth):
		###################################
		######### SELECTION PHASE #########
		###################################

		# note: parallelization opportunity here

		# select child node to expand
		sel_node = self.root
#		print sel_node.label
		for _level in range(tree_depth):
			child_nodes = sel_node.children
			if len(child_nodes) == 0: # end of search tree
				break
			# end if
			# calculate uct
			ucts = calculate_UCTs(child_nodes)
			# select with highest value
			sorter = [(ucts[i], i) for i in range(len(ucts))]
			sorter.sort()
			sel = sorter[-1][1]
			sel_node = child_nodes[sel]
#			print 'selected node:', sel_node.label
#			print sel_node.data['states'][-1]
		# end for
		###################################


		###################################
		######### EXPANSION PHASE #########
		###################################
		# - initial state
#		print 'copy state'
		states0 = sel_node.data['states']
		###################################


		####################################
		######### SIMULATION PHASE #########
		####################################
		winner = self.agent.playout(states0)
#		print('finish playout, winner:', winner)
#		raw_input('Enter')
		###################################


		###################################
		########## UPDATE PHASE ###########
		###################################
		sel_node.data['visits']  += 1
		if sel_node.cur_player() == winner:
			sel_node.data['success'] += 1
		# end if
		for i in range(tree_depth):
			sel_node = sel_node.parent
			if sel_node is None: # case for pre-maturely ended tree (no move or end game)
				break
			# end if
			sel_node.data['visits']  += 1
			if sel_node.cur_player() == winner:
				sel_node.data['success'] += 1
			# end if
		# end for
		###################################
	# end def

	def get_mcts_probs(self):
		return self.root.children
	# end def

	def select_move(self):
		if len(self.root.children) > 0:
			return self.choose_most_visited(self.root.children)
		else:
			return (-1, 1) # pass
		# end if
	# end def

	@staticmethod
	def choose_most_visited(nodes):
		# choose the most visited node as output
		max_visit = 0
		index = 0
		for i in range(len(nodes)):
			_node = nodes[i]
			if _node.data['visits'] > max_visit:
				max_visit = _node.data['visits']
				index = i
			# end if
		# end for
		sel_move = nodes[index]
		############################

		return sel_move
	# end def
# end class
