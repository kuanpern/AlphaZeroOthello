# import libraries
import dill

######################
## Import game rule ##
######################
import rules.Othello as Othello
OthelloGame = Othello.OthelloGame   # shorthand

######################
## Define Predictor ##
######################
class GreedyPredictor:
	def __init__(self, Game, rand_factor=0.3):
		self.Game = Game
		self.rand_factor = rand_factor
	# end def

	def get(self, state):
		nexts = self.Game.list_nexts(state)
		if len(nexts) > 1:
			# random 
			if random.random() < self.rand_factor:
				return random.choice(nexts).action
			# end if

			# greedy
			sorter = []
			for item in nexts:
				value = sum(item.state[-1].data.flatten())
				value = value*state[-1].player
				sorter.append([value, random.random(), item.action])
			# end for
			sorter.sort()
			return sorter[-1][-1]
		else:
			return nexts[0].action
		# end if
	# end def
# end class

outfile = 'greedy_predictor.dill'
rand_factor = 0.3
# initalize agent
predictor = GreedyPredictor(OthelloGame, rand_factor=rand_factor)
with open(outfile, 'wb') as fout:
	dill.dump(predictor, fout)
# end with
print('wrote to: %s' % (outfile,))
