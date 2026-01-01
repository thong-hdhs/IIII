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
import os
from ui_renderer import UIRenderer, NeonColors
from network_handler import NetworkHandler
from sound import SoundManager


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
        self.last_scores = [0, 0]
        
        # UI and Network
        self.main_frame = tk.Frame(self.root, bg=NeonColors.BG_PRIMARY)
        self.main_frame.pack(fill='both', expand=True)
        
        self.ui = UIRenderer(self.main_frame, NeonColors())
        self.net = NetworkHandler()
        # Sound manager (preload expected asset names)
        try:
            self.sound = SoundManager(volume=0.6)
            def _asset(*parts):
                return os.path.join(*parts)
            self.sound.preload_effect('click', _asset('assets', 'sfx', 'click.wav'))
            self.sound.preload_effect('explosion', _asset('assets', 'sfx', 'explosion.wav'))
            self.sound.preload_effect('win', _asset('assets', 'sfx', 'win.wav'))
            self.sound.preload_effect('lose', _asset('assets', 'sfx', 'lose.wav'))
        except Exception:
            self.sound = None

        self.show_menu_screen()
        self.poll_net()
    
    def leave_game(self):
        """Exit game session and return to menu."""
        # Send leave message to server first
        if self.current_screen == 'game':
            self.net.send_leave()
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
        mode = self.mode.get()
        self.ui.show_game_screen(mode=mode, on_leave=self.leave_game)
        self.ui.set_board_callback(self.select_cell)
    
    def select_cell(self, r, c):
        """Handle cell click."""
        # play click sound
        try:
            if self.sound:
                self.sound.play_effect('click')
        except Exception:
            pass

        if self.net.send_select(r, c):
            return
        messagebox.showerror('Error', 'Failed to send move.')
    
    def show_end_screen(self, result, reason):
        """Display game end screen."""
        self.current_screen = 'end'
        # play result sound
        try:
            if self.sound:
                if result == 'win':
                    self.sound.play_effect('win')
                elif result == 'lose':
                    self.sound.play_effect('lose')
        except Exception:
            pass

        self.ui.show_end_screen(
            result, reason, self.mode.get(), self.last_scores,
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
            scores = msg.get('scores', [0, 0])
            self.last_scores = scores
            self.ui.update_scores(scores)
        
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
            scores = msg.get('scores', [0, 0])
            self.last_scores = scores
            self.ui.update_scores(scores)
        
        elif msg_type == 'mine_hit':
            # Show explosion immediately when mine is hit (before end message)
            r = msg.get('r')
            c = msg.get('c')
            self.ui.reveal_explosion(r, c, self.root)
            try:
                if self.sound:
                    self.sound.play_effect('explosion')
            except Exception:
                pass
        
        elif msg_type == 'end':
            self.is_game_ended = True
            winner = msg.get('winner')
            reason = msg.get('reason')
            scores = msg.get('scores', [0, 0])
            self.last_scores = scores
            
            # Reveal mines with explosion animation
            mines = msg.get('mines', [])
            for (r, c) in mines:
                self.ui.reveal_explosion(r, c, self.root)
            try:
                if self.sound:
                    self.sound.play_effect('explosion')
            except Exception:
                pass
            
            self.ui.disable_board()
            
            # Determine result based on winner
            if self.mode.get() == 'scoring':
                # In scoring mode, -1 means tie
                if winner == -1:
                    result = 'tie'
                else:
                    result = 'win' if (winner == self.player_id) else 'lose'
            else:
                result = 'win' if (winner == self.player_id) else 'lose'
            # Wait 1000ms to ensure explosion animation completes before showing end screen
            self.root.after(1000, lambda: self.show_end_screen(result, reason))
        
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
