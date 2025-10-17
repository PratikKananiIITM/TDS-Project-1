from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Your secret from the Google Form
YOUR_SECRET = os.environ.get("STUDENT_SECRET", "your-secret-here")

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        if self.path in ['/api/health', '/health', '/']:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "message": "API is running"
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        if self.path in ['/api/receive-task', '/receive-task']:
            try:
                # Read request body
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # Validate required fields
                required = ["email", "secret", "task", "round", "nonce", "brief", "checks", "evaluation_url"]
                for field in required:
                    if field not in data:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": f"Missing field: {field}"}).encode())
                        return
                
                # Verify secret
                if data["secret"] != YOUR_SECRET:
                    self.send_response(403)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Invalid secret"}).encode())
                    return
                
                # Log task received
                print(f"[{datetime.now()}] Task received: {data['task']} Round {data['round']}")
                
                # Send 200 immediately
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "accepted",
                    "task": data["task"],
                    "round": data["round"]
                }).encode())
                
                # Process task in background
                try:
                    import asyncio
                    from builder import build_and_deploy
                    
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(build_and_deploy(data))
                    loop.close()
                    
                    print(f"[{datetime.now()}] Task completed: {result}")
                except Exception as e:
                    print(f"[{datetime.now()}] Processing error: {str(e)}")
                    import traceback
                    traceback.print_exc()
                
            except json.JSONDecodeError as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())
