import yaml
import argparse
from socket import *
from socketIO_client import SocketIO
from socketIO_client import SocketIO, BaseNamespace
from multiprocessing import Pool, Process

import _pickle as pickle
import logging
import logging.handlers
import socketserver
import struct


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
	def handle(self):
		while 1:
			chunk = self.connection.recv(4)
			if len(chunk) < 4:
				break
			slen = struct.unpack(">L", chunk)[0]
			chunk = self.connection.recv(slen)
			while len(chunk) < slen:
				chunk = chunk + self.connection.recv(slen - len(chunk))
			obj = self.unPickle(chunk)
			record = logging.makeLogRecord(obj)
			self.handleLogRecord(record)

	def unPickle(self, data):
		return pickle.loads(data)

	def handleLogRecord(self, record):
		self.sio.emit(self.tgt_event, record.msg)
	# end def
# end class

class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):

	allow_reuse_address = 1

	def __init__(self, host, port, 
				 handler=LogRecordStreamHandler):
		self.abort = 0
		self.timeout = 1
		self.logname = None
		self.handler = handler
		self.listen_host = host
		self.listen_port = port

	def initialize(self, event, host, port, namespace):
		sio_base = SocketIO(host, port)
		sio = sio_base.define(BaseNamespace, '/'+namespace)

		self.handler.sio = sio
		self.handler.tgt_event = event
		socketserver.ThreadingTCPServer.__init__(self, (self.listen_host, self.listen_port), self.handler)
	# end def


	def serve_until_stopped(self):
		import select
		abort = 0
		while not abort:
			rd, wr, ex = select.select([self.socket.fileno()],
									   [], [],
									   self.timeout)
			if rd:
				self.handle_request()
			abort = self.abort
# end class


# _from = (host, port, buf)
# _to   = (host, port, namespace, event)
def relay_message(input_data):
	key, _from, _to = input_data
	print("relaying %s to %s (I)" % (_from, _to,))

	# listening port
	(host, port, buf) = map(_from.get, ['host', 'port', 'buf'])
	addr = (host, port)
	UDPSock = socket(AF_INET, SOCK_DGRAM)
	UDPSock.bind(addr)

	# targeting port
	(host, port, namespace, event) = map(_to.get, ['host', 'port', 'namespace', 'event'])
	sio_base = SocketIO(host, port)
	sio = sio_base.define(BaseNamespace, '/'+namespace)

	# watch
	while True:
		(data, addr) = UDPSock.recvfrom(buf)
		print('%s activated' % (key,))
		sio.emit(event, str(data, 'utf-8'))
	# end while
# end def

def relay_log(input_data):
	key, _from, _to = input_data
	print("relaying %s to %s (II)" % (_from, _to,))

	# listening port
	(host, port, buf) = map(_from.get, ['host', 'port', 'buf'])
	tcpserver = LogRecordSocketReceiver(host, port)

	(host, port, namespace, event) = map(_to.get, ['host', 'port', 'namespace', 'event'])
	tcpserver.initialize(event, host, port, namespace)

	tcpserver.serve_until_stopped()
# end def


# parse inputs
parser = argparse.ArgumentParser(description='Relay messages between sockets')
parser.add_argument('--input', help="input file (.yaml)", type=str, required=True)
pars = vars(parser.parse_args())
pairs_inputfile = pars['input']

# read input
with open(pairs_inputfile, 'rb') as fin:
	inputs = yaml.load(fin)
# end with

input_pairs_I  = []
input_pairs_II = []

for key, val in inputs.items():
	if   val['type'] == 'I':
		input_pairs_I .append([key, val['source'], val['dest']])
	elif val['type'] == 'II':
		input_pairs_II.append([key, val['source'], val['dest']])
	# end if
# end for


##############################
########### TYPE I ###########
##############################
for input_pair in input_pairs_I:
	Process(target=relay_message, args=(input_pair,)).start()
# end for 
##############################
##############################


##############################
########## TYPE II ###########
##############################
for input_pair in input_pairs_II:
	Process(target=relay_log, args=(input_pair,)).start()
# end for 
##############################
##############################

