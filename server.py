"""Multiclient server for 8x8 Mines game

Run: python server.py
"""
import socket
import select
import threading
import random
import time
from common import send_msg, recv_msg
import datetime

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
        mine_count = random.choice([2, 3, 4])  # Random 2-4 mines
        for _ in range(mine_count):
            while True:
                r = random.randrange(8)
                c = random.randrange(8)
                if (r,c) not in self.mines:
                    self.mines.add((r,c))
                    break
        self.mines_hit = set()  # Track which mines have been hit
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
            cur_sock = self.socks[cur]
            other_sock = self.socks[other]
            
            # inform whose turn
            for i,s in enumerate(self.socks):
                try:
                    server_time = time.time()
                    send_msg(s, {'type':'turn','player':cur,'time':10,'server_time':server_time,'board':self._board_view(i)})
                except Exception:
                    self._end_due_to_disconnect(i); return

            # Use select to listen to BOTH sockets for 10 seconds
            # This allows us to receive 'leave' messages from either player
            req = None
            start_time = time.time()
            while time.time() - start_time < 10.0 and req is None:
                timeout = 10.0 - (time.time() - start_time)
                readable, _, _ = select.select([cur_sock, other_sock], [], [], max(0, timeout))
                
                if readable:
                    # Check which socket has data
                    if cur_sock in readable:
                        req = recv_msg(cur_sock, timeout=0.1)
                        if req and req.get('type') == 'leave':
                            # Current player sent leave
                            self._end_due_to_disconnect(cur, reason='opponent_quit')
                            return
                    if other_sock in readable and req is None:
                        msg = recv_msg(other_sock, timeout=0.1)
                        if msg and msg.get('type') == 'leave':
                            # Other player left while waiting
                            self._end_due_to_disconnect(other, reason='opponent_quit')
                            return

            if req is None:
                # timeout or disconnect
                if self.mode == 'survival':
                    # opponent wins
                    self._send_end(winner=other, reason='timeout')
                    return
                else:
                    # scoring: skip turn
                    self.turn = other
                    for s in self.socks:
                        try:
                            send_msg(s, {'type':'info','msg':'player %d timeout, turn passed' % cur})
                        except Exception:
                            # Opponent disconnected
                            self._end_due_to_disconnect(cur, reason='opponent_quit')
                            return
                    continue

            if req.get('type') == 'leave':
                # Player left the game - opponent wins
                self._end_due_to_disconnect(cur, reason='opponent_quit')
                return

            if req.get('type') == 'select':
                r = int(req.get('r'))
                c = int(req.get('c'))
                if (r,c) in self.selected:
                    send_msg(sock, {'type':'error','msg':'cell already chosen'})
                    continue
                self.selected[(r,c)] = cur
                if (r,c) in self.mines:
                    # Mine hit - show explosion immediately to all players
                    # Send mine_hit message so clients show explosion right away
                    for i, s in enumerate(self.socks):
                        try:
                            send_msg(s, {'type': 'mine_hit', 'r': r, 'c': c})
                        except Exception:
                            pass
                    
                    self.mines_hit.add((r,c))
                    if self.mode == 'scoring':
                        self.scores[cur] -= 1
                    
                    # Survival mode: end game immediately on first mine hit
                    if self.mode == 'survival':
                        winner = other
                        reason = 'mine'
                        self._send_end(winner=winner, reason=reason)
                        return
                    else:
                        # Scoring mode: continue until all mines are hit
                        if len(self.mines_hit) == len(self.mines):
                            # All mines hit - determine winner by score
                            if self.scores[0] > self.scores[1]:
                                winner = 0
                            elif self.scores[1] > self.scores[0]:
                                winner = 1
                            else:
                                winner = -1  # Tie
                            reason = 'all_mines_hit'
                            self._send_end(winner=winner, reason=reason)
                            return
                        # Continue turn in scoring mode if not all mines hit yet
                else:
                    # safe: add point
                    if self.mode == 'scoring':
                        self.scores[cur] += 1

                # continue or switch
                self.turn = other
                # broadcast update
                for i,s in enumerate(self.socks):
                    send_msg(s, {'type':'update','selected':[(k[0],k[1],v) for k,v in self.selected.items()], 'scores':self.scores})

                # If all cells chosen or other end condition, end
                if len(self.selected) >= 64:
                    if self.scores[0] > self.scores[1]:
                        winner = 0
                    elif self.scores[1] > self.scores[0]:
                        winner = 1
                    else:
                        winner = -1  # Tie
                    self._send_end(winner=winner, reason='board_full')
                    return

    def _board_view(self, viewer):
        # hide mines; only show selected cells and scores
        return {'selected':[(r,c,p) for (r,c),p in self.selected.items()], 'scores':self.scores}

    def _send_end(self, winner=None, loser=None, reason=''):
        for i,s in enumerate(self.socks):
            try:
                # In survival mode, don't send scores; in scoring mode, send them
                scores = self.scores if self.mode == 'scoring' else [0, 0]
                # Send only hit mines (mines_hit) to show as red, not all mines
                send_msg(s, {'type':'end','winner':winner,'loser':loser,'reason':reason,'scores':scores,'selected':[(k[0],k[1],v) for k,v in self.selected.items()], 'mines': [[r,c] for (r,c) in self.mines_hit]})
            except Exception:
                pass
        # Wait a bit for clients to read the end message before closing sockets
        time.sleep(0.3)
        self.running = False
        self._close_all()

    def _end_due_to_disconnect(self, idx, reason='opponent_quit'):
        other = 1-idx
        # Use _send_end to send proper end message with all data to both players
        self._send_end(winner=other, reason=reason)

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
