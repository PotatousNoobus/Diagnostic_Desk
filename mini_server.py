import http.server
import socketserver

PORT = 8080
LOG_FILE = "system_errors.log"

class HoneypotHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.capture_and_log("GET")

    def do_POST(self):
        self.capture_and_log("POST")

    def capture_and_log(self, method):
        client_ip = self.client_address[0]
        request_path = self.path
        user_agent = self.headers.get('User-Agent', 'Unknown')
        
        request_line = f"{method} {request_path} {self.request_version}"
        log_entry = f"[INFO] {client_ip} - {request_line} User-Agent: {user_agent}\n"
        
        print(log_entry.strip())
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
            
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        # Explicitly force the connection to close so browsers can't hijack it
        self.send_header('Connection', 'close') 
        self.end_headers()
        self.wfile.write(b"OK")
        
    def log_message(self, format, *args):
        pass

# Upgraded to ThreadingTCPServer to handle concurrent knocks
server = socketserver.ThreadingTCPServer(("", PORT), HoneypotHandler)
server.allow_reuse_address = True
server.daemon_threads = True

print(f"Honeypot active! Listening on port {PORT}...")
try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down server cleanly.")
    server.server_close()