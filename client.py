"""Mines 8x8 Client - Refactored with modular architecture.

Modules:
- ui_renderer.py: Screen rendering and UI components
- network_handler.py: Socket communication and message handling
- client.py: Main game orchestrator

Run: python client.py
"""
import tkinter as tk
from tkinter import messagebox
import time
from ui_renderer import UIRenderer, NeonColors
from network_handler import NetworkHandler


class NeonMinesGame:
    """Main game controller orchestrating UI, network, and game logic."""
    
    def __init__(self, root):
        self.root = root
        self.root.title('MINES ARENA')
        self.root.geometry('760x640')
        self.root.config(bg=NeonColors.BG_PRIMARY)
        self.root.resizable(False, False)
        
        # Game state
        self.mode = tk.StringVar(value='survival')
        self.player_id = None
        self.current_screen = None
        self.remaining_time = 10
        self.server_start_time = None
        self.is_game_ended = False
        
        # UI and Network
        self.main_frame = tk.Frame(self.root, bg=NeonColors.BG_PRIMARY)
        self.main_frame.pack(fill='both', expand=True)
        
        self.ui = UIRenderer(self.main_frame, NeonColors())
        self.net = NetworkHandler()
        
        # Persistent exit button
        self.global_exit_btn = tk.Button(self.root, text='✕',
                                         bg=NeonColors.NEON_PINK, fg=NeonColors.BG_PRIMARY,
                                         font=('Arial', 9, 'bold'),
                                         command=self.leave_game,
                                         relief='solid', bd=1, cursor='hand2',
                                         width=3, height=1)
        self.global_exit_btn.place(relx=0.985, rely=0.02, anchor='ne')

        self.show_menu_screen()
        self.poll_net()
    
    def leave_game(self):
        """Exit game session and return to menu."""
        self.net.disconnect()
        self.show_menu_screen()
    
    def show_menu_screen(self):
        """Display main menu."""
        self.current_screen = 'menu'
        self.ui.show_menu_screen(
            on_survival=lambda: self.start_game('survival'),
            on_scoring=lambda: self.start_game('scoring'),
            on_exit=self.root.quit
        )
    
    def start_game(self, mode):
        """Connect to server and start game in chosen mode."""
        self.mode.set(mode)
        self.is_game_ended = False
        
        try:
            self.net.connect(mode)
            self.show_game_screen()
        except Exception as e:
            messagebox.showerror('Connection Error', str(e))
            self.show_menu_screen()
    
    def show_game_screen(self):
        """Display game board."""
        self.current_screen = 'game'
        self.ui.show_game_screen()
        self.ui.set_board_callback(self.select_cell)
    
    def select_cell(self, r, c):
        """Handle cell click."""
        if self.net.send_select(r, c):
            return
        messagebox.showerror('Error', 'Failed to send move.')
    
    def show_end_screen(self, result, reason):
        """Display game end screen."""
        self.current_screen = 'end'
        self.ui.show_end_screen(
            result, reason, self.mode.get(),
            on_play_again=lambda: self.start_game(self.mode.get()),
            on_back_menu=self.show_menu_screen
        )
    
    def poll_net(self):
        """Poll network queue and process messages."""
        for msg in self.net.poll_messages():
            self.handle_msg(msg)
        self.root.after(100, self.poll_net)
    
    def handle_msg(self, msg):
        """Process messages from server."""
        msg_type = msg.get('type')
        
        if msg_type == 'start':
            self.player_id = msg.get('you')
            self.is_game_ended = False
        
        elif msg_type == 'turn':
            player = msg.get('player')
            server_time = msg.get('server_time')
            
            if server_time:
                self.server_start_time = server_time
            
            my_turn = (player == self.player_id)
            self.ui.enable_board_for_player(my_turn)
            
            if my_turn:
                self.start_countdown_server(self.server_start_time or time.time())
        
        elif msg_type == 'update':
            for (r, c, p) in msg.get('selected', []):
                self.ui.mark_cell(r, c, p)
        
        elif msg_type == 'end':
            self.is_game_ended = True
            winner = msg.get('winner')
            reason = msg.get('reason')
            
            # Reveal mines
            mines = msg.get('mines', [])
            for (r, c) in mines:
                self.ui.reveal_explosion(r, c, self.root)
            
            self.ui.disable_board()
            
            result = 'win' if (winner == self.player_id) else 'lose'
            self.root.after(500, lambda: self.show_end_screen(result, reason))
        
        elif msg_type == 'disconnect':
            if self.current_screen == 'game' and not self.is_game_ended:
                messagebox.showerror('Disconnected', 'Lost connection to server')
            self.net.sock = None
    
    def start_countdown_server(self, server_time):
        """Start countdown using server timestamp."""
        self.server_start_time = server_time
        self._tick_server()
    
    def _tick_server(self):
        """Update timer based on server time."""
        if not self.server_start_time or not self.ui.timer_label:
            return
        
        elapsed = time.time() - self.server_start_time
        remaining = max(0, 10 - int(elapsed))
        self.ui.timer_label.config(text=f'⏱ {remaining}s')
        
        if remaining > 0:
            self.root.after(500, self._tick_server)


if __name__ == '__main__':
    root = tk.Tk()
    app = NeonMinesGame(root)
    root.mainloop()
