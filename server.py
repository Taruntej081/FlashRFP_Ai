import os
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from admin_db import add_lead

class CustomRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Always serve index.html for root path or directory root
        if path == "/" or path == "":
            return os.path.join(os.path.dirname(__file__), "index.html")
        return super().translate_path(path)

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        
        if parsed_url.path == "/api/book-demo":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                first_name = data.get("first_name", "")
                last_name = data.get("last_name", "")
                email = data.get("email", "")
                phone = data.get("phone", "")
                sector = data.get("sector", "")
                rfps = data.get("rfps", "")
                
                if not first_name or not email:
                    self.send_error_response(400, "Missing required parameters (first_name, email)")
                    return
                
                success = add_lead(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    sector=sector,
                    rfps=rfps,
                    source="Demo Booking Form"
                )
                
                if success:
                    self.send_success_response({"message": "Demo request recorded successfully"})
                else:
                    self.send_success_response({"message": "Demo request already registered"})
            except Exception as e:
                self.send_error_response(500, f"Internal server error: {e}")
                
        elif parsed_url.path == "/api/upgrade":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                email = data.get("email", "")
                plan = data.get("plan", "")
                
                if not email or not plan:
                    self.send_error_response(400, "Missing required parameters (email, plan)")
                    return
                
                success = add_lead(
                    first_name="Pending",
                    last_name="Upgrade",
                    email=email,
                    phone="",
                    sector=plan,
                    rfps="",
                    source=f"Pricing Upgrade ({plan})"
                )
                
                if success:
                    self.send_success_response({"message": "Upgrade intent recorded successfully"})
                else:
                    self.send_success_response({"message": "Upgrade intent already registered"})
            except Exception as e:
                self.send_error_response(500, f"Internal server error: {e}")
        else:
            self.send_error_response(404, "API endpoint not found")

    def send_success_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))

    def do_OPTIONS(self):
        # Support CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, CustomRequestHandler)
    print(f"Serving B2B Landing Page and API endpoints on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    import sys
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run(port)
