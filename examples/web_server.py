"""
Web server example for the DomainSale library.

This example demonstrates how to create a simple web server that displays domain sale information.
"""

import argparse
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from domainsale import get_domain_sale_status
from domainsale.api import DomainSaleOptions


class DomainSaleHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the DomainSale web server."""

    def do_GET(self):
        """Handle GET requests."""
        # Parse the URL
        parsed_url = urlparse(self.path)
        
        # Check if this is the root path
        if parsed_url.path == "/":
            self._serve_form()
            return
        
        # Check if this is a domain lookup request
        if parsed_url.path == "/lookup":
            # Parse the query parameters
            query_params = parse_qs(parsed_url.query)
            
            # Check if the domain parameter is present
            if "domain" not in query_params:
                self._serve_error("Missing domain parameter")
                return
            
            # Get the domain from the query parameters
            domain = query_params["domain"][0]
            
            # Check if the RDAP parameter is present
            enable_rdap = "rdap" in query_params
            
            # Look up the domain
            self._serve_lookup(domain, enable_rdap)
            return
        
        # If we get here, the path is not recognized
        self._serve_not_found()

    def _serve_form(self):
        """Serve the domain lookup form."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Domain Sale Lookup</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1 {
                    color: #333;
                }
                form {
                    margin: 20px 0;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }
                label {
                    display: block;
                    margin-bottom: 10px;
                }
                input[type="text"] {
                    width: 100%;
                    padding: 8px;
                    margin-bottom: 10px;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                }
                input[type="checkbox"] {
                    margin-right: 5px;
                }
                button {
                    padding: 8px 16px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #45a049;
                }
            </style>
        </head>
        <body>
            <h1>Domain Sale Lookup</h1>
            <p>Enter a domain name to check if it's for sale.</p>
            <form action="/lookup" method="get">
                <label for="domain">Domain:</label>
                <input type="text" id="domain" name="domain" placeholder="example.com" required>
                <label>
                    <input type="checkbox" id="rdap" name="rdap">
                    Enable RDAP cross-check
                </label>
                <button type="submit">Lookup</button>
            </form>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())

    def _serve_lookup(self, domain, enable_rdap):
        """Serve the domain lookup results."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        # Create options
        options = DomainSaleOptions(enable_rdap_check=enable_rdap)
        
        try:
            # Look up the domain
            response = get_domain_sale_status(domain, options)
            
            # Create the HTML response
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Domain Sale Lookup - {domain}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    h1 {{
                        color: #333;
                    }}
                    .result {{
                        margin: 20px 0;
                        padding: 20px;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                    }}
                    .domain-sale-info {{
                        margin: 10px 0;
                    }}
                    .domain-sale-error {{
                        color: red;
                        margin: 10px 0;
                    }}
                    .back-link {{
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <h1>Domain Sale Lookup - {domain}</h1>
                <div class="result">
                    {response.to_html()}
                </div>
                <div class="back-link">
                    <a href="/">Back to lookup form</a>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
        except Exception as e:
            self._serve_error(f"Error looking up domain: {e}")

    def _serve_error(self, message):
        """Serve an error message."""
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Domain Sale Lookup - Error</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1 {{
                    color: #333;
                }}
                .error {{
                    color: red;
                    margin: 20px 0;
                    padding: 20px;
                    border: 1px solid #f88;
                    border-radius: 5px;
                    background-color: #fee;
                }}
                .back-link {{
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <h1>Domain Sale Lookup - Error</h1>
            <div class="error">
                {message}
            </div>
            <div class="back-link">
                <a href="/">Back to lookup form</a>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())

    def _serve_not_found(self):
        """Serve a 404 Not Found response."""
        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Domain Sale Lookup - Not Found</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1 {
                    color: #333;
                }
                .error {
                    color: red;
                    margin: 20px 0;
                    padding: 20px;
                    border: 1px solid #f88;
                    border-radius: 5px;
                    background-color: #fee;
                }
                .back-link {
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <h1>Domain Sale Lookup - Not Found</h1>
            <div class="error">
                The requested page was not found.
            </div>
            <div class="back-link">
                <a href="/">Back to lookup form</a>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Start a web server for domain sale lookups."
    )
    
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind to (default: localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Start the web server."""
    args = parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create the HTTP server
    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, DomainSaleHandler)
    
    # Start the server
    logging.info(f"Starting server on {args.host}:{args.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Stopping server")
        httpd.server_close()


if __name__ == "__main__":
    main()
