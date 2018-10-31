import os
import sys
import time
import uuid
import json
import dill
import numpy as np
import glob
import random
import itertools
import argparse
import torch
import torch.nn
import torch.optim
import torch.distributed
from torch.multiprocessing import Process as torch_Process
from distributed_helpers import *

import logging
_handler = logging.StreamHandler(sys.stdout)
_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
_handler.setFormatter(formatter)
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)
rootLogger.addHandler(_handler)
##########################
#### HYPERPARAMETERS #####
##########################
# idiosyncratic
BOARD_SIZE     = 8

# architecture
IN_CHANNEL     = 7
FILTER_SIZE_0  = 36
KERNEL_SIZE    = (2, 2)
STRIDE         = (1, 1)
TOWER_HEIGHT   = 4
FILTER_SIZE_m1 = 36
FILTER_SIZE_m2 = 36
FC_SIZE        = 25

# learning
LEARNING_RATE = 0.001
MOMENTUM      = 0.9
BATCH_SIZE    = 200
EPOCH_N       = 10
##########################
##########################


##########################
## NETWORK ARCHITECTURE ##
##########################
class Net(torch.nn.Module):
	def __init__(self):
		super(Net, self).__init__()
		
		# N-0
		self.n0_conv        = torch.nn.Conv2d(in_channels=IN_CHANNEL, out_channels=FILTER_SIZE_0, kernel_size=KERNEL_SIZE, stride=STRIDE)
		self.n0_batch_norm  = torch.nn.BatchNorm2d(FILTER_SIZE_0)
		self.n0_ReLu        = torch.nn.ReLU()		
		
		# N-mid
		self.nm_batch_norm0 = torch.nn.BatchNorm2d(FILTER_SIZE_0)
		self.nm_conv1       = torch.nn.Conv2d(in_channels=FILTER_SIZE_0,  out_channels=FILTER_SIZE_m1, kernel_size=KERNEL_SIZE, stride=STRIDE)
		self.nm_batch_norm1 = torch.nn.BatchNorm2d(FILTER_SIZE_m1)
		self.nm_ReLu        = torch.nn.ReLU()
		self.nm_conv2       = torch.nn.Conv2d(in_channels=FILTER_SIZE_m1, out_channels=FILTER_SIZE_m2, kernel_size=KERNEL_SIZE, stride=STRIDE)
		self.nm_batch_norm2 = torch.nn.BatchNorm2d(FILTER_SIZE_m2)
		self.nm_upsample    = torch.nn.ConvTranspose2d((BOARD_SIZE-2)**2, (BOARD_SIZE-2)**2, kernel_size=3)

		# N-end (policy)
		self.np_conv        = torch.nn.Conv2d(in_channels=FILTER_SIZE_0, out_channels=2, kernel_size=(1, 1), stride=STRIDE)
		self.np_batch_norm  = torch.nn.BatchNorm2d(2)
		self.np_fc          = torch.nn.Linear(2*(BOARD_SIZE-1)**2, BOARD_SIZE*BOARD_SIZE) # note: Othello doesn't allow passing voluntarily
		self.np_softmax     = torch.nn.Softmax(dim=1)
		
		# N-end (value)		
		self.nv_conv        = torch.nn.Conv2d(in_channels=FILTER_SIZE_0, out_channels=1, kernel_size=(1, 1), stride=STRIDE)
		self.nv_batch_norm  = torch.nn.BatchNorm2d(1)
		self.nv_ReLu1       = torch.nn.ReLU()
		self.nv_fc1         = torch.nn.Linear((BOARD_SIZE-1)**2, FC_SIZE)
		self.nv_ReLu2       = torch.nn.ReLU()
		self.nv_fc2         = torch.nn.Linear(FC_SIZE, 1)
		self.nv_tanh        = torch.nn.Tanh()
	# end def
	
	def forward(self, x):
		out = self.n0_forward(x)
		for height in range(TOWER_HEIGHT):
			out = self.nm_forward(out)
		# end dfor
		
		out_p = self.np_forward(out) # policy
		out_v = self.nv_forward(out) # value
		
		out_vec = torch.cat([out_p, out_v], 1)
		return out_vec
	# end def
	
	# first, single convolutional block
	def n0_forward(self, x):
		out = self.n0_conv(x)
		out = self.n0_batch_norm(out)
		out = self.n0_ReLu(out)
		return out
	# end def
	
	
	# ResNet (building block of tower)
	def nm_forward(self, x):
		shortcut = x
		
		out = self.nm_conv1(x)
		out = self.nm_batch_norm1(out)
		out = self.nm_ReLu(out)
		out = self.nm_conv2(out)
		out = self.nm_batch_norm2(out)
		
		# skip connection
		out = self.nm_upsample(out)
		out = self.nm_batch_norm0(out)
		out = out + shortcut

		out = self.nm_ReLu(out)
		return out
	# end def

	def np_forward(self, x):
		out = self.np_conv(x)
		out = self.np_batch_norm(out)
		out = out.view(-1, 2 * IN_CHANNEL * IN_CHANNEL)
		out = self.np_fc(out)
		out = self.np_softmax(out) # <- this is added in this implemenation - unsure how would FC gives a logit as described in paper ...
		return out
	# end def
	
	def nv_forward(self, x):
		out = self.nv_conv(x)
		out = self.nv_batch_norm(out)
		out = self.nv_ReLu1(out)
		out = out.view(-1, 1 * IN_CHANNEL * IN_CHANNEL)
		out = self.nv_fc1(out)
		out = self.nv_ReLu2(out)
		out = self.nv_fc2(out)
		out = self.nv_tanh(out)
		return out
	# end def
