# Hexplorer

![Hexplorer GUI](https://github.com/user-attachments/assets/89de6006-8f0a-4d08-847e-f13c60f236aa)

Hexplorer is an advanced, user-friendly hex editor designed for efficient binary file analysis and manipulation. Built with Python, it offers both a feature-rich command-line interface and a modern web-based GUI that combines powerful functionality with intuitive controls.

## Features

### 🖥️ Web-based GUI (NEW!)
- **Modern Interface**: Beautiful, responsive web-based GUI that runs in your browser
- **File Browser**: Integrated file explorer for easy navigation
- **Advanced Viewing**: Multiple view modes (Hex, Decimal, ASCII) with live switching
- **Smart Search**: Real-time search with highlighting
- **Bookmarks**: Visual bookmark system for quick navigation
- **Dark/Light Theme**: Toggle between themes for comfort
- **Export Options**: Export data in various formats
- **Responsive Design**: Works on desktop and mobile devices

### 📟 Command-Line Interface (Classic)
- Multi-mode viewing: Hex, Decimal, and ASCII representations
- Advanced search functionality with forward and backward search
- In-place editing capabilities
- Bookmarking system for quick navigation
- File statistics display
- Color-coded interface for enhanced readability
- Comprehensive help system

## Installation

1. Ensure you have Python 3.6 or higher installed on your system.

2. Clone the Hexplorer repository:
   ```
   git clone https://github.com/yourusername/hexplorer.git
   cd hexplorer
   ```

3. (Optional) Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

## Usage

### 🌐 Web GUI (Recommended)

To start the advanced web-based GUI:

```bash
python hexplorer_web_gui.py
```

This will:
1. Start a local web server (default port 8080)
2. Automatically open your browser to the Hexplorer interface
3. Provide a modern, feature-rich editing experience

**GUI Features:**
- **File Browser**: Click on files in the left panel to open them
- **View Modes**: Switch between Hex, Decimal, and ASCII views
- **Search**: Use the search bar to find patterns in your files
- **Bookmarks**: Add bookmarks for quick navigation
- **Themes**: Toggle between light and dark themes
- **Export**: Export data in various formats

### 📟 Command-Line Interface

To start the classic CLI version:

```bash
python hexplorer.py <filename>
```

Replace `<filename>` with the path to the file you want to examine or edit.

### Key Commands (CLI Version)

- Arrow keys: Navigate through the file
- Page Up/Down: Scroll by page
- Home (g): Go to the start of the file
- End (G): Go to the end of the file
- '/': Enter search mode
- 'n'/'N': Find next/previous occurrence
- 'e': Edit current byte
- 'v': Cycle through view modes (Hex/Decimal/ASCII)
- 'b': Toggle bookmark at current position
- 'B': Jump to next bookmark
- 'f': Display file statistics
- 'h': Show help panel
- 's': Save changes
- 'q': Quit the editor

For a full list of commands, press 'h' while in the editor.

## Contributing

Contributions to Hexplorer are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by classic hex editors and modern code analysis tools
- Built with Python and the curses library

---

Happy Hexploring!
