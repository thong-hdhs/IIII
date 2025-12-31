"""Multiclient server for 8x8 Mines game

Run: python server.py
"""
import socket
import threading
import random
import time
from common import send_msg, recv_msg

HOST = '0.0.0.0'
PORT = 5000

class MatchMaker:
    def __init__(self):
        self.lock = threading.Lock()
        self.queues = {'survival': [], 'scoring': []}

    def join(self, client_sock, mode):
        with self.lock:
            q = self.queues.setdefault(mode, [])
            q.append(client_sock)
            if len(q) >= 2:
                a = q.pop(0)
                b = q.pop(0)
                session = GameSession(a, b, mode)
                session.start()

class GameSession(threading.Thread):
    def __init__(self, sock_a, sock_b, mode):
        super().__init__(daemon=True)
        self.socks = [sock_a, sock_b]
        self.mode = mode
        self.board = [[0]*8 for _ in range(8)]
        self.mines = set()
        for _ in range(random.choice([2,3])):
            while True:
                r = random.randrange(8)
                c = random.randrange(8)
                if (r,c) not in self.mines:
                    self.mines.add((r,c))
                    break
        self.selected = {}  # (r,c) -> player
        self.scores = [0,0]
        self.turn = 0
        self.running = True

    def run(self):
        # send start
        for i,sock in enumerate(self.socks):
            try:
                send_msg(sock, {'type':'start','you':i,'mode':self.mode})
            except Exception:
                self._close_all(); return

        while self.running:
            cur = self.turn
            other = 1-cur
            sock = self.socks[cur]
            # inform whose turn
            for i,s in enumerate(self.socks):
                try:
                    send_msg(s, {'type':'turn','player':cur,'time':10,'board':self._board_view(i)})
                except Exception:
                    self._end_due_to_disconnect(i); return

            # wait for move up to 10s
            req = None
            try:
                req = recv_msg(sock, timeout=10.0)
            except Exception:
                req = None

            if req is None:
                # timeout
                if self.mode == 'survival':
                    # opponent wins
                    self._send_end(winner=other, reason='timeout')
                    return
                else:
                    # scoring: skip turn
                    self.turn = other
                    for s in self.socks:
                        send_msg(s, {'type':'info','msg':'player %d timeout, turn passed' % cur})
                    continue

            if req.get('type') == 'select':
                r = int(req.get('r'))
                c = int(req.get('c'))
                if (r,c) in self.selected:
                    send_msg(sock, {'type':'error','msg':'cell already chosen'})
                    continue
                self.selected[(r,c)] = cur
                if (r,c) in self.mines:
                    if self.mode == 'survival':
                        # immediate loss
                        self._send_end(winner=other, loser=cur, reason='mine')
                        return
                    else:
                        # scoring: subtract point
                        self.scores[cur] -= 1
                else:
                    # safe: add point
                    self.scores[cur] += 1

                # continue or switch
                self.turn = other
                # broadcast update
                for i,s in enumerate(self.socks):
                    send_msg(s, {'type':'update','selected':[(k[0],k[1],v) for k,v in self.selected.items()], 'scores':self.scores})

                # If all cells chosen or other end condition, end
                if len(self.selected) >= 64:
                    winner = 0 if self.scores[0] > self.scores[1] else 1
                    self._send_end(winner=winner, reason='board_full')
                    return

    def _board_view(self, viewer):
        # hide mines; only show selected cells and scores
        return {'selected':[(r,c,p) for (r,c),p in self.selected.items()], 'scores':self.scores}

    def _send_end(self, winner=None, loser=None, reason=''):
        for i,s in enumerate(self.socks):
            try:
                send_msg(s, {'type':'end','winner':winner,'loser':loser,'reason':reason,'scores':self.scores,'selected':[(k[0],k[1],v) for k,v in self.selected.items()], 'mines': [[r,c] for (r,c) in self.mines]})
            except Exception:
                pass
        self.running = False
        self._close_all()

    def _end_due_to_disconnect(self, idx):
        other = 1-idx
        try:
            send_msg(self.socks[other], {'type':'end','winner':other,'reason':'opponent_disconnect'})
        except Exception:
            pass
        self._close_all()

    def _close_all(self):
        for s in self.socks:
            try:
                s.close()
            except Exception:
                pass

def handle_client(conn, addr, mm):
    try:
        msg = recv_msg(conn, timeout=30.0)
        if not msg:
            conn.close(); return
        if msg.get('type') == 'join':
            mode = msg.get('mode','survival')
            mm.join(conn, mode)
        else:
            conn.close()
    except Exception:
        try: conn.close()
        except: pass

def main():
    mm = MatchMaker()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print('Server listening on %s:%d' % (HOST, PORT))
    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr, mm), daemon=True).start()
    finally:
        s.close()

if __name__ == '__main__':
    main()
