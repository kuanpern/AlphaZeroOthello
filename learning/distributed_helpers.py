import os
import torch
import torch.distributed

def average_gradients(model):
	size = float(torch.distributed.get_world_size())
	for param in model.parameters():
		torch.distributed.all_reduce(param.grad.data, op=torch.distributed.reduce_op.SUM)
		param.grad.data /= size
	# end
# end def

class Partition():
	def __init__(self, data, index):
		self.data = data
		self.index = index
	# end def

	def __len__(self):
		return len(self.index)
	# end def

	def __getitem__(self, index):
		data_idx = self.index[index]
		return self.data[data_idx]
	# end def
# end class


class DataPartitioner():

	def __init__(self, data, sizes):
		self.data = data
		self.partitions = []
		data_len = len(data)
		indexes = [x for x in range(0, data_len)]

		for frac in sizes:
			part_len = int(frac * data_len)
			self.partitions.append(indexes[0:part_len])
			indexes = indexes[part_len:]
		# end for
	# end def

	def use(self, partition):
		return Partition(self.data, self.partitions[partition])
	# end def
# end class

def partition_dataset(dataset, partition_sizes):
	partition = DataPartitioner(dataset, partition_sizes)
	partition = partition.use(torch.distributed.get_rank())
	return partition
# end def


def init_processes(host, port, rank, size, fn, backend='tcp'):
	os.environ['MASTER_ADDR'] = host
	os.environ['MASTER_PORT'] = str(port) # strange design
	torch.distributed.init_process_group(backend, rank=rank, world_size=size)
	fn(rank, size)
# end def
