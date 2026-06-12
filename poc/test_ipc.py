import zmq
import struct

context = zmq.Context()
subscriber = context.socket(zmq.SUB)

# Connect to the exact same IPC file
subscriber.connect("ipc:///tmp/hypr_bridge.ipc")
subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

print("Python Receiver Active. Listening for Battery metrics...")

# The format blueprint
# '<'   = Little-endian
# 'B'   = 1-byte unsigned char (0-255, perfect for percentage)
# '15s' = 15-byte string array
format_string = "<Bc"

while True:
    payload = subscriber.recv()
    
    # Instantly unpack the bytes back into Python variables
    battery_pct, raw_status_bytes = struct.unpack(format_string, payload)
    
    # Decode the raw bytes into UTF-8 text and strip the invisible null padding (\x00)
    status_text = raw_status_bytes.decode('utf-8').strip('\x00')
    
    print(f"Battery: {battery_pct}% | Status: {status_text}")