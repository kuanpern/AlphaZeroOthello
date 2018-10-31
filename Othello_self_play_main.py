from MCTS_lib.self_play import *

###############################################
######## DEFINE OTHELLO GAME HERE #############
###############################################
import game_rules.Othello as Othello
#------------------------------------------#
#------------- DATA STRUCTURE -------------#
#------------------------------------------#
from MCTS_lib.helper import GameDataNode
class OthelloDataNode(GameDataNode):
	def __init__(self, label):
		super(GameDataNode, self).__init__(label)
		self.Game = Othello.OthelloGame
	# end def
# end class
# -----------------------------------------#

#------------------------------------------#
#---------- INTELLIGNET AGENT -------------#
#------------------------------------------#
from MCTS_lib.Agent import MCTS_Agent
class OthelloAgent_AI(MCTS_Agent):
	def __init__(self, predictor_obj):
		super(OthelloAgent_AI, self).__init__()
		self.Game = Othello.OthelloGame
		self.predictor = predictor_obj
	# end def
# end class
# -----------------------------------------#
###############################################


# command line interface
if __name__ == '__main__':
	# initialize game object
	game_obj = Othello.OthelloGame()

	# use the self-play interface
	import MCTS_lib.self_play
	MCTS_lib.self_play.cmd_interface(
		DataNode = OthelloDataNode, 
		Agent_P  = OthelloAgent_AI,
		Agent_Q  = OthelloAgent_AI,
		game_obj = game_obj
	) # end 
# end if


