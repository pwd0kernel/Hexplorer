# Hexplorer

![Hexplorer CLI]([placeholder_for_cli_image.png](https://raw.githubusercontent.com/pwd0kernel/Hexplorer/main/Screenshot%20from%202024-08-24%2020-08-59.png))

Hexplorer is an advanced, user-friendly hex editor designed for efficient binary file analysis and manipulation. Built with Python, it offers a feature-rich command-line interface that combines powerful functionality with intuitive controls.

## Features

- Multi-mode viewing: Hex, Decimal, and ASCII representations
- Advanced search functionality with forward and backward search
- In-place editing capabilities
- Bookmarking system for quick navigation
- String extraction utility for easy text analysis
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

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To start Hexplorer, run:

```
python hexplorer.py <filename>
```

Replace `<filename>` with the path to the file you want to examine or edit.

### Key Commands

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
- 'x': Extract and display strings
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
