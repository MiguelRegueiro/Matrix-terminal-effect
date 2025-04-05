#!/usr/bin/env python3
import random
import time
import colorama
from colorama import Fore, Style
import msvcrt
import os
import sqlite3
from datetime import datetime

# Initialize colorama
colorama.init()

class MatrixTerminal:
    def __init__(self):
        # First initialize character sets
        self.char_sets = {
            'main': "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン",
            'numbers': "0123456789" * 8,  # 8 times more numbers
            'symbols': "!@#$%^&*()_+-=[]{};':\",./<>?\\|`~"
        }
        self.matrix_chars = self.char_sets['main'] + self.char_sets['numbers'] + self.char_sets['symbols']
        
        # Initialize other components
        self.hidden_mode = False
        self.setup_db()
        self.setup_ui()
        self.last_draw_time = time.time()
        self.frame_delay = 0.07  # Slightly slower for better visibility
        self.prev_output = {}

    def setup_db(self):
        """Initialize SQLite database for messages"""
        self.conn = sqlite3.connect('messages.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS messages
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          sender TEXT,
                          content TEXT,
                          timestamp DATETIME)''')
        self.conn.commit()

    def setup_ui(self):
        """Initialize UI elements"""
        self.update_terminal_size()
        self.columns = []
        self.initialize_columns()

    def update_terminal_size(self):
        """Get current terminal dimensions"""
        try:
            size = os.get_terminal_size()
            self.width = min(size.columns, 120)  # Limit maximum width
            self.height = size.lines - 1  # Leave room for input
        except:
            # Default size if terminal detection fails
            self.width = 80
            self.height = 24

    def initialize_columns(self):
        """Initialize all matrix columns"""
        density = 0.7  # 70% of columns will be active
        self.columns = []
        for x in range(self.width):
            if random.random() < density:
                self.columns.append({
                    'x': x,
                    'pos': random.uniform(-self.height, 0),  # Start position
                    'speed': random.uniform(0.3, 0.6),  # Slower speed range
                    'trail_length': random.randint(10, 20),  # Longer trails
                    'chars': self.generate_char_sequence(40),  # Longer sequences
                    'char_index': 0
                })

    def generate_char_sequence(self, length):
        """Generate a random sequence of characters for a column"""
        return [random.choice(self.matrix_chars) for _ in range(length)]

    def clear_screen(self):
        """Clear the terminal screen using ANSI escape codes"""
        print("\033[2J\033[H", end='')

    def draw_matrix_rain(self):
        """Draw the falling code rain with optimized rendering"""
        current_time = time.time()
        if current_time - self.last_draw_time < self.frame_delay:
            return
        self.last_draw_time = current_time

        self.update_terminal_size()
        new_output = {}
        
        for col in self.columns:
            if col['x'] >= self.width:
                continue
                
            # Update position
            col['pos'] += col['speed']
            current_pos = int(col['pos'])
            col['char_index'] = (col['char_index'] + 1) % len(col['chars'])
            
            # Draw the trail
            for i in range(col['trail_length']):
                trail_pos = current_pos - i
                if 0 <= trail_pos < self.height:
                    char = col['chars'][(col['char_index'] - i) % len(col['chars'])]
                    
                    # Calculate intensity
                    intensity = 1 - (i / col['trail_length'])
                    if intensity > 0.8:
                        color = Fore.GREEN + Style.BRIGHT
                    elif intensity > 0.5:
                        color = Fore.GREEN
                    elif intensity > 0.3:
                        color = Fore.GREEN + Style.DIM
                    else:
                        continue  # Skip very dim characters
                    
                    new_output[(trail_pos, col['x'])] = color + char
            
            # Reset column if it goes off screen
            if current_pos > self.height + col['trail_length'] and random.random() > 0.96:
                col['pos'] = random.uniform(-col['trail_length'], 0)
                col['speed'] = random.uniform(0.3, 0.6)
                col['trail_length'] = random.randint(10, 20)
                col['chars'] = self.generate_char_sequence(40)
                col['char_index'] = 0

        # Draw only the changes from previous frame
        self.draw_changes(new_output)
        self.prev_output = new_output

    def draw_changes(self, new_output):
        """Draw only the changes since last frame to reduce flickering"""
        buffer = []
        
        # Clear characters from previous frame that are no longer needed
        for pos in self.prev_output:
            if pos not in new_output:
                buffer.append(f"\033[{pos[0]+1};{pos[1]+1}H ")
        
        # Draw new or changed characters
        for pos, char in new_output.items():
            if self.prev_output.get(pos) != char:
                buffer.append(f"\033[{pos[0]+1};{pos[1]+1}H{char}")
        
        # Print all changes at once
        if buffer:
            print(''.join(buffer), end='', flush=True)

    def draw_hidden_ui(self):
        """Draw the hidden chat interface"""
        self.clear_screen()
        border = Fore.GREEN + "┌" + "─" * (self.width - 2) + "┐"
        print(border)
        
        # Title
        title = " HIDDEN MATRIX COMMUNICATION SYSTEM "
        print(Fore.GREEN + "│" + Fore.WHITE + title.center(self.width - 2) + Fore.GREEN + "│")
        print(Fore.GREEN + "├" + "─" * (self.width - 2) + "┤")
        
        # Messages area
        messages = self.get_messages()
        for i, msg in enumerate(messages[-10:]):  # Show last 10 messages
            msg_text = f"{msg[2]} | {msg[1]}: {msg[3]}"
            print(Fore.GREEN + "│" + Fore.WHITE + msg_text.ljust(self.width - 2) + Fore.GREEN + "│")
        
        # Input area
        print(Fore.GREEN + "├" + "─" * (self.width - 2) + "┤")
        print(Fore.GREEN + "│" + Fore.WHITE + "Message: ".ljust(self.width - 2) + Fore.GREEN + "│")
        print(Fore.GREEN + "└" + "─" * (self.width - 2) + "┘")
        print(Fore.CYAN + "Press ESC to return to Matrix, F1 to clear messages")

    def get_messages(self):
        """Retrieve messages from database"""
        self.c.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT 50")
        return self.c.fetchall()

    def add_message(self, sender, content):
        """Add a new message to database"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.c.execute("INSERT INTO messages (sender, content, timestamp) VALUES (?, ?, ?)",
                      (sender, content, timestamp))
        self.conn.commit()

    def run(self):
        """Main application loop"""
        try:
            while True:
                if self.hidden_mode:
                    self.draw_hidden_ui()
                    self.handle_hidden_input()
                else:
                    self.draw_matrix_rain()
                
                # Handle input
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'm' or key == b'M':  # Toggle hidden mode
                        self.hidden_mode = not self.hidden_mode
                        self.clear_screen()
                    elif key == b'\x1b':  # ESC
                        self.hidden_mode = False
                        self.clear_screen()
                    elif key == b'\x00' or key == b'\xe0':  # Function key prefix
                        next_key = msvcrt.getch()
                        if next_key == b';':  # F1 key
                            self.c.execute("DELETE FROM messages")
                            self.conn.commit()
                
                time.sleep(0.01)  # Small sleep to prevent CPU overuse
                
        except KeyboardInterrupt:
            print(Style.RESET_ALL + "\nExiting Matrix...")
            self.conn.close()
        finally:
            print(Style.RESET_ALL)

    def handle_hidden_input(self):
        """Process input in hidden mode"""
        print(f"\033[{self.height+1};10H", end='', flush=True)
        try:
            message = input()
            if message:
                self.add_message("User", message)
        except:
            pass  # Ignore input errors

if __name__ == "__main__":
    app = MatrixTerminal()
    app.run()