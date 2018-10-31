# test real time harvesting
import time



from multiprocessing import Process, Queue

def f(q):
    q.put([42, None, 'hello'])


    q = Queue()
    p = Process(target=f, args=(q,))
    p.start()

	while signal_received:
		harvested = q[-1]
		p.kill() # simply kill the process (brutal !!)
    print(q.get())    # prints "[42, None, 'hello']"
    p.join()


def inc(x, allowed_time = 3):


class holder():
	def __init__(self, state_in):
		self.latest_result = state_in
		self.det_stop = False
	# end def

	def run(self):
		

		while True:
			# check stopped
			if self.det_stop is True:
				break
			# end if
			thread = Thread(target=run_epoch, args=(start_state, output_data,))
			thread.start()
			thread.kill()
			self.latest_result = copy.copy(output_data)
			start_state = output_data
		# end while
	# end def

	def get


	return x
# end def

def run_epoch(input_data, output_data):

# end def


bg_runner = test()
bg_runner.run_inc() # spawn thread and run independently infinitely
bg_runner.harvest()



class test:
	def __init__(self):
		self.x = 0
		self.allowed_time


	def run_inc(self, allowed_time):
		t = threading.Thread(name='my_service', target=inc, args=())
		t.start()

	def harvest(self):
		