# end class


##################################################
### Customized loss function of Zero algorithm ###
##################################################
class AlphaZERO_Loss(torch.nn.Module):
	def __init__(self):
		super(AlphaZERO_Loss,self).__init__()
	# end def
		
	def forward(self, outputs, labels):
		# get the batch size
		batch_n = outputs.shape[0]

		move_probs, pred_vals = torch.split(outputs, [BOARD_SIZE**2, 1], 1)
		search_probs, winners = torch.split(labels , [BOARD_SIZE**2, 1], 1)

		# compute the loss function
		pi  = search_probs.contiguous().view(-1).float()
		logp = torch.log(move_probs).contiguous().view(-1).float()

		loss = torch.pow(pred_vals - winners, 2).sum() - pi.dot(logp)
		loss = loss / batch_n

		return loss
	# end def
# end class
##################################################
##################################################


##################################################
######### Define network and optimizer ###########
##################################################
criterion = AlphaZERO_Loss()
##################################################
##################################################



# parse inputs
parser = argparse.ArgumentParser(description='Othello DeepLearning Training')
parser.add_argument('--host',      help="hostname", type=str, required=True)
parser.add_argument('--port',      help="port",     type=int, required=True)
parser.add_argument('--worldsize', help="number of processes to run", type=int, required=True)
parser.add_argument('--inputNet',  help="input network model (.dill)", type=str, required=False, default=None)
parser.add_argument('--inputdir',  help="input directory",   type=str, required=True)
parser.add_argument('--outroot',   help="output model name", type=str, required=True)
parser.add_argument('--outdir' ,   help="output directory",  type=str, required=True)
parser.add_argument('--interval',  help="Interval (in seconds) to save a model snapshot", type=int, default=3600)
parser.add_argument('--infile_N',  help="number of files taken each time", type=int, default=100)
parser.add_argument('--backend',   help="backend", choices=("tcp", "mpi"), default="tcp")
pars = vars(parser.parse_args())

inputdir   = pars['inputdir']
infile_N   = pars['infile_N']
outroot    = pars['outroot']
outdir     = pars['outdir']
interval   = pars['interval']
inputNet   = pars['inputNet']
world_size = pars['worldsize']
host       = pars['host']
port       = pars['port']
backend    = pars['backend']

def run(rank, size):
	torch.manual_seed(random.randint(0, 9999))

	# START
	# -- initialize model
	if inputNet is None:
		net = Net()
	else: # start from previous model
		with open(inputNet, 'rb') as fin:
			net = dill.load(fin)['net']
		# end with
	# end if
	# -- initialize optimizer
	rootLogger.info(' - initialize optimizer')
	optimizer = torch.optim.SGD(net.parameters(), lr=LEARNING_RATE, momentum=MOMENTUM)

	stime = time.time()
	while True:

		rootLogger.info(' - selecting data sets for training')
		input_data = []
		# select input files from directory randomly
		files = glob.glob(inputdir+'/*.json')
		sel_files = []
		for i in range(infile_N):
			sel_file = random.choice(files)
			with open(sel_file, 'r') as fin:
				_input_data = json.load(fin)
				input_data.extend(_input_data)
			# end with
		# end for

		# partition and select the data set
		# - use equal partition here
		rootLogger.info(' - partition and distributing data')
		n = torch.distributed.get_world_size()
		fracs = [1.0/n] * n 
		input_data = partition_dataset(input_data, fracs)


		n = len(input_data) / BATCH_SIZE * EPOCH_N
		input_data = itertools.cycle(input_data)

		rootLogger.info(' - start training')
		running_loss = 0.0
		_iter = 0
		while True:
			_iter += 1
			if _iter > n:
				break
			# end if

			inputs, labels = [[], []]
			for i in range(BATCH_SIZE):
				item = next(input_data)
				inputs.append(item[ 'input'])
				labels.append(item['target'])
			# end for
			inputs = torch.from_numpy(np.array(inputs)).float()
			labels = torch.from_numpy(np.array(labels)).float()

			# zero the parameter gradients
			optimizer.zero_grad()

			# forward + backward + optimize
			outputs = net(inputs)
			loss = criterion(outputs, labels)
			loss.backward()
			average_gradients(net)
			optimizer.step()

			# print statistics
			running_loss += loss.item()
			if _iter % 10 == 0:	# print every 500 mini-batches
				rootLogger.info('[node %d] [iteration %d] loss: %.3f' % (torch.distributed.get_rank(), _iter, running_loss / 500))
				running_loss = 0.0
			# end if
		# end for

		curtime = int(time.time())
		if curtime - stime >= interval:
			# save to file
			output = {
				'uuid': str(uuid.uuid4()),
				'timestamp': curtime,
				'net': net
			} # end output
			outfilename = outdir+'/'+outroot+'.'+str(curtime)+'-'+str(torch.distributed.get_rank())+'.dill'
			with open(outfilename, 'wb') as fout:
				dill.dump(output, fout)
			# end with
			rootLogger.info(' save model snapshot to: %s' % (outfilename,))

			stime = curtime
		# end if
	# end while
# end def


# MAIN #
processes = []
for rank in range(world_size):
	p = torch_Process(target=init_processes, args=(host, port, rank, world_size, run, backend))
	p.start()
	processes.append(p)
# end for

for p in processes:
	p.join()
# end for

