import zmq
import json

context = zmq.Context()
subs = context.socket(zmq.SUB)
ipc_path = "ipc:///tmp/hypr_bridge.ipc"

subs.connect(ipc_path)
subs.setsockopt_string(zmq.SUBSCRIBE, "")

def get_info():
    payload_data = subs.recv()
    data = json.loads(payload_data.decode('utf-8'))
    return data