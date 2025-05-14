#!/usr/bin/env python3
# Simple HTTP server to display logger content
import http.server
import socketserver
import os

PORT = 8080
ALERTS_DIR = os.path.dirname(os.path.abspath(__file__))
OU3_LOGGER = os.path.join(ALERTS_DIR, "OU3.logger")

class LoggerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OU3.logger Contents</title>
            <style>
                body {{ font-family: monospace; line-height: 1.5; padding: 20px; }}
                h1 {{ color: #333; }}
                pre {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                .highlight {{ background-color: #ffffcc; }}
                .odds-table {{ margin-top: 20px; }}
                .odds-row {{ white-space: pre; }}
            </style>
        </head>
        <body>
            <h1>OU3.logger Contents (Last Updated: {os.path.getmtime(OU3_LOGGER)})</h1>
            <pre>"""
            
        # Add the file contents
        try:
            with open(OU3_LOGGER, 'r') as f:
                logger_content = f.read()
                # Highlight the betting odds section
                betting_section = False
                for line in logger_content.split('\n'):
                    if "--- MATCH BETTING ODDS ---" in line:
                        betting_section = True
                        html_content += f'<div class="highlight">{line}</div>'
                    elif "--- MATCH ENVIRONMENT ---" in line:
                        betting_section = False
                        html_content += line + "\n"
                    elif betting_section and "│ " in line:
                        html_content += f'<div class="odds-row highlight">{line}</div>'
                    else:
                        html_content += line + "\n"
        except Exception as e:
            html_content += f"Error reading file: {e}"
            
        html_content += """
            </pre>
            
            <h2>Column Alignment Explanation</h2>
            <p>We've fixed the alignment by adding a space after "Away:" to match the width of "Under:"</p>
            <div class="odds-table">
                <pre class="highlight">--- MATCH BETTING ODDS ---
│ Home: +195 │ Draw: +350 │ <strong>Away : +400</strong> │ (@4')
│ Home: +180 │ Hcap: -1.0 │ <strong>Away : +210</strong> │ (@4')
│ Over: +190 │ Line: 3.5 │ <strong>Under: +200</strong> │ (@4')</pre>
            </div>
            <p>Notice that "Away :" (with the extra space) now has the same width as "Under:"</p>
        </body>
        </html>
        """
        
        self.wfile.write(html_content.encode())
        
    def log_message(self, format, *args):
        # Suppress log messages
        return

print(f"Starting server at http://localhost:{PORT}")
with socketserver.TCPServer(("", PORT), LoggerHandler) as httpd:
    print("Press Ctrl+C to stop the server")
    httpd.serve_forever()
