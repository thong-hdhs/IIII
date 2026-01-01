"""Network communication handler for Mines Arena client."""
import socket
import threading
import queue
from common import send_msg, recv_msg


class NetworkHandler:
    """Manages socket communication with the server."""
    
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.sock = None
        self.netq = queue.Queue()
        self.reader_thread = None
    
    def connect(self, mode):
        """Connect to server and send join message."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            send_msg(s, {'type': 'join', 'mode': mode})
            self.sock = s
            # Start reader thread in background
            self.reader_thread = threading.Thread(target=self._net_reader, daemon=True)
            self.reader_thread.start()
            return True
        except Exception as e:
            self.sock = None
            raise e
    
    def disconnect(self):
        """Close socket connection."""
        if self.sock:
            try:
                send_msg(self.sock, {'type': 'leave'})
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
    
    def send_select(self, r, c):
        """Send a cell selection to server."""
        if not self.sock:
            return False
        try:
            send_msg(self.sock, {'type': 'select', 'r': r, 'c': c})
            return True
        except Exception:
            return False
    
    def send_leave(self):
        """Send leave message to server."""
        if not self.sock:
            return False
        try:
            send_msg(self.sock, {'type': 'leave'})
            return True
        except Exception:
            return False
    
    def poll_messages(self):
        """Get all pending messages from queue (non-blocking)."""
        messages = []
        try:
            while True:
                msg = self.netq.get_nowait()
                messages.append(msg)
        except queue.Empty:
            pass
        return messages
    
    def _net_reader(self):
        """Background thread: read messages from socket and queue them."""
        while self.sock:
            msg = recv_msg(self.sock, timeout=None)
            if msg is None:
                break
            self.netq.put(msg)
        # Signal disconnect
        self.netq.put({'type': 'disconnect'})
