import argparse
import asyncio
import json
import logging
import os
import secrets
import signal
import sys
import threading
import time
import urllib.parse
import webbrowser
from typing import Any, Dict, Optional
import requests
from dotenv import load_dotenv

# Set up module-specific logger with DEBUG level
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Logger handler will be configured based on verbose flag
_verbose_mode = False

def setup_logging(verbose: bool = False):
    """Configure logging based on verbose flag."""
    global _verbose_mode
    _verbose_mode = verbose
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    if verbose:
        # Create handler for stdout output when verbose mode is enabled
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(filename)s:%(lineno)d - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

# Load environment variables
load_dotenv()

# OAuth configuration - will be set from command line arguments
CLIENT_ID = None
CLIENT_SECRET = None
AUTH0_DOMAIN = None

# OAuth endpoints - will be set after parsing arguments
AUTHORIZATION_URL = None
TOKEN_URL = None
USERINFO_URL = None

# Redirect URI for local development - will be set after parsing arguments
REDIRECT_URI = None

# Global variable to track callback server for cleanup
_callback_server_instance = None

def signal_handler(signum, frame):
    """Handle SIGINT (Ctrl+C) to clean up resources."""
    global _callback_server_instance
    print("\n⚡ Shutting down gracefully...")
    
    if _callback_server_instance:
        print("🛑 Stopping callback server...")
        try:
            _callback_server_instance.stop()
        except Exception as e:
            logger.debug(f"Error during server cleanup: {e}")
        finally:
            _callback_server_instance = None
    
    print("👋 Goodbye!")
    sys.exit(0)

class OAuth2Client:
    """Simple OAuth2 client for Auth0 authentication."""
    
    def __init__(self, client_id: str, client_secret: str, auth0_domain: str, port: int = 8080):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth0_domain = auth0_domain
        self.authorization_url = f"https://{auth0_domain}/authorize"
        self.token_url = f"https://{auth0_domain}/oauth/token"
        self.userinfo_url = f"https://{auth0_domain}/userinfo"
        self.redirect_uri = f"http://127.0.0.1:{port}/callback"
        
    def generate_auth_url(self, state: str) -> str:
        """Generate the authorization URL for OAuth flow."""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'openid profile email',
            'state': state,
        }
        
        query_string = urllib.parse.urlencode(params)
        auth_url = f"{self.authorization_url}?{query_string}"
        
        logger.debug(f"Generated auth URL: {auth_url}")
        return auth_url
    
    def exchange_code_for_token(self, code: str) -> Optional[Dict]:
        """Exchange authorization code for access token."""
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri,
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        logger.debug("Exchanging authorization code for token...")
        
        try:
            response = requests.post(self.token_url, data=token_data, headers=headers)
            response.raise_for_status()
            
            token_response = response.json()
            logger.debug(f"Token response received: {list(token_response.keys())}")
            
            return token_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Token exchange failed: {e}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get user information using access token."""
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            response = requests.get(self.userinfo_url, headers=headers)
            response.raise_for_status()
            
            user_info = response.json()
            logger.debug(f"User info received: {list(user_info.keys())}")
            
            return user_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get user info: {e}")
            return None


class CallbackServer:
    """Local server to handle OAuth callback."""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.callback_code = None
        self.server_ready = threading.Event()
        self.code_received = threading.Event()
        self.server_error = threading.Event()
        self.error_message = None
        self.httpd = None
        self.server_thread = None
        
    def start(self):
        """Start the callback server in a separate thread."""
        import http.server
        import socketserver
        from urllib.parse import urlparse, parse_qs
        
        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def __init__(self, callback_server, *args, **kwargs):
                self.callback_server = callback_server
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                if self.path.startswith('/callback'):
                    # Parse the callback URL
                    parsed_url = urlparse(self.path)
                    query_params = parse_qs(parsed_url.query)
                    
                    if 'code' in query_params:
                        self.callback_server.callback_code = query_params['code'][0]
                        self.callback_server.code_received.set()
                        
                        # Send success response
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.wfile.write(b'''
                        <html>
                        <body>
                            <h2>Authentication Successful!</h2>
                            <p>You can close this window and return to the application.</p>
                            <script>window.close();</script>
                        </body>
                        </html>
                        ''')
                    else:
                        # Handle error
                        error = query_params.get('error', ['Unknown error'])[0]
                        self.send_response(400)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.wfile.write(f'''
                        <html>
                        <body>
                            <h2>Authentication Failed</h2>
                            <p>Error: {error}</p>
                        </body>
                        </html>
                        '''.encode())
                        self.callback_server.code_received.set()  # Signal completion even on error
                elif self.path == '/' or self.path == '':
                    # Default handler for root path
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'hello from callback server')
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                # Suppress default server logging
                if _verbose_mode:
                    logger.debug(f"Server: {format % args}")
        
        # Create handler with access to callback_server
        def handler_factory(*args, **kwargs):
            return CallbackHandler(self, *args, **kwargs)
        
        def run_server():
            try:
                # Bind to all interfaces so it works with the IP address
                self.httpd = socketserver.TCPServer(("0.0.0.0", self.port), handler_factory)
                self.server_ready.set()
                logger.debug(f"Local server started on 0.0.0.0:{self.port}")
                
                self.httpd.timeout = 0.5  # Set timeout for handle_request
                
                while not self.code_received.is_set():
                    self.httpd.handle_request()
                
                logger.debug("Local server stopped")
            except OSError as e:
                if e.errno == 98 or "Address already in use" in str(e):  # Port in use
                    self.error_message = f"Port {self.port} is already in use. Please choose a different port or stop the service using port {self.port}."
                    logger.error(self.error_message)
                else:
                    self.error_message = f"Failed to bind to port {self.port}: {e}"
                    logger.error(self.error_message)
                self.server_error.set()
                self.server_ready.set()  # Signal ready even on error
            except Exception as e:
                self.error_message = f"Server error: {e}"
                logger.error(self.error_message)
                self.server_error.set()
                self.server_ready.set()  # Signal ready even on error
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Wait for server to be ready
        if not self.server_ready.wait(timeout=5):
            raise RuntimeError("Failed to start local server")
        
        # Check if server had an error during startup
        if self.server_error.is_set():
            raise RuntimeError(self.error_message or "Unknown server error")
    
    def wait_for_callback(self, timeout: int) -> Optional[str]:
        """Wait for OAuth callback and return authorization code."""
        logger.debug(f"wait_for_callback")
        if self.code_received.wait(timeout=timeout):
            return self.callback_code
        return None
    
    def stop(self):
        """Stop the callback server."""
        logger.debug("Stopping callback server...")
        
        # Signal the server to stop accepting requests
        self.code_received.set()
        
        # Shutdown the HTTP server
        if self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
                logger.debug("HTTP server stopped")
            except Exception as e:
                logger.debug(f"Error stopping HTTP server: {e}")
        
        # Wait for server thread to finish
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2)
            if self.server_thread.is_alive():
                logger.warning("Server thread did not stop gracefully")


async def authenticate(client_id: str, client_secret: str, auth0_domain: str, callback_server, port: int = 8080) -> Optional[Dict]:
    """Complete OAuth authentication flow."""
    
    # Create OAuth client
    oauth_client = OAuth2Client(client_id, client_secret, auth0_domain, port=port)
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Generate authorization URL
    auth_url = oauth_client.generate_auth_url(state)
    
    print(f"🔗 Opening browser for authentication...")
    print(f"If the browser doesn't open automatically, visit: {auth_url}")
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Wait for callback from the already-running server
    print("⏳ Waiting for authentication callback...")
    authorization_code = callback_server.wait_for_callback(timeout=300)
    
    if not authorization_code:
        print("❌ Authentication failed: No authorization code received")
        return None
    
    logger.debug(f"Received authorization code: {authorization_code[:10]}...")
    
    # Exchange code for token
    print("🔄 Exchanging authorization code for access token...")
    token_response = oauth_client.exchange_code_for_token(authorization_code)
    
    if not token_response:
        print("❌ Failed to exchange authorization code for token")
        return None
    
    print("✅ Authentication successful!")
    
    # Get user info
    if 'access_token' in token_response:
        print("👤 Fetching user information...")
        user_info = oauth_client.get_user_info(token_response['access_token'])
        if user_info:
            print(f"Welcome, {user_info.get('name', 'User')}!")
            token_response['user_info'] = user_info
    
    return token_response


def main():
    """Main function."""
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description="Auth0 OAuth2 client example")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Enable verbose logging to stdout")
    parser.add_argument("--client-id", required=True,
                       help="OAuth2 client ID")
    parser.add_argument("--client-secret", required=True,
                       help="OAuth2 client secret")
    parser.add_argument("--auth0-domain", required=True,
                       help="Auth0 domain (e.g., example.us.auth0.com)")
    parser.add_argument("--port", type=int, default=8080,
                       help="Local callback server port (default: 8080)")
    args = parser.parse_args()
    
    # Configure logging based on verbose flag
    setup_logging(args.verbose)
    
    print("🚀 Starting Auth0 OAuth2 authentication...")
    print(f"📍 Auth0 Domain: {args.auth0_domain}")
    print(f"🆔 Client ID: {args.client_id}")
    print()
    
    # Start local server FIRST in a separate thread
    print("🌐 Starting local callback server...")
    callback_server = CallbackServer(port=args.port)
    callback_server.start()
    print(f"✅ Local server ready on http://127.0.0.1:{args.port}")
    global _callback_server_instance
    _callback_server_instance = callback_server
    time.sleep(5)

    # Run authentication
    logger.debug("Starting OAuth authentication process...")
    result = asyncio.run(authenticate(args.client_id, args.client_secret, args.auth0_domain, callback_server, port=args.port))
    # time.sleep(30)

    if result:
        print()
        print("📋 Authentication Results:")
        print(f"   Access Token: {result.get('access_token', 'N/A')[:50]}...")
        print(f"   Token Type: {result.get('token_type', 'N/A')}")
        print(f"   Expires In: {result.get('expires_in', 'N/A')} seconds")
        
        if 'id_token' in result:
            print(f"   ID Token: {result['id_token'][:50]}...")
        
        if 'user_info' in result:
            user = result['user_info']
            print(f"   User: {user.get('name', 'N/A')} ({user.get('email', 'N/A')})")
    else:
        print("💥 Authentication failed!")
        # exit(1)


if __name__ == "__main__":
    main()