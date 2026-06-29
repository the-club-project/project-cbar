import zmq
import json

context = zmq.Context()
subs = context.socket(zmq.SUB)
ipc_path = "ipc:///tmp/clio_bridge.ipc"
subs.connect(ipc_path)
subs.setsockopt_string(zmq.SUBSCRIBE, "")

res = context.socket(zmq.REQ)
res_path = "ipc:///tmp/clio_bridge_res.ipc"
res.connect(res_path)

def get_info():
    payload_data = subs.recv()
    data = json.loads(payload_data.decode('utf-8'))
    return data

def send_cmd(action):
    payload = json.dumps(action)
    res.send_string(payload)
    reply = res.recv_string()
    print(reply)