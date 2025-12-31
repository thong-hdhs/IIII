"""Shared helpers and protocol for Mines game server/client.
Simple JSON line protocol: each message is a JSON object followed by a newline.
"""
import json

def send_msg(sock, obj):
    data = json.dumps(obj, separators=(',', ':')) + '\n'
    sock.sendall(data.encode('utf-8'))

def recv_msg(sock, timeout=None):
    # read until newline; uses socket timeout
    import socket
    buf = []
    sock.settimeout(timeout)
    try:
        while True:
            ch = sock.recv(1)
            if not ch:
                return None
            if ch == b'\n':
                break
            buf.append(ch)
    except socket.timeout:
        return None
    data = b''.join(buf).decode('utf-8')
    try:
        return json.loads(data)
    except Exception:
        return None
