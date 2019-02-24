import numpy
import copy
import random
import requests
from .utils import GameRecord

############################################
########### INTELLIGNET AGENT ##############
############################################

# predictor object must provide a "predict" method that takes in game's state and return a list of ranked action
class RandomPredictor:
	def __init__(self, Game):
		self.Game = Game
	# end def

	def evaluate(self, state):
		nexts = self.Game.list_nexts(state)
		return [(random.random(), item.action) for item in nexts]
	# end def

	def get(self, state):
		evaluations = self.evaluate(state)
		# example of random sampling here
		sorter = [(e[0]+random.random(), e[1]) for e in evaluations]
		sorter.sort()
		return sorter[-1][-1]
	# end def
# end class


# querying prediction over web
class WebServicePredictor:
	def __init__(self, url):
		self.url = url
	# end def

	@staticmethod
	def encode(state):
		# encode state such that it's json serializable
		raise NotImplementedError
	# end def

	def get(self, state):
		r = requests.post(url, json=self.encode(state))
		action = r.json()['action']
		return action
	# end def
# end class


class Agent:
	def __init__(self, Game, predictor, name=None):
		self.Game = Game
		self.name = name
		if hasattr(predictor, 'get') and callable(getattr(predictor, 'get')):
			self.predictor = predictor
		else:
			raise NotImplementedError('"get" method must be implemented in predictor')
		# end if
	# end def

	def playout(self, init_state, max_steps=70, legal_action_check=True, legal_action_max_trials=100, game_record_type='default'):
		_iter = 0

		# setup a game record
		if game_record_type == 'default':
			game_record = GameRecord()
		else:
			game_record = game_record_type()
		# end if
		game_record.append(None, init_state)

		while True:
			# emergency stop
			_iter += 1
			if _iter > max_steps:
				# default behaviour if can't finish by max_steps
				return {'winner': 0, 'record': game_record}
			# end if

			# (2) predict the next move
			_state = game_record.current_state()
			if legal_action_check is True:
				# check if the predictor gives legal action. Usually predictor should be made smart enough so this can be skipped
				_trial = 0
				while True:
					_trial += 1
					action = self.predictor.get(_state)
					nexts = self.Game.list_nexts(_state)
					legal_actions = [item.action for item in nexts]
					if action in legal_actions:
						break
					# end if

					if _trial > legal_action_max_trials:
						raise Exception("predictor give too many illegal actions")
						break
					# end if
				# end for
			else:
				action = self.predictor.get(_state)
			# end if

			new_state = self.Game.transform(_state, action)
			game_record.append(action, new_state)

			winner = self.Game.get_winner(game_record)
			if winner is not None:
				return {'winner': winner, 'record': game_record}
			# end if
		# end while
	# end def

# end class

