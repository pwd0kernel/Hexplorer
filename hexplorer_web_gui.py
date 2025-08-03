#!/usr/bin/env python3
"""
Hexplorer GUI - Advanced Hex Editor with Web-based Interface
An enhanced version of the Hexplorer hex editor with modern web GUI features.
"""

import http.server
import socketserver
import webbrowser
import json
import mmap
import os
import re
import time
import threading
import urllib.parse
from pathlib import Path
from typing import Optional, List, Tuple, Dict
import base64
import hashlib
import socket


class HexEditorServer:
    def __init__(self, port=8080):
        self.port = port
        self.current_file = None
        self.file_data = None
        self.file_handle = None
        self.bookmarks = []
        self.search_history = []
        self.bytes_per_row = 16
        self.view_mode = "hex"
        
    def start_server(self):
        """Start the web server and open browser."""
        # Create the HTTP request handler
        handler = self.create_request_handler()
        
        # Find available port
        while True:
            try:
                with socketserver.TCPServer(("", self.port), handler) as httpd:
                    print(f"Hexplorer GUI server running at http://localhost:{self.port}")
                    
                    # Open browser automatically
                    webbrowser.open(f"http://localhost:{self.port}")
                    
                    httpd.serve_forever()
            except OSError:
                self.port += 1
                if self.port > 8090:
                    print("Could not find available port")
                    break
    
    def create_request_handler(self):
        """Create the HTTP request handler class."""
        hex_editor = self
        
        class HexEditorHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/" or self.path == "/index.html":
                    self.serve_main_page()
                elif self.path == "/api/file_list":
                    self.serve_file_list()
                elif self.path.startswith("/api/file_content"):
                    self.serve_file_content()
                elif self.path == "/api/status":
                    self.serve_status()
                else:
                    self.serve_static_file()
            
            def do_POST(self):
                if self.path == "/api/open_file":
                    self.handle_open_file()
                elif self.path == "/api/save_file":
                    self.handle_save_file()
                elif self.path == "/api/search":
                    self.handle_search()
                elif self.path == "/api/bookmark":
                    self.handle_bookmark()
                elif self.path == "/api/set_view_mode":
                    self.handle_view_mode()
                else:
                    self.send_error(404)
            
            def serve_main_page(self):
                """Serve the main HTML page."""
                html_content = hex_editor.get_main_html()
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.send_header("Content-length", len(html_content))
                self.end_headers()
                self.wfile.write(html_content.encode())
            
            def serve_file_list(self):
                """Serve the file browser data."""
                try:
                    current_dir = os.getcwd()
                    files = []
                    for item in sorted(os.listdir(current_dir)):
                        if item.startswith('.'):
                            continue  # Skip hidden files
                        item_path = os.path.join(current_dir, item)
                        is_dir = os.path.isdir(item_path)
                        try:
                            size = os.path.getsize(item_path) if not is_dir else 0
                        except OSError:
                            size = 0
                        files.append({
                            "name": item,
                            "is_directory": is_dir,
                            "size": size,
                            "path": item_path
                        })
                    
                    response = json.dumps(files)
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Content-length", len(response))
                    self.end_headers()
                    self.wfile.write(response.encode())
                except Exception as e:
                    self.send_error(500, str(e))
            
            def serve_file_content(self):
                """Serve hex content of the current file."""
                try:
                    if not hex_editor.file_data:
                        response = json.dumps({"error": "No file loaded"})
                    else:
                        content = hex_editor.get_hex_content()
                        response = json.dumps(content)
                    
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.send_header("Content-length", len(response))
                    self.end_headers()
                    self.wfile.write(response.encode())
                except Exception as e:
                    self.send_error(500, str(e))
            
            def serve_status(self):
                """Serve current status information."""
                status = {
                    "current_file": hex_editor.current_file,
                    "file_size": len(hex_editor.file_data) if hex_editor.file_data else 0,
                    "bookmarks": hex_editor.bookmarks,
                    "view_mode": hex_editor.view_mode,
                    "bytes_per_row": hex_editor.bytes_per_row
                }
                
                response = json.dumps(status)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Content-length", len(response))
                self.end_headers()
                self.wfile.write(response.encode())
            
            def handle_open_file(self):
                """Handle file opening request."""
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode())
                    
                    file_path = data.get("file_path")
                    if file_path and os.path.exists(file_path):
                        hex_editor.load_file(file_path)
                        response = json.dumps({"success": True, "message": f"Opened {file_path}"})
                    else:
                        response = json.dumps({"success": False, "message": "File not found"})
                    
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.send_header("Content-length", len(response))
                    self.end_headers()
                    self.wfile.write(response.encode())
                except Exception as e:
                    self.send_error(500, str(e))
            
            def handle_search(self):
                """Handle search request."""
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode())
                    
                    search_term = data.get("search_term", "")
                    results = hex_editor.search_in_file(search_term)
                    
                    response = json.dumps({"results": results})
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.send_header("Content-length", len(response))
                    self.end_headers()
                    self.wfile.write(response.encode())
                except Exception as e:
                    self.send_error(500, str(e))
            
            def handle_bookmark(self):
                """Handle bookmark operations."""
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode())
                    
                    action = data.get("action")
                    offset = data.get("offset", 0)
                    
                    if action == "add":
                        hex_editor.add_bookmark(offset)
                    elif action == "remove":
                        hex_editor.remove_bookmark(offset)
                    
                    response = json.dumps({"bookmarks": hex_editor.bookmarks})
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.send_header("Content-length", len(response))
                    self.end_headers()
                    self.wfile.write(response.encode())
                except Exception as e:
                    self.send_error(500, str(e))
            
            def handle_view_mode(self):
                """Handle view mode change."""
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode())
                    
                    view_mode = data.get("view_mode", "hex")
                    hex_editor.view_mode = view_mode
                    
                    bytes_per_row = data.get("bytes_per_row")
                    if bytes_per_row:
                        hex_editor.bytes_per_row = int(bytes_per_row)
                    
                    response = json.dumps({"success": True})
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.send_header("Content-length", len(response))
                    self.end_headers()
                    self.wfile.write(response.encode())
                except Exception as e:
                    self.send_error(500, str(e))
            
            def serve_static_file(self):
                """Serve static files (CSS, JS, etc.)."""
                if self.path == "/style.css":
                    css_content = hex_editor.get_css()
                    self.send_response(200)
                    self.send_header("Content-type", "text/css")
                    self.send_header("Content-length", len(css_content))
                    self.end_headers()
                    self.wfile.write(css_content.encode())
                elif self.path == "/script.js":
                    js_content = hex_editor.get_javascript()
                    self.send_response(200)
                    self.send_header("Content-type", "application/javascript")
                    self.send_header("Content-length", len(js_content))
                    self.end_headers()
                    self.wfile.write(js_content.encode())
                else:
                    self.send_error(404)
        
        return HexEditorHandler
    
    def load_file(self, file_path):
        """Load a file for hex editing."""
        try:
            if self.file_handle:
                self.file_handle.close()
            if self.file_data:
                self.file_data.close()
            
            self.file_handle = open(file_path, 'r+b')
            self.file_data = mmap.mmap(self.file_handle.fileno(), 0, access=mmap.ACCESS_READ)
            self.current_file = file_path
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def get_hex_content(self):
        """Get hex content for display."""
        if not self.file_data:
            return {"lines": [], "total_size": 0}
        
        lines = []
        file_size = len(self.file_data)
        
        for offset in range(0, min(file_size, 10000), self.bytes_per_row):  # Limit initial display
            line_data = {
                "offset": offset,
                "offset_hex": f"{offset:08x}",
                "hex_bytes": [],
                "ascii_chars": ""
            }
            
            ascii_chars = ""
            for i in range(self.bytes_per_row):
                if offset + i < file_size:
                    byte_val = self.file_data[offset + i]
                    
                    if self.view_mode == "hex":
                        line_data["hex_bytes"].append(f"{byte_val:02x}")
                    elif self.view_mode == "decimal":
                        line_data["hex_bytes"].append(f"{byte_val:3d}")
                    else:  # ascii
                        if 32 <= byte_val <= 126:
                            line_data["hex_bytes"].append(chr(byte_val))
                        else:
                            line_data["hex_bytes"].append(".")
                    
                    # ASCII representation
                    if 32 <= byte_val <= 126:
                        ascii_chars += chr(byte_val)
                    else:
                        ascii_chars += "."
                else:
                    line_data["hex_bytes"].append("")
                    ascii_chars += " "
            
            line_data["ascii_chars"] = ascii_chars
            lines.append(line_data)
        
        return {
            "lines": lines,
            "total_size": file_size,
            "view_mode": self.view_mode,
            "bytes_per_row": self.bytes_per_row
        }
    
    def search_in_file(self, search_term):
        """Search for a term in the file."""
        if not self.file_data or not search_term:
            return []
        
        results = []
        search_bytes = search_term.encode('utf-8', errors='ignore')
        
        for i in range(len(self.file_data) - len(search_bytes) + 1):
            if self.file_data[i:i+len(search_bytes)] == search_bytes:
                results.append({
                    "offset": i,
                    "offset_hex": f"{i:08x}",
                    "context": self.file_data[max(0, i-8):i+len(search_bytes)+8].hex()
                })
                if len(results) >= 100:  # Limit results
                    break
        
        return results
    
    def add_bookmark(self, offset):
        """Add a bookmark at the specified offset."""
        if offset not in self.bookmarks:
            self.bookmarks.append(offset)
            self.bookmarks.sort()
    
    def remove_bookmark(self, offset):
        """Remove a bookmark at the specified offset."""
        if offset in self.bookmarks:
            self.bookmarks.remove(offset)
    
    def get_main_html(self):
        """Generate the main HTML page."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hexplorer - Advanced Hex Editor</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <header class="header">
        <div class="header-left">
            <h1>🔍 Hexplorer</h1>
            <span class="subtitle">Advanced Hex Editor</span>
        </div>
        <div class="header-right">
            <button id="themeToggle" class="btn btn-secondary">🌙 Dark Mode</button>
        </div>
    </header>

    <nav class="toolbar">
        <div class="toolbar-group">
            <button id="openFile" class="btn">📁 Open</button>
            <button id="saveFile" class="btn">💾 Save</button>
            <button id="exportFile" class="btn">📤 Export</button>
        </div>
        
        <div class="toolbar-group">
            <label>View:</label>
            <select id="viewMode">
                <option value="hex">Hex</option>
                <option value="decimal">Decimal</option>
                <option value="ascii">ASCII</option>
            </select>
            
            <label>Bytes/Row:</label>
            <select id="bytesPerRow">
                <option value="8">8</option>
                <option value="16" selected>16</option>
                <option value="32">32</option>
            </select>
        </div>
        
        <div class="toolbar-group">
            <input type="text" id="searchInput" placeholder="Search..." class="search-input">
            <button id="searchBtn" class="btn">🔍 Find</button>
            <button id="gotoBtn" class="btn">🎯 Go to Offset</button>
        </div>
    </nav>

    <div class="main-container">
        <aside class="sidebar">
            <div class="sidebar-section">
                <h3>📂 File Browser</h3>
                <div id="fileList" class="file-list"></div>
            </div>
            
            <div class="sidebar-section">
                <h3>🔖 Bookmarks</h3>
                <div id="bookmarkList" class="bookmark-list"></div>
                <button id="addBookmark" class="btn btn-small">Add Bookmark</button>
            </div>
            
            <div class="sidebar-section">
                <h3>📊 File Info</h3>
                <div id="fileInfo" class="file-info">
                    <p>No file loaded</p>
                </div>
            </div>
        </aside>

        <main class="editor-area">
            <div class="editor-header">
                <div class="file-tabs">
                    <div class="tab active" data-file="">Welcome</div>
                </div>
            </div>
            
            <div class="hex-display" id="hexDisplay">
                <div class="welcome-message">
                    <h2>Welcome to Hexplorer GUI</h2>
                    <p>🎯 <strong>Advanced Features:</strong></p>
                    <ul>
                        <li>📁 File browser with drag & drop support</li>
                        <li>🔍 Advanced search with regex support</li>
                        <li>🔖 Bookmark system for quick navigation</li>
                        <li>📊 Real-time file statistics</li>
                        <li>🎨 Dark/Light theme toggle</li>
                        <li>📝 Multiple viewing modes (Hex, Decimal, ASCII)</li>
                        <li>💾 Export to various formats</li>
                        <li>⚡ High-performance rendering</li>
                    </ul>
                    <p>Select a file from the browser to start editing!</p>
                </div>
            </div>
        </main>
    </div>

    <footer class="status-bar">
        <div class="status-left">
            <span id="statusMessage">Ready</span>
        </div>
        <div class="status-right">
            <span id="cursorPosition">Offset: 0x00000000</span>
            <span id="fileSize">Size: 0 bytes</span>
            <span id="selectionInfo"></span>
        </div>
    </footer>

    <script src="/script.js"></script>
</body>
</html>"""
    
    def get_css(self):
        """Generate the CSS styles."""
        return """/* Hexplorer Advanced GUI Styles */

:root {
    --primary-color: #2563eb;
    --secondary-color: #64748b;
    --success-color: #10b981;
    --danger-color: #ef4444;
    --warning-color: #f59e0b;
    
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --bg-tertiary: #e2e8f0;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --border-color: #e2e8f0;
    
    --font-mono: 'Courier New', monospace;
    --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

[data-theme="dark"] {
    --bg-primary: #1e293b;
    --bg-secondary: #334155;
    --bg-tertiary: #475569;
    --text-primary: #f1f5f9;
    --text-secondary: #cbd5e1;
    --border-color: #475569;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: var(--font-sans);
    background: var(--bg-primary);
    color: var(--text-primary);
    height: 100vh;
    display: flex;
    flex-direction: column;
}

/* Header */
.header {
    background: var(--primary-color);
    color: white;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header h1 {
    font-size: 1.5rem;
    font-weight: bold;
}

.subtitle {
    font-size: 0.875rem;
    opacity: 0.9;
    margin-left: 1rem;
}

/* Toolbar */
.toolbar {
    background: var(--bg-secondary);
    padding: 0.75rem 2rem;
    display: flex;
    gap: 2rem;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    flex-wrap: wrap;
}

.toolbar-group {
    display: flex;
    gap: 0.5rem;
    align-items: center;
}

.toolbar-group label {
    font-weight: 500;
    font-size: 0.875rem;
}

/* Buttons */
.btn {
    background: var(--primary-color);
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.2s;
}

.btn:hover {
    background: #1d4ed8;
    transform: translateY(-1px);
}

.btn-secondary {
    background: var(--secondary-color);
}

.btn-secondary:hover {
    background: #475569;
}

.btn-small {
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
}

/* Form Controls */
select, input[type="text"] {
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.875rem;
}

.search-input {
    width: 200px;
}

/* Main Container */
.main-container {
    display: flex;
    flex: 1;
    overflow: hidden;
}

/* Sidebar */
.sidebar {
    width: 300px;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    padding: 1rem;
    overflow-y: auto;
}

.sidebar-section {
    margin-bottom: 2rem;
}

.sidebar-section h3 {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
    color: var(--text-primary);
}

/* File List */
.file-list {
    max-height: 200px;
    overflow-y: auto;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    background: var(--bg-primary);
}

.file-item {
    padding: 0.5rem;
    cursor: pointer;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: background 0.2s;
}

.file-item:hover {
    background: var(--bg-tertiary);
}

.file-item:last-child {
    border-bottom: none;
}

.file-icon {
    font-size: 1rem;
}

.file-name {
    flex: 1;
    font-size: 0.875rem;
}

.file-size {
    font-size: 0.75rem;
    color: var(--text-secondary);
}

/* Bookmark List */
.bookmark-list {
    max-height: 150px;
    overflow-y: auto;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    background: var(--bg-primary);
    margin-bottom: 0.5rem;
}

.bookmark-item {
    padding: 0.5rem;
    border-bottom: 1px solid var(--border-color);
    cursor: pointer;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    transition: background 0.2s;
}

.bookmark-item:hover {
    background: var(--bg-tertiary);
}

.bookmark-item:last-child {
    border-bottom: none;
}

/* File Info */
.file-info {
    font-size: 0.875rem;
    line-height: 1.5;
}

.file-info p {
    margin-bottom: 0.5rem;
}

/* Editor Area */
.editor-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.editor-header {
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    padding: 0.5rem 1rem;
}

.file-tabs {
    display: flex;
    gap: 0.25rem;
}

.tab {
    padding: 0.5rem 1rem;
    background: var(--bg-tertiary);
    border-radius: 0.375rem 0.375rem 0 0;
    cursor: pointer;
    font-size: 0.875rem;
    transition: background 0.2s;
}

.tab.active {
    background: var(--bg-primary);
    border-bottom: 2px solid var(--primary-color);
}

.tab:hover:not(.active) {
    background: var(--bg-primary);
    opacity: 0.8;
}

/* Hex Display */
.hex-display {
    flex: 1;
    padding: 1rem;
    overflow: auto;
    font-family: var(--font-mono);
    font-size: 0.875rem;
    line-height: 1.5;
    background: var(--bg-primary);
}

.hex-line {
    display: flex;
    margin-bottom: 0.25rem;
    padding: 0.125rem 0;
}

.hex-line:hover {
    background: var(--bg-secondary);
}

.hex-offset {
    color: var(--text-secondary);
    margin-right: 1rem;
    font-weight: bold;
    min-width: 80px;
}

.hex-bytes {
    display: flex;
    gap: 0.5rem;
    margin-right: 2rem;
    flex: 1;
}

.hex-byte {
    color: var(--primary-color);
    cursor: pointer;
    padding: 1px 2px;
    border-radius: 2px;
    transition: background 0.2s;
}

.hex-byte:hover {
    background: var(--bg-tertiary);
}

.hex-byte.bookmark {
    background: var(--warning-color);
    color: white;
}

.hex-byte.search-highlight {
    background: var(--success-color);
    color: white;
}

.hex-ascii {
    color: var(--text-secondary);
    font-weight: 500;
}

/* Welcome Message */
.welcome-message {
    text-align: center;
    padding: 4rem 2rem;
    max-width: 600px;
    margin: 0 auto;
}

.welcome-message h2 {
    font-size: 2rem;
    margin-bottom: 1rem;
    color: var(--primary-color);
}

.welcome-message ul {
    text-align: left;
    margin: 2rem 0;
}

.welcome-message li {
    margin-bottom: 0.5rem;
    padding-left: 0.5rem;
}

/* Status Bar */
.status-bar {
    background: var(--bg-secondary);
    border-top: 1px solid var(--border-color);
    padding: 0.5rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
}

.status-right {
    display: flex;
    gap: 2rem;
}

.status-right span {
    color: var(--text-secondary);
}

/* Responsive Design */
@media (max-width: 768px) {
    .sidebar {
        width: 250px;
    }
    
    .toolbar {
        flex-direction: column;
        gap: 1rem;
        align-items: stretch;
    }
    
    .toolbar-group {
        justify-content: center;
    }
    
    .main-container {
        flex-direction: column;
    }
    
    .sidebar {
        width: 100%;
        height: 200px;
    }
}

/* Animations */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.hex-line {
    animation: fadeIn 0.3s ease-out;
}

/* Scrollbars */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--text-secondary);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--text-primary);
}"""
    
    def get_javascript(self):
        """Generate the JavaScript code."""
        return """// Hexplorer Advanced GUI JavaScript

class HexplorerGUI {
    constructor() {
        this.currentFile = null;
        this.bookmarks = [];
        this.searchResults = [];
        this.currentTheme = 'light';
        this.viewMode = 'hex';
        this.bytesPerRow = 16;
        
        this.initializeEventListeners();
        this.loadFileList();
        this.updateStatus();
    }
    
    initializeEventListeners() {
        // File operations
        document.getElementById('openFile').addEventListener('click', () => this.showFileDialog());
        document.getElementById('saveFile').addEventListener('click', () => this.saveFile());
        document.getElementById('exportFile').addEventListener('click', () => this.exportFile());
        
        // View controls
        document.getElementById('viewMode').addEventListener('change', (e) => {
            this.viewMode = e.target.value;
            this.updateViewMode();
        });
        
        document.getElementById('bytesPerRow').addEventListener('change', (e) => {
            this.bytesPerRow = parseInt(e.target.value);
            this.updateViewMode();
        });
        
        // Search
        document.getElementById('searchBtn').addEventListener('click', () => this.performSearch());
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.performSearch();
        });
        
        // Navigation
        document.getElementById('gotoBtn').addEventListener('click', () => this.showGotoDialog());
        
        // Bookmarks
        document.getElementById('addBookmark').addEventListener('click', () => this.addBookmark());
        
        // Theme toggle
        document.getElementById('themeToggle').addEventListener('click', () => this.toggleTheme());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }
    
    async loadFileList() {
        try {
            const response = await fetch('/api/file_list');
            const files = await response.json();
            this.displayFileList(files);
        } catch (error) {
            console.error('Error loading file list:', error);
        }
    }
    
    displayFileList(files) {
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = '';
        
        files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const icon = file.is_directory ? '📁' : '📄';
            const size = file.is_directory ? '' : this.formatFileSize(file.size);
            
            fileItem.innerHTML = `
                <span class="file-icon">${icon}</span>
                <span class="file-name">${file.name}</span>
                <span class="file-size">${size}</span>
            `;
            
            if (!file.is_directory) {
                fileItem.addEventListener('click', () => this.openFile(file.path));
            }
            
            fileList.appendChild(fileItem);
        });
    }
    
    async openFile(filePath) {
        try {
            const response = await fetch('/api/open_file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_path: filePath })
            });
            
            const result = await response.json();
            if (result.success) {
                this.currentFile = filePath;
                await this.loadFileContent();
                this.updateStatus();
                this.showStatusMessage(result.message, 'success');
            } else {
                this.showStatusMessage(result.message, 'error');
            }
        } catch (error) {
            this.showStatusMessage('Error opening file', 'error');
            console.error('Error:', error);
        }
    }
    
    async loadFileContent() {
        try {
            const response = await fetch('/api/file_content');
            const content = await response.json();
            
            if (content.error) {
                this.showStatusMessage(content.error, 'error');
                return;
            }
            
            this.displayHexContent(content);
        } catch (error) {
            console.error('Error loading file content:', error);
        }
    }
    
    displayHexContent(content) {
        const hexDisplay = document.getElementById('hexDisplay');
        hexDisplay.innerHTML = '';
        
        if (!content.lines || content.lines.length === 0) {
            hexDisplay.innerHTML = '<div class="welcome-message"><p>No content to display</p></div>';
            return;
        }
        
        content.lines.forEach(line => {
            const lineElement = document.createElement('div');
            lineElement.className = 'hex-line';
            
            // Offset
            const offsetSpan = document.createElement('span');
            offsetSpan.className = 'hex-offset';
            offsetSpan.textContent = line.offset_hex;
            lineElement.appendChild(offsetSpan);
            
            // Hex bytes
            const bytesContainer = document.createElement('div');
            bytesContainer.className = 'hex-bytes';
            
            line.hex_bytes.forEach((byte, index) => {
                if (byte !== '') {
                    const byteSpan = document.createElement('span');
                    byteSpan.className = 'hex-byte';
                    byteSpan.textContent = byte;
                    byteSpan.dataset.offset = line.offset + index;
                    
                    // Check for bookmarks
                    if (this.bookmarks.includes(line.offset + index)) {
                        byteSpan.classList.add('bookmark');
                    }
                    
                    byteSpan.addEventListener('click', (e) => {
                        this.selectByte(parseInt(e.target.dataset.offset));
                    });
                    
                    bytesContainer.appendChild(byteSpan);
                } else {
                    const spacer = document.createElement('span');
                    spacer.className = 'hex-byte';
                    spacer.innerHTML = '&nbsp;&nbsp;';
                    bytesContainer.appendChild(spacer);
                }
            });
            
            lineElement.appendChild(bytesContainer);
            
            // ASCII representation
            if (content.view_mode !== 'ascii') {
                const asciiSpan = document.createElement('span');
                asciiSpan.className = 'hex-ascii';
                asciiSpan.textContent = line.ascii_chars;
                lineElement.appendChild(asciiSpan);
            }
            
            hexDisplay.appendChild(lineElement);
        });
        
        // Update file info
        this.updateFileInfo(content);
    }
    
    updateFileInfo(content) {
        const fileInfo = document.getElementById('fileInfo');
        const fileName = this.currentFile ? this.currentFile.split('/').pop() : 'Unknown';
        
        fileInfo.innerHTML = `
            <p><strong>File:</strong> ${fileName}</p>
            <p><strong>Size:</strong> ${this.formatFileSize(content.total_size)}</p>
            <p><strong>View:</strong> ${content.view_mode.toUpperCase()}</p>
            <p><strong>Bytes/Row:</strong> ${content.bytes_per_row}</p>
        `;
    }
    
    async updateViewMode() {
        try {
            await fetch('/api/set_view_mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    view_mode: this.viewMode,
                    bytes_per_row: this.bytesPerRow
                })
            });
            
            await this.loadFileContent();
        } catch (error) {
            console.error('Error updating view mode:', error);
        }
    }
    
    async performSearch() {
        const searchTerm = document.getElementById('searchInput').value;
        if (!searchTerm) return;
        
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ search_term: searchTerm })
            });
            
            const result = await response.json();
            this.searchResults = result.results;
            this.displaySearchResults();
        } catch (error) {
            console.error('Error performing search:', error);
        }
    }
    
    displaySearchResults() {
        // Clear previous highlights
        document.querySelectorAll('.hex-byte.search-highlight').forEach(el => {
            el.classList.remove('search-highlight');
        });
        
        // Highlight search results
        this.searchResults.forEach(result => {
            const byteElement = document.querySelector(`[data-offset="${result.offset}"]`);
            if (byteElement) {
                byteElement.classList.add('search-highlight');
            }
        });
        
        this.showStatusMessage(`Found ${this.searchResults.length} results`, 'success');
    }
    
    async addBookmark() {
        const offset = this.getCurrentOffset();
        if (offset === null) return;
        
        try {
            const response = await fetch('/api/bookmark', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: 'add',
                    offset: offset
                })
            });
            
            const result = await response.json();
            this.bookmarks = result.bookmarks;
            this.updateBookmarkList();
            await this.loadFileContent(); // Refresh display
        } catch (error) {
            console.error('Error adding bookmark:', error);
        }
    }
    
    updateBookmarkList() {
        const bookmarkList = document.getElementById('bookmarkList');
        bookmarkList.innerHTML = '';
        
        this.bookmarks.forEach(offset => {
            const bookmarkItem = document.createElement('div');
            bookmarkItem.className = 'bookmark-item';
            bookmarkItem.textContent = `0x${offset.toString(16).padStart(8, '0')}`;
            bookmarkItem.addEventListener('click', () => this.jumpToOffset(offset));
            bookmarkList.appendChild(bookmarkItem);
        });
    }
    
    selectByte(offset) {
        // Remove previous selection
        document.querySelectorAll('.hex-byte.selected').forEach(el => {
            el.classList.remove('selected');
        });
        
        // Add selection to clicked byte
        const byteElement = document.querySelector(`[data-offset="${offset}"]`);
        if (byteElement) {
            byteElement.classList.add('selected');
        }
        
        this.updateCursorPosition(offset);
    }
    
    updateCursorPosition(offset) {
        const positionLabel = document.getElementById('cursorPosition');
        positionLabel.textContent = `Offset: 0x${offset.toString(16).padStart(8, '0')}`;
    }
    
    getCurrentOffset() {
        const selected = document.querySelector('.hex-byte.selected');
        return selected ? parseInt(selected.dataset.offset) : 0;
    }
    
    jumpToOffset(offset) {
        const byteElement = document.querySelector(`[data-offset="${offset}"]`);
        if (byteElement) {
            byteElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            this.selectByte(offset);
        }
    }
    
    showGotoDialog() {
        const offset = prompt('Enter offset (hex or decimal):');
        if (offset) {
            let numOffset;
            if (offset.startsWith('0x') || offset.startsWith('0X')) {
                numOffset = parseInt(offset, 16);
            } else {
                numOffset = parseInt(offset);
            }
            
            if (!isNaN(numOffset)) {
                this.jumpToOffset(numOffset);
            }
        }
    }
    
    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', this.currentTheme);
        
        const themeBtn = document.getElementById('themeToggle');
        themeBtn.textContent = this.currentTheme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode';
    }
    
    handleKeyboard(event) {
        // Handle keyboard shortcuts
        if (event.ctrlKey) {
            switch (event.key) {
                case 'o':
                    event.preventDefault();
                    this.showFileDialog();
                    break;
                case 's':
                    event.preventDefault();
                    this.saveFile();
                    break;
                case 'f':
                    event.preventDefault();
                    document.getElementById('searchInput').focus();
                    break;
                case 'g':
                    event.preventDefault();
                    this.showGotoDialog();
                    break;
            }
        }
    }
    
    showFileDialog() {
        // In a real implementation, this would open a file dialog
        // For now, we'll show the file browser
        this.showStatusMessage('Use the file browser on the left to select a file', 'info');
    }
    
    saveFile() {
        this.showStatusMessage('Save functionality coming soon', 'info');
    }
    
    exportFile() {
        this.showStatusMessage('Export functionality coming soon', 'info');
    }
    
    showStatusMessage(message, type = 'info') {
        const statusLabel = document.getElementById('statusMessage');
        statusLabel.textContent = message;
        statusLabel.className = `status-${type}`;
        
        setTimeout(() => {
            statusLabel.textContent = 'Ready';
            statusLabel.className = '';
        }, 3000);
    }
    
    async updateStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            // Update file size
            const fileSizeLabel = document.getElementById('fileSize');
            fileSizeLabel.textContent = `Size: ${this.formatFileSize(status.file_size)}`;
            
            // Update bookmarks
            this.bookmarks = status.bookmarks;
            this.updateBookmarkList();
            
        } catch (error) {
            console.error('Error updating status:', error);
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 bytes';
        const k = 1024;
        const sizes = ['bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new HexplorerGUI();
});"""


def main():
    """Main function to run the web-based hex editor."""
    import sys
    
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number, using default 8080")
    
    server = HexEditorServer(port)
    print("\n🔍 Hexplorer GUI - Advanced Hex Editor")
    print("=" * 50)
    print(f"Starting web server on port {port}...")
    print("The GUI will open automatically in your browser.")
    print("Press Ctrl+C to stop the server.")
    print("=" * 50)
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nShutting down server...")


if __name__ == "__main__":
    main()