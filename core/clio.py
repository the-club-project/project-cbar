import zmq
import struct

context = zmq.Context()
subs = context.socket(zmq.SUB)