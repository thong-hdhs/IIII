"""UI screen rendering and components for Mines Arena client."""
import tkinter as tk
from tkinter import font as tkfont


class NeonColors:
    """Neon color scheme for the UI."""
    BG_PRIMARY = '#0f0f1e'
    BG_SECONDARY = '#1a1a2e'
    NEON_PURPLE = '#b537f2'
    NEON_PINK = '#ff006e'
    NEON_CYAN = '#00f5ff'
    NEON_GREEN = '#39ff14'
    NEON_YELLOW = '#ffff00'
    WHITE_TEXT = '#ffffff'
    GRAY_TEXT = '#cccccc'


class UIRenderer:
    """Handles all screen rendering and UI components."""
    
    def __init__(self, main_frame, colors=None):
        self.main_frame = main_frame
        self.colors = colors or NeonColors()
        self.btns = None
        self.timer_label = None
    
    def clear_frame(self):
        """Clear all widgets from main frame."""
        for w in self.main_frame.winfo_children():
            w.destroy()
    
    def create_neon_button(self, parent, text, command, color=None, size=None):
        """Create a styled neon button."""
        if color is None:
            color = self.colors.NEON_CYAN
        if size is None:
            width, height, font_size = 24, 2, 12
        else:
            width, height, font_size = size
        
        btn = tk.Button(parent, text=text, command=command,
                       bg=self.colors.BG_SECONDARY, fg=color,
                       font=('Arial', font_size, 'bold'),
                       width=width, height=height,
                       relief='solid', bd=2, cursor='hand2',
                       activebackground=self.colors.BG_SECONDARY, activeforeground=color,
                       highlightthickness=2, highlightcolor=color, highlightbackground=color)
        return btn
    
    def show_menu_screen(self, on_survival, on_scoring, on_exit):
        """Render the main menu screen."""
        self.clear_frame()
        
        # Vertical centering
        top_spacer = tk.Frame(self.main_frame, bg=self.colors.BG_PRIMARY)
        top_spacer.pack(fill='both', expand=True)

        center = tk.Frame(self.main_frame, bg=self.colors.BG_PRIMARY)
        center.pack(padx=40)
        
        # Title
        title_frame = tk.Frame(center, bg=self.colors.BG_PRIMARY)
        title_frame.pack(pady=(18, 6), anchor='center')
        tk.Label(title_frame, text='⬤ MINES ARENA ⬤',
                bg=self.colors.BG_PRIMARY, fg=self.colors.NEON_CYAN, 
                font=('Arial', 34, 'bold')).pack()
        tk.Label(title_frame, text='Multiplayer Minesweeper',
                bg=self.colors.BG_PRIMARY, fg=self.colors.NEON_PURPLE, 
                font=('Arial', 12)).pack(pady=(6, 0))
        
        # Mode descriptions
        desc_frame = tk.Frame(center, bg=self.colors.BG_PRIMARY)
        desc_frame.pack(pady=(6, 8))
        tk.Label(desc_frame, 
                text='Survival: One mine ends the match — last player standing wins.',
                bg=self.colors.BG_PRIMARY, fg=self.colors.GRAY_TEXT, 
                font=('Arial', 10)).grid(row=0, column=0, padx=10)
        tk.Label(desc_frame, 
                text='Scoring: Each mine reduces your score; higher score wins.',
                bg=self.colors.BG_PRIMARY, fg=self.colors.GRAY_TEXT, 
                font=('Arial', 10)).grid(row=0, column=1, padx=10)

        # Mode buttons in cards
        btn_frame = tk.Frame(center, bg=self.colors.BG_PRIMARY)
        btn_frame.pack(pady=(10, 12), anchor='center', fill='x')

        card1 = tk.Frame(btn_frame, bg=self.colors.BG_SECONDARY, bd=2, relief='solid')
        card1.pack(pady=8, fill='x')
        btn_survival = self.create_neon_button(card1, '▶ SURVIVAL ◀',
                                              on_survival,
                                              self.colors.NEON_GREEN, (34, 2, 14))
        btn_survival.pack(padx=12, pady=10)

        card2 = tk.Frame(btn_frame, bg=self.colors.BG_SECONDARY, bd=2, relief='solid')
        card2.pack(pady=8, fill='x')
        btn_scoring = self.create_neon_button(card2, '▶ SCORING ◀',
                                             on_scoring,
                                             self.colors.NEON_YELLOW, (34, 2, 14))
        btn_scoring.pack(padx=12, pady=10)
        
        # Bottom spacer and exit
        bottom_spacer = tk.Frame(self.main_frame, bg=self.colors.BG_PRIMARY)
        bottom_spacer.pack(fill='both', expand=True)

        bot_frame = tk.Frame(self.main_frame, bg=self.colors.BG_PRIMARY)
        bot_frame.pack(side='bottom', fill='x', padx=40, pady=8)
        
        exit_btn = tk.Button(bot_frame, text='✕ EXIT',
                           bg=self.colors.NEON_PINK, fg=self.colors.BG_PRIMARY,
                           font=('Arial', 9, 'bold'),
                           command=on_exit,
                           relief='solid', bd=2, cursor='hand2',
                           width=12, height=1)
        exit_btn.pack()
    
    def show_game_screen(self):
        """Render the game board screen."""
        self.clear_frame()
        
        # Top bar
        top = tk.Frame(self.main_frame, bg=self.colors.NEON_PURPLE, height=70)
        top.pack(fill='x', padx=0, pady=0)
        top.pack_propagate(False)
        
        inner_top = tk.Frame(top, bg=self.colors.BG_SECONDARY, height=65)
        inner_top.pack(fill='both', expand=True, padx=2, pady=2)
        
        tk.Label(inner_top, text='◆ MINES ARENA ◆',
                bg=self.colors.BG_SECONDARY, fg=self.colors.NEON_CYAN,
                font=('Arial', 14, 'bold')).pack(side='left', padx=15, pady=10)
        
        self.timer_label = tk.Label(inner_top, text='⏱ 10s',
                                    bg=self.colors.BG_SECONDARY, fg=self.colors.NEON_PINK,
                                    font=('Arial', 14, 'bold'))
        self.timer_label.pack(side='right', padx=15, pady=10)
        
        # Board container
        board_container = tk.Frame(self.main_frame, bg=self.colors.BG_PRIMARY)
        board_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        self._create_board(board_container)
        self._clear_board()
    
    def _create_board(self, parent):
        """Create 8x8 board grid."""
        board = tk.Frame(parent, bg=self.colors.NEON_PURPLE, relief='raised', bd=3)
        board.pack()
        
        inner_board = tk.Frame(board, bg=self.colors.BG_SECONDARY)
        inner_board.pack(padx=3, pady=3)
        
        self.btns = [[None]*8 for _ in range(8)]
        btn_font = tkfont.Font(family='Arial', size=11, weight='bold')
        
        for r in range(8):
            for c in range(8):
                b = tk.Button(inner_board, text='□', width=7, height=3, font=btn_font,
                            bg='#2a2a3e', fg=self.colors.GRAY_TEXT, 
                            relief='solid', bd=2, cursor='hand2',
                            activebackground=self.colors.NEON_CYAN, 
                            activeforeground=self.colors.BG_PRIMARY)
                b.grid(row=r, column=c, padx=1, pady=1)
                self.btns[r][c] = b
    
    def _clear_board(self):
        """Reset board to empty state."""
        if not self.btns:
            return
        for r in range(8):
            for c in range(8):
                b = self.btns[r][c]
                b.config(text='□', state='disabled', bg='#2a2a3e', fg=self.colors.GRAY_TEXT)
    
    def set_board_callback(self, callback):
        """Set callback for board cell clicks."""
        if self.btns:
            for r in range(8):
                for c in range(8):
                    self.btns[r][c].config(command=lambda rr=r, cc=c: callback(rr, cc))
    
    def show_end_screen(self, result, reason, mode_value, on_play_again, on_back_menu):
        """Render the end game screen."""
        self.clear_frame()
        
        result_color = self.colors.NEON_GREEN if result == 'win' else self.colors.NEON_PINK
        result_emoji = '◆ VICTORY ◆' if result == 'win' else '✕ DEFEAT ✕'
        result_symbol = '⬤' if result == 'win' else '⊗'
        
        # Vertical centering
        top_spacer = tk.Frame(self.main_frame, bg=self.colors.BG_PRIMARY)
        top_spacer.pack(fill='both', expand=True)

        center = tk.Frame(self.main_frame, bg=self.colors.BG_PRIMARY)
        center.pack(padx=50)

        # Result card
        card = tk.Frame(center, bg=self.colors.BG_SECONDARY, bd=2, relief='solid')
        card.pack(padx=10, pady=(10, 18))

        tk.Label(card, text=result_symbol,
                bg=self.colors.BG_SECONDARY, fg=result_color, 
                font=('Arial', 48, 'bold')).pack(pady=(18, 6))
        tk.Label(card, text=result_emoji,
                bg=self.colors.BG_SECONDARY, fg=result_color, 
                font=('Arial', 22, 'bold')).pack(pady=(0, 6))
        tk.Label(card, text=reason,
                bg=self.colors.BG_SECONDARY, fg=self.colors.GRAY_TEXT, 
                font=('Arial', 11)).pack(pady=(0, 12))

        # Mode description
        mode_desc = 'Survival: One mine ends the match.' if mode_value == 'survival' else 'Scoring: Mines subtract points from your score.'
        tk.Label(center, text=mode_desc, bg=self.colors.BG_PRIMARY, 
                fg=self.colors.GRAY_TEXT, font=('Arial', 11)).pack(pady=(0, 12))
        
        # Action buttons
        btn_frame = tk.Frame(center, bg=self.colors.BG_PRIMARY)
        btn_frame.pack(pady=10, anchor='center')
        
        btn_again = self.create_neon_button(btn_frame, '▶ PLAY AGAIN ◀',
                                           on_play_again,
                                           self.colors.NEON_GREEN, (18, 2, 12))
        btn_again.grid(row=0, column=0, padx=8)
        
        btn_menu = self.create_neon_button(btn_frame, '◀ BACK TO MENU ▶',
                                          on_back_menu,
                                          self.colors.NEON_CYAN, (18, 2, 12))
        btn_menu.grid(row=0, column=1, padx=8)
        
        # Bottom exit
        bottom_spacer = tk.Frame(self.main_frame, bg=self.colors.BG_PRIMARY)
        bottom_spacer.pack(fill='both', expand=True)

        bot_frame = tk.Frame(self.main_frame, bg=self.colors.BG_PRIMARY)
        bot_frame.pack(side='bottom', fill='x', padx=50, pady=8)
        
        exit_btn = tk.Button(bot_frame, text='✕ EXIT',
                           bg=self.colors.NEON_PINK, fg=self.colors.BG_PRIMARY,
                           font=('Arial', 9, 'bold'),
                           command=lambda: None,  # Will be set by caller
                           relief='solid', bd=2, cursor='hand2',
                           width=12, height=1)
        exit_btn.pack()
    
    def mark_cell(self, r, c, player):
        """Mark a cell as selected by a player."""
        if not self.btns:
            return
        b = self.btns[r][c]
        symbols = {0: '★', 1: '◆'}
        colors = {0: self.colors.NEON_GREEN, 1: self.colors.NEON_YELLOW}
        b.config(text=symbols.get(player, '●'), state='disabled', relief='sunken')
        b.config(bg=colors.get(player, '#aaa'), fg=self.colors.BG_PRIMARY)
    
    def reveal_explosion(self, r, c, root):
        """Animate a mine explosion and surrounding cells."""
        if not self.btns:
            return
        
        coords = [(r, c)] + [(r+dr, c+dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if not (dr==0 and dc==0)]
        shown = []
        for (rr, cc) in coords:
            if 0 <= rr < 8 and 0 <= cc < 8:
                b = self.btns[rr][cc]
                prev = (b['text'], b['bg'], b['fg'])
                shown.append(((rr, cc), prev))
                b.config(text='◇' if (rr, cc)==(r, c) else b['text'],
                        bg='#ff6b35' if (rr, cc)==(r, c) else '#ff9770', fg='black')

        def finalise():
            for (rr, cc), prev in shown:
                if self.btns:
                    b = self.btns[rr][cc]
                    if (rr, cc) == (r, c):
                        b.config(text='☠', bg=self.colors.NEON_PINK, fg=self.colors.WHITE_TEXT)
                    else:
                        b.config(bg='#ff9770', fg='black')

        root.after(300, finalise)
    
    def enable_board_for_player(self, my_turn):
        """Enable or disable board based on whose turn it is."""
        if not self.btns:
            return
        for r in range(8):
            for c in range(8):
                if my_turn:
                    b = self.btns[r][c]
                    if b['text'] == '□':
                        b.config(state='normal', bg=self.colors.NEON_CYAN, fg=self.colors.BG_PRIMARY)
                else:
                    b = self.btns[r][c]
                    b.config(state='disabled', bg='#2a2a3e', fg=self.colors.GRAY_TEXT)
    
    def disable_board(self):
        """Disable all board cells."""
        if not self.btns:
            return
        for r in range(8):
            for c in range(8):
                self.btns[r][c].config(state='disabled')
