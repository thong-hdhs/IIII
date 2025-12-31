"""Tkinter client for Mines 8x8 game.

Run: python client.py
"""
import socket
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import font as tkfont
from common import send_msg, recv_msg
import queue

HOST = '127.0.0.1'
PORT = 5000

class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Mines 8x8 Client')
        self.mode = tk.StringVar(value='survival')
        self.sock = None
        self.netq = queue.Queue()
        self.player_id = None
        self.create_menu()
        self.create_topbar()
        self.create_board()
        # disable all cells initially until connected/started
        self.clear_board()
        self.status = tk.Label(root, text='Not connected', anchor='w')
        self.status.pack(fill='x')
        self.turn_timer = None
        self.remaining = 0
        self.poll_net()
        # try auto-connect shortly after startup to improve UX
        try:
            self.root.after(100, self.connect)
        except Exception:
            pass

    def create_topbar(self):
        f = tk.Frame(self.root)
        f.pack(fill='x', pady=4)
        self.lbl_player = tk.Label(f, text='You: -', width=15)
        self.lbl_player.pack(side='left', padx=6)
        self.lbl_timer = tk.Label(f, text='Timer: -', width=12)
        self.lbl_timer.pack(side='left', padx=6)
        self.lbl_scores = tk.Label(f, text='Scores: [0,0]', width=20)
        self.lbl_scores.pack(side='left', padx=6)

        # simple icons (text) per player
        self.player_icons = {0: '⭐', 1: '🔷'}
        self.player_colors = {0: '#4da6ff', 1: '#66cc66'}


    def create_menu(self):
        men = tk.Menu(self.root)
        self.root.config(menu=men)
        game = tk.Menu(men, tearoff=False)
        men.add_cascade(label='Game', menu=game)
        game.add_command(label='Connect', command=self.connect)
        game.add_command(label='Play Again', command=self.play_again)
        game.add_command(label='Exit', command=self.root.quit)
        mode_menu = tk.Menu(men, tearoff=False)
        men.add_cascade(label='Mode', menu=mode_menu)
        mode_menu.add_radiobutton(label='Survival', variable=self.mode, value='survival')
        mode_menu.add_radiobutton(label='Scoring', variable=self.mode, value='scoring')

    def create_board(self):
        fr = tk.Frame(self.root)
        fr.pack(padx=6, pady=6)
        self.btns = [[None]*8 for _ in range(8)]
        self.btn_font = tkfont.Font(size=12, weight='bold')
        for r in range(8):
            for c in range(8):
                b = tk.Button(fr, text=' ', width=4, height=2, font=self.btn_font, command=lambda rr=r,cc=c: self.select(rr,cc))
                b.grid(row=r, column=c, padx=2, pady=2)
                self.btns[r][c] = b

    def connect(self):
        if self.sock:
            messagebox.showinfo('Info','Already connected')
            return
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            send_msg(s, {'type':'join','mode':self.mode.get()})
            self.sock = s
            threading.Thread(target=self.net_reader, daemon=True).start()
            self.status.config(text='Connected, waiting for opponent...')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def play_again(self):
        if self.sock:
            try:
                self.sock.close()
            except: pass
            self.sock = None
        self.clear_board()
        self.connect()

    def clear_board(self):
        for r in range(8):
            for c in range(8):
                b = self.btns[r][c]
                b.config(text=' ', state='disabled', bg='SystemButtonFace', fg='black')

    def net_reader(self):
        while self.sock:
            msg = recv_msg(self.sock, timeout=None)
            if msg is None:
                break
            self.netq.put(msg)
        self.netq.put({'type':'disconnect'})

    def poll_net(self):
        try:
            while True:
                msg = self.netq.get_nowait()
                self.handle_msg(msg)
        except queue.Empty:
            pass
        self.root.after(100, self.poll_net)

    def handle_msg(self, msg):
        t = msg.get('type')
        if t == 'start':
            self.player_id = msg.get('you')
            self.mode.set(msg.get('mode','survival'))
            self.status.config(text=f'Started as player {self.player_id} ({self.mode.get()})')
            self.clear_board()
            self.lbl_player.config(text=f'You: Player {self.player_id}')
            self.lbl_scores.config(text='Scores: [0,0]')
            for r in range(8):
                for c in range(8):
                    self.btns[r][c].config(state='disabled')
        elif t == 'turn':
            player = msg.get('player')
            if player == self.player_id:
                self.status.config(text='Your turn')
                for r in range(8):
                    for c in range(8):
                        if self.btns[r][c]['text'] == ' ':
                            self.btns[r][c].config(state='normal')
                self.start_countdown(10)
            else:
                self.status.config(text='Opponent turn')
                for r in range(8):
                    for c in range(8):
                        self.btns[r][c].config(state='disabled')
        elif t == 'update':
            for (r,c,p) in msg.get('selected',[]):
                self.mark_cell(r,c,p)
            scores = msg.get('scores')
            self.lbl_scores.config(text=f'Scores: {scores}')
            self.status.config(text=f'Scores updated')
        elif t == 'info':
            self.status.config(text=msg.get('msg',''))
        elif t == 'end':
            winner = msg.get('winner')
            reason = msg.get('reason')
            self.status.config(text=f'Game ended. Winner: {winner}. {reason}')
            # reveal mines if provided
            mines = msg.get('mines', [])
            # show explosion animation for each mine
            for (r,c) in mines:
                self.reveal_explosion(r, c)
            for r in range(8):
                for c in range(8):
                    self.btns[r][c].config(state='disabled')
            messagebox.showinfo('Game Over', f'Winner: {winner}\nReason: {reason}')
        elif t == 'disconnect':
            self.status.config(text='Disconnected from server')
            self.sock = None

    def mark_cell(self, r, c, player):
        b = self.btns[r][c]
        # show player icon in center and color cell
        icon = self.player_icons.get(player, '•')
        b.config(text=icon)
        b.config(state='disabled')
        # color depending on owner
        color = self.player_colors.get(player, 'lightgray')
        b.config(bg=color)
        b.config(fg='white')

    def reveal_explosion(self, r, c):
        # reveal the mine cell and animate neighbors briefly
        coords = [(r,c)] + [(r+dr,c+dc) for dr in (-1,0,1) for dc in (-1,0,1) if not (dr==0 and dc==0)]
        shown = []
        for (rr,cc) in coords:
            if 0 <= rr < 8 and 0 <= cc < 8:
                b = self.btns[rr][cc]
                # save original
                prev = (b['text'], b['bg'], b['fg'])
                shown.append(((rr,cc), prev))
                b.config(text='*' if (rr,cc)==(r,c) else b['text'], bg='orange' if (rr,cc)==(r,c) else '#ffcc99', fg='black')

        # after short delay, mark center as red and restore neighbors gradually
        def finalise():
            for (rr,cc), prev in shown:
                b = self.btns[rr][cc]
                if (rr,cc) == (r,c):
                    b.config(text='💥', bg='red', fg='white')
                else:
                    # keep neighbor highlighted but non-clickable
                    b.config(bg='#ffcc99', fg='black')

        self.root.after(300, finalise)

    def select(self, r, c):
        if not self.sock:
            return
        try:
            send_msg(self.sock, {'type':'select','r':r,'c':c})
        except Exception as e:
            messagebox.showerror('Error', str(e))

    def start_countdown(self, secs):
        self.remaining = secs
        self._tick()

    def _tick(self):
        if self.remaining <= 0:
            self.status.config(text='Time up')
            return
        self.status.config(text=f'Time left: {self.remaining}s')
        self.remaining -= 1
        self.root.after(1000, self._tick)

if __name__ == '__main__':
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()
