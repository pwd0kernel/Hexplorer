import curses
import mmap
import argparse
import os
import time
from curses import textpad

class HexEditor:
    def __init__(self, filename):
        self.filename = filename
        self.mm = None
        self.offset = 0
        self.cursor = 0
        self.status_message = ""
        self.show_help = False
        self.search_term = ""
        self.search_mode = False
        self.edit_mode = False
        self.edit_buffer = ""
        self.view_mode = "hex"  # Can be "hex", "dec", or "ascii"
        self.bookmarks = []

    def load_file(self):
        self.file = open(self.filename, 'r+b')
        self.mm = mmap.mmap(self.file.fileno(), 0)

    def save_file(self):
        self.mm.flush()
        self.file.close()

    def setup_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Header
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Hex values
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)  # ASCII values
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Status bar
        curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Help text
        curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)    # Search highlight
        curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)# Bookmarks

    def display(self, stdscr):
        height, width = stdscr.getmaxyx()
        bytes_per_line = 16
        
        stdscr.clear()
        
        # Display header
        header = f" Offset    00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F  ASCII"
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(0, 0, header[:width])
        stdscr.attroff(curses.color_pair(1))
        
        for i in range(1, height - 2):  # Leave two lines for status
            offset = self.offset + (i - 1) * bytes_per_line
            if offset >= len(self.mm):
                break
            
            # Display offset
            offset_str = f"{offset:08x}:"
            stdscr.addstr(i, 1, offset_str)
            
            # Display values based on view mode
            if self.view_mode in ["hex", "dec"]:
                color_pair = curses.color_pair(2)
                format_str = "{:02x}" if self.view_mode == "hex" else "{:3d}"
            else:  # ASCII mode
                color_pair = curses.color_pair(3)
            
            stdscr.attron(color_pair)
            for j in range(bytes_per_line):
                if offset + j >= len(self.mm):
                    break
                if 10 + j * 3 >= width:
                    break
                
                if offset + j in self.bookmarks:
                    stdscr.attron(curses.color_pair(7))
                
                if self.cursor == offset + j:
                    stdscr.attron(curses.A_REVERSE)
                
                if self.search_term and self.search_term.startswith(chr(self.mm[offset+j])):
                    stdscr.attron(curses.color_pair(6))
                
                if self.view_mode in ["hex", "dec"]:
                    stdscr.addstr(i, 10 + j * 3, format_str.format(self.mm[offset+j]))
                else:
                    char = chr(self.mm[offset+j])
                    stdscr.addstr(i, 10 + j, char if 32 <= self.mm[offset+j] <= 126 else ".")
                
                stdscr.attroff(curses.A_REVERSE)
                stdscr.attroff(curses.color_pair(6))
                stdscr.attroff(curses.color_pair(7))
            
            stdscr.attroff(color_pair)
            
            # Display ASCII representation (if not in ASCII view mode)
            if self.view_mode != "ascii":
                ascii_start = 10 + bytes_per_line * 3 + 2
                if ascii_start < width:
                    stdscr.addstr(i, ascii_start - 2, "  ")
                    stdscr.attron(curses.color_pair(3))
                    for j in range(bytes_per_line):
                        if offset + j >= len(self.mm) or ascii_start + j >= width:
                            break
                        char = chr(self.mm[offset+j])
                        if 32 <= self.mm[offset+j] <= 126:
                            stdscr.addstr(i, ascii_start + j, char)
                        else:
                            stdscr.addstr(i, ascii_start + j, ".")
                    stdscr.attroff(curses.color_pair(3))

        # Status bar
        self.display_status_bar(stdscr)

        # Help panel
        if self.show_help:
            self.display_help(stdscr)

    def display_status_bar(self, stdscr):
        height, width = stdscr.getmaxyx()
        if self.search_mode:
            status = f" Search: {self.search_term} | Press Enter to search, Esc to cancel "
        elif self.edit_mode:
            status = f" Edit mode | Current value: {self.edit_buffer} | Press Enter to confirm, Esc to cancel "
        else:
            status = f" File: {self.filename} | Cursor: {self.cursor:08x} | Mode: {self.view_mode.upper()} | Press 'h' for help "
        
        status = status.ljust(width - 1)
        stdscr.attron(curses.color_pair(4))
        stdscr.addstr(height - 2, 0, status[:width - 1])
        stdscr.attroff(curses.color_pair(4))

        # Command hint bar
        hint = " [↑↓←→] Navigate | [/] Search | [e] Edit | [v] View Mode | [b] Bookmark | [q] Quit "
        hint = hint.ljust(width - 1)
        stdscr.attron(curses.color_pair(5))
        stdscr.addstr(height - 1, 0, hint[:width - 1])
        stdscr.attroff(curses.color_pair(5))

    def display_help(self, stdscr):
        height, width = stdscr.getmaxyx()
        help_text = [
            "Hex Editor Help",
            "",
            "Navigation:",
            "  Arrow keys: Move cursor",
            "  Page Up/Down: Scroll by page",
            "  Home (g): Go to start of file",
            "  End (G): Go to end of file",
            "",
            "Editing and Viewing:",
            "  e: Enter edit mode",
            "  v: Cycle view mode (HEX/DEC/ASCII)",
            "  b: Toggle bookmark at cursor",
            "  B: Jump to next bookmark",
            "",
            "Search:",
            "  /: Enter search mode",
            "  n: Find next occurrence",
            "  N: Find previous occurrence",
            "",
            "File Operations:",
            "  f: Display file statistics",
            "  s: Save file",
            "",
            "Other Commands:",
            "  h: Toggle this help panel",
            "  q: Quit the editor",
            "",
            "Press any key to close help"
        ]
        
        panel_height = len(help_text) + 2
        panel_width = max(len(line) for line in help_text) + 4
        start_y = (height - panel_height) // 2
        start_x = (width - panel_width) // 2

        help_win = curses.newwin(panel_height, panel_width, start_y, start_x)
        help_win.box()
        help_win.attron(curses.color_pair(5))
        
        for i, line in enumerate(help_text):
            help_win.addstr(i + 1, 2, line)
        
        help_win.attroff(curses.color_pair(5))
        help_win.refresh()
        help_win.getch()

    def display_file_stats(self, stdscr):
        height, width = stdscr.getmaxyx()
        file_stat = os.stat(self.filename)
        stats_text = [
            "File Statistics",
            "",
            f"Filename: {self.filename}",
            f"Size: {file_stat.st_size} bytes",
            f"Created: {time.ctime(file_stat.st_ctime)}",
            f"Last Modified: {time.ctime(file_stat.st_mtime)}",
            f"Last Accessed: {time.ctime(file_stat.st_atime)}",
            f"Permissions: {oct(file_stat.st_mode)[-3:]}",
            f"Number of bookmarks: {len(self.bookmarks)}",
            "",
            "Press any key to close"
        ]
        
        panel_height = len(stats_text) + 2
        panel_width = max(len(line) for line in stats_text) + 4
        start_y = (height - panel_height) // 2
        start_x = (width - panel_width) // 2

        stats_win = curses.newwin(panel_height, panel_width, start_y, start_x)
        stats_win.box()
        stats_win.attron(curses.color_pair(5))
        
        for i, line in enumerate(stats_text):
            stats_win.addstr(i + 1, 2, line)
        
        stats_win.attroff(curses.color_pair(5))
        stats_win.refresh()
        stats_win.getch()

    def search(self, direction=1):
        if self.search_term:
            start = self.cursor + direction
            end = len(self.mm) if direction > 0 else -1
            step = direction
            
            search_bytes = self.search_term.encode('utf-8')
            index = -1
            
            for i in range(start, end, step):
                if self.mm[i:i+len(search_bytes)] == search_bytes:
                    index = i
                    break
            
            if index != -1:
                self.cursor = index
                self.status_message = f"Found at offset: {index:08x}"
            else:
                self.status_message = "Search term not found"

    def toggle_bookmark(self):
        if self.cursor in self.bookmarks:
            self.bookmarks.remove(self.cursor)
            self.status_message = f"Bookmark removed at offset: {self.cursor:08x}"
        else:
            self.bookmarks.append(self.cursor)
            self.status_message = f"Bookmark added at offset: {self.cursor:08x}"
        self.bookmarks.sort()

    def jump_to_next_bookmark(self):
        if not self.bookmarks:
            self.status_message = "No bookmarks set"
            return
        
        for bookmark in self.bookmarks:
            if bookmark > self.cursor:
                self.cursor = bookmark
                self.status_message = f"Jumped to bookmark at offset: {self.cursor:08x}"
                return
        
        # If we're past all bookmarks, wrap around to the first one
        self.cursor = self.bookmarks[0]
        self.status_message = f"Jumped to bookmark at offset: {self.cursor:08x}"

    def edit_byte(self):
        if self.edit_mode:
            try:
                if self.view_mode == "hex":
                    value = int(self.edit_buffer, 16)
                elif self.view_mode == "dec":
                    value = int(self.edit_buffer)
                else:  # ASCII mode
                    value = ord(self.edit_buffer)
                
                if 0 <= value <= 255:
                    self.mm[self.cursor] = value
                    self.cursor += 1
                    self.status_message = f"Byte updated to: {value:02x}"
                else:
                    self.status_message = "Invalid byte value"
            except ValueError:
                self.status_message = "Invalid input"
            
            self.edit_mode = False
            self.edit_buffer = ""
        else:
            self.edit_mode = True
            self.edit_buffer = ""
            self.status_message = "Enter new byte value"

    def run(self):
        curses.wrapper(self._run)

    def _run(self, stdscr):
        self.setup_colors()
        curses.curs_set(0)  # Hide the cursor
        stdscr.clear()
        
        while True:
            self.display(stdscr)
            self.adjust_view(stdscr)
            stdscr.refresh()
            
            if self.search_mode or self.edit_mode:
                key = stdscr.getch()
                if key == 27:  # Esc
                    self.search_mode = False
                    self.edit_mode = False
                    self.search_term = ""
                    self.edit_buffer = ""
                elif key == 10:  # Enter
                    if self.search_mode:
                        self.search_mode = False
                        self.search()
                    elif self.edit_mode:
                        self.edit_byte()
                elif key == curses.KEY_BACKSPACE or key == 127:
                    if self.search_mode:
                        self.search_term = self.search_term[:-1]
                    elif self.edit_mode:
                        self.edit_buffer = self.edit_buffer[:-1]
                elif 32 <= key <= 126:
                    if self.search_mode:
                        self.search_term += chr(key)
                    elif self.edit_mode:
                        self.edit_buffer += chr(key)
                continue

            key = stdscr.getch()
            if self.show_help:
                self.show_help = False
                continue

            if key == ord('q'):
                if self.confirm_quit(stdscr):
                    break
            elif key == curses.KEY_DOWN:
                self.cursor = min(len(self.mm) - 1, self.cursor + 16)
            elif key == curses.KEY_UP:
                self.cursor = max(0, self.cursor - 16)
            elif key == curses.KEY_RIGHT:
                self.cursor = min(len(self.mm) - 1, self.cursor + 1)
            elif key == curses.KEY_LEFT:
                self.cursor = max(0, self.cursor - 1)
            elif key == curses.KEY_NPAGE:  # Page Down
                self.cursor = min(len(self.mm) - 1, self.cursor + 160)
            elif key == curses.KEY_PPAGE:  # Page Up
                self.cursor = max(0, self.cursor - 160)
            elif key == ord('g'):
                self.cursor = 0
            elif key == ord('G'):
                self.cursor = len(self.mm) - 1
            elif key == ord('h'):
                self.show_help = True
            elif key == ord('f'):
                self.display_file_stats(stdscr)
            elif key == ord('/'):
                self.search_mode = True
                self.search_term = ""
            elif key == ord('n'):
                self.search(direction=1)
            elif key == ord('N'):
                self.search(direction=-1)
            elif key == ord('e'):
                self.edit_byte()
            elif key == ord('v'):
                self.cycle_view_mode()
            elif key == ord('b'):
                self.toggle_bookmark()
            elif key == ord('B'):
                self.jump_to_next_bookmark()
            elif key == ord('s'):
                self.save_file()
                self.status_message = "File saved successfully"

    def adjust_view(self, stdscr):
        height, _ = stdscr.getmaxyx()
        cursor_line = self.cursor // 16
        if cursor_line < self.offset // 16:
            self.offset = (cursor_line * 16) - (height - 5) * 16
        elif cursor_line >= (self.offset // 16) + height - 4:
            self.offset = (cursor_line - height + 5) * 16
        self.offset = max(0, self.offset)

    def cycle_view_mode(self):
        modes = ["hex", "dec", "ascii"]
        current_index = modes.index(self.view_mode)
        self.view_mode = modes[(current_index + 1) % len(modes)]
        self.status_message = f"View mode changed to: {self.view_mode.upper()}"

    def confirm_quit(self, stdscr):
        height, width = stdscr.getmaxyx()
        confirm_text = "Do you want to quit? Unsaved changes will be lost. (y/n)"
        panel_height = 3
        panel_width = len(confirm_text) + 4
        start_y = (height - panel_height) // 2
        start_x = (width - panel_width) // 2

        confirm_win = curses.newwin(panel_height, panel_width, start_y, start_x)
        confirm_win.box()
        confirm_win.addstr(1, 2, confirm_text)
        confirm_win.refresh()

        while True:
            key = confirm_win.getch()
            if key in [ord('y'), ord('Y')]:
                return True
            elif key in [ord('n'), ord('N')]:
                return False

def main():
    parser = argparse.ArgumentParser(description="Hexplorer")
    parser.add_argument("filename", help="File to edit")
    args = parser.parse_args()

    editor = HexEditor(args.filename)
    editor.load_file()
    try:
        editor.run()
    finally:
        editor.save_file()

if __name__ == "__main__":
    main()
