import random
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

rand_factor = 0.3
# initalize agent
predictor = GreedyPredictor(OthelloGame, rand_factor=rand_factor)


#########################
## DEFINE A WEB SERVER ##
#########################
import flask
app = flask.Flask(__name__)

@app.route("/")
def index():
	return "This is a MCTS predictor interface server. Use /get to predict the next state."
# end def

@app.route("/get", methods=['POST'])
def get():
	import dill
	import json
	import base64

	# get content
	content = flask.request.get_json()
	state_repr = content['data']
	# decode content
	state_repr = base64.decodebytes(state_repr.encode('ascii'))
	state = dill.loads(state_repr)
	# make prediction
	action = predictor.get(state)
	# encode prediction
	action_repr = dill.dumps(action)
	action_repr = base64.encodebytes(action_repr).decode('ascii')
	# send back
	output = {'data': {'action': action_repr}}
	return flask.jsonify(output)
# end def


# run the server
if __name__ == '__main__':
	app.run(host='localhost', port=8080, debug=True)
# end if



