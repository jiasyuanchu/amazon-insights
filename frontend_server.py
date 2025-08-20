#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple HTTP server for Amazon Insights Frontend Dashboard
Serves the competitive analysis dashboard on localhost:8888
"""

import os
import http.server
import socketserver
import webbrowser
from threading import Timer

# Configuration
PORT = 8888
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), 'frontend')

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler with CORS support"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)
    
    def end_headers(self):
        """Add CORS headers to allow API requests"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"📊 Dashboard: {format % args}")

def open_browser():
    """Open browser after a short delay"""
    webbrowser.open(f'http://localhost:{PORT}')

def main():
    print("🚀 Amazon Insights - Competitive Analysis Dashboard")
    print("=" * 60)
    print(f"📊 Starting frontend server on port {PORT}...")
    
    # Check if frontend directory exists
    if not os.path.exists(FRONTEND_DIR):
        print(f"❌ Frontend directory not found: {FRONTEND_DIR}")
        print("Please make sure the frontend files are in the correct location.")
        exit(1)
    
    # Check if main files exist
    required_files = ['index.html', 'styles.css', 'script.js']
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(FRONTEND_DIR, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        exit(1)
    
    try:
        # Create server
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"✅ Server started successfully!")
            print(f"🌐 Dashboard URL: http://localhost:{PORT}")
            print(f"📁 Serving files from: {FRONTEND_DIR}")
            print()
            print("📝 Important Notes:")
            print("   • Make sure the API server is running on localhost:8001")
            print("   • Create competitive groups via API before using dashboard")
            print("   • Use Ctrl+C to stop the server")
            print()
            
            # Open browser after 2 seconds
            Timer(2.0, open_browser).start()
            print("🚀 Opening browser in 2 seconds...")
            print()
            print("📊 Dashboard Ready! Waiting for requests...")
            print("-" * 60)
            
            # Start serving
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 Shutting down dashboard server...")
        print("✅ Server stopped successfully!")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use!")
            print("Please stop any other services using this port or change the PORT variable.")
        else:
            print(f"❌ Server error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()