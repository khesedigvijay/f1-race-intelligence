"""
Vercel Serverless Function Entrypoint for F1 Race Intelligence Dashboard.
Enables serverless execution and health telemetry on Vercel platform.
"""

from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>F1 Race Intelligence API & Web Engine</title>
            <style>
                body {
                    background-color: #0B0C10;
                    color: #FFFFFF;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                }
                .card {
                    background: #161724;
                    border: 1px solid #282A3E;
                    border-top: 4px solid #E10600;
                    border-radius: 8px;
                    padding: 30px;
                    max-width: 600px;
                    text-align: center;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
                }
                h1 { color: #E10600; margin-top: 0; font-size: 1.8rem; }
                p { color: #A0A4B8; line-height: 1.6; }
                .code { background: #0E1017; padding: 10px; border-radius: 4px; font-family: monospace; color: #00D2BE; }
                .btn {
                    display: inline-block;
                    background: #E10600;
                    color: #FFFFFF;
                    text-decoration: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    font-weight: bold;
                    margin-top: 15px;
                }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🏎️ F1 RACE INTELLIGENCE ENGINE</h1>
                <p>Formula 1 Telemetry, Strategy Simulation & ML Lap Time Engine is operational.</p>
                <div class="code">Local Launch: streamlit run app.py</div>
                <p>For native live FastF1 WebSocket streaming, deploy seamlessly via Streamlit Community Cloud or Render.</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))
        return
