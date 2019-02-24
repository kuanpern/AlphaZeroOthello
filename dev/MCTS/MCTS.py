# main script for monte carlo tree search
import time
import copy
import random
import logging
logger = logging.getLogger()
from .utils import calculate_UCTs

class MCTS_Runner:
	def __init__(self, Node, agent, logger_name=__name__):
		self.Node  = Node
		self.agent = agent

		# default node choosing strategy
		self.choose_node = self.choose_most_visited
	# end def

	def set_state(self, state):
		self.state = copy.deepcopy(state)
	# end def

	def build_tree(self, tree_depth=3, prior_node=None, logger_name=__name__):
		logger = logging.getLogger(logger_name)

		# make root
		if prior_node is None: # from scratch
			root = self.Node("root")
			root.state = self.state
		else:
			root = copy.copy(prior_node)
		# end if

		# BUILD LAYERS
		layers = [[root]] # first layer consists of only root
		logger.info('   - building search tree')
		for _level in range(tree_depth):
			new_layer = []
			for node in layers[-1]:
				if len(node.children) == 0:
					child_nodes = node.grow_branches() # grow_branches
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

	def start_mcts(self, tree_depth=3, allowed_time=None, step_size=20, prior_node=None, logger_name=__name__):
		logger = logging.getLogger(logger_name)
		stime = time.time()
		############################
		###### build the tree ######
		############################
		self.root = self.build_tree(tree_depth=tree_depth, prior_node=prior_node, logger_name=logger_name)
		############################


		############################
		###### MAIN MTCS HERE ######
		############################
		n_iter = 0
		logger.info('  = simulating: ')
		while True:
			logger.info(str(n_iter)+'. ')
			# check for time out
			# -- time based exit
			if allowed_time is not None:
				if time.time() - stime >= allowed_time:
					break
				# end if
			# end if

			for i in range(step_size):
				self.epoch_update(tree_depth=tree_depth)
				# estimate confidence
				_node = self.choose_node(self.root.children)

				# compute confidence
				r = _node.success / _node.visits
				self.confidence = r
				n_iter += 1
			# end for
		# end while
		logger.info('\n')
		logger.info('  = %d games simulated\n' % (n_iter, ))
		logger.info(self.root.print_tree()+'\n')
		############################

		return self.root # return simulated tree
	# end def

	def epoch_update(self, tree_depth):
		###################################
		######### SELECTION PHASE #########
		###################################

		# note: parallelization opportunity here

		# select child node to expand
		sel_node = self.root
		for _level in range(tree_depth):
			child_nodes = sel_node.children
			if len(child_nodes) == 0: # end of search tree
				break
			# end if
			# calculate uct
			ucts = calculate_UCTs(child_nodes)
			# select with highest value
			sorter = [(ucts[i], random.random(), i) for i in range(len(ucts))]
			sorter.sort()
			sel = sorter[-1][-1]
			sel_node = child_nodes[sel]
		# end for
		###################################


		###################################
		######### EXPANSION PHASE #########
		###################################
		# - initial state
		init_state = sel_node.state
		###################################


		####################################
		######### SIMULATION PHASE #########
		####################################
		winner = self.agent.playout(init_state)['winner']
		###################################


		###################################
		########## UPDATE PHASE ###########
		###################################
		sel_node.visits  += 1
		if sel_node.player == winner:
			sel_node.success += 1
		# end if
		for i in range(tree_depth):
			sel_node = sel_node.parent
			if sel_node is None: # case for pre-maturely ended tree (no move or end game)
				break
			# end if
			sel_node.visits  += 1
			if sel_node.player == winner:
				sel_node.success += 1
			# end if
		# end for
		###################################
	# end def


	@staticmethod
	def choose_most_success(nodes):
		# choose the most successful node as output
		sorter = [(node.success / node.visits, random.random(), node) for node in nodes]
		sorter.sort()
		return sorter[-1][-1]
	# end def


	@staticmethod
	def choose_most_visited(nodes):
		# choose the most visited node as output
		sorter = [(node.visits, random.random(), node) for node in nodes]
		sorter.sort()
		return sorter[-1][-1]
	# end def
# end class
