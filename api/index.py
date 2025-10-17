"""
Vercel Serverless Function for receiving exam tasks
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import asyncio
from datetime import datetime

# Your secret from the Google Form
YOUR_SECRET = os.environ.get("STUDENT_SECRET", "your-secret-here")

class handler(BaseHTTPRequestHandler):
    """
    Vercel serverless function handler
    """
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/api/health' or self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"message": "Student API Endpoint - Ready"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/receive-task' or self.path == '/receive-task':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # Validate
                required = ["email", "secret", "task", "round", "nonce", "brief", "checks", "evaluation_url"]
                for field in required:
                    if field not in data:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": f"Missing {field}"}).encode())
                        return
                
                # Verify secret
                if data["secret"] != YOUR_SECRET:
                    self.send_response(403)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Invalid secret"}).encode())
                    return
                
                print(f"✅ Task received: {data['task']} Round {data['round']}")
                
                # Send 200 immediately
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "accepted",
                    "task": data["task"],
                    "round": data["round"]
                }).encode())
                
                # Process task
                try:
                    from builder import build_and_deploy
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(build_and_deploy(data))
                    loop.close()
                    print(f"✅ Task completed: {result}")
                except Exception as e:
                    print(f"❌ Processing error: {e}")
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
