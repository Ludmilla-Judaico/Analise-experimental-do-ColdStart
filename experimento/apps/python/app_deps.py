import json, hashlib, requests
from cryptography.fernet import Fernet
from http.server import BaseHTTPRequestHandler, HTTPServer

d = json.loads('{"a": 1, "b": [1, 2, 3]}')                  # parser JSON
hashlib.sha256(json.dumps(d).encode()).hexdigest()           # hash
Fernet(Fernet.generate_key()).encrypt(b"x")                  # criptografia
requests.Session()                                           # cliente HTTP

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200) 
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *a):
        pass

HTTPServer(("0.0.0.0", 8080), H).serve_forever()