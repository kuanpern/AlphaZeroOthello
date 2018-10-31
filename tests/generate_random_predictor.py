class predictor:
	def predict(self, states):
		import numpy as np
		return np.random.rand(8, 8)
	# end def
# end class

import dill
a = {'model_bin': predictor()}
dill.dump(a, open('pars/random_predictor.dill', 'wb'))

