"""
Renderer module for safe HTML rendering of domain sale information.

This module handles safe HTML rendering of domain sale information.
It addresses the high severity issue of Content Injection / XSS.
"""

import html
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class HTMLRenderer:
    """
    Safe HTML renderer for domain sale information.
    """

    def __init__(self):
        """Initialize the HTML renderer."""
        pass

    def render_sale_info(self, sale_info: Dict[str, Any]) -> str:
        """
        Render domain sale information as safe HTML.

        Args:
            sale_info: The domain sale information to render.

        Returns:
            The rendered HTML.
        """
        # Start with an empty HTML string
        html_output = []
        
        # Add the domain name if available
        if "domain" in sale_info:
            domain = self._escape(sale_info["domain"])
            html_output.append(f"<h2>Domain for Sale: {domain}</h2>")
        else:
            html_output.append("<h2>Domain for Sale</h2>")
        
        # Add a container div
        html_output.append('<div class="domain-sale-info">')
        
        # Add the price if available
        if sale_info.get("price"):
            price = self._escape(sale_info["price"])
            html_output.append(f'<div class="sale-price"><strong>Price:</strong> {price}</div>')
        
        # Add the contact information if available
        if sale_info.get("contact"):
            contact = self._escape(sale_info["contact"])
            # Extract email from mailto: URI
            if contact.startswith("mailto:"):
                email = self._escape(contact[7:])
                html_output.append(
                    f'<div class="sale-contact"><strong>Contact:</strong> '
                    f'<a href="{contact}">{email}</a></div>'
                )
            else:
                html_output.append(
                    f'<div class="sale-contact"><strong>Contact:</strong> {contact}</div>'
                )
        
        # Add the URL if available
        if sale_info.get("url"):
            url = self._escape(sale_info["url"])
            html_output.append(
                f'<div class="sale-url"><strong>More Info:</strong> '
                f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a></div>'
            )
        
        # Add the expiration date if available
        if sale_info.get("expires"):
            expires = self._escape(sale_info["expires"])
            html_output.append(f'<div class="sale-expires"><strong>Expires:</strong> {expires}</div>')
        
        # Close the container div
        html_output.append('</div>')
        
        return "\n".join(html_output)

    def render_error(self, error_message: str) -> str:
        """
        Render an error message as safe HTML.

        Args:
            error_message: The error message to render.

        Returns:
            The rendered HTML.
        """
        error_message = self._escape(error_message)
        return f'<div class="domain-sale-error">{error_message}</div>'

    def _escape(self, text: str) -> str:
        """
        Escape HTML special characters in a string.

        Args:
            text: The string to escape.

        Returns:
            The escaped string.
        """
        return html.escape(text, quote=True)


class ConsoleRenderer:
    """
    Console renderer for domain sale information.
    """

    def __init__(self):
        """Initialize the console renderer."""
        pass

    def render_sale_info(self, sale_info: Dict[str, Any]) -> str:
        """
        Render domain sale information as plain text for console output.

        Args:
            sale_info: The domain sale information to render.

        Returns:
            The rendered text.
        """
        # Start with an empty text string
        text_output = []
        
        # Add the domain name if available
        if "domain" in sale_info:
            domain = sale_info["domain"]
            text_output.append(f"Domain for Sale: {domain}")
        else:
            text_output.append("Domain for Sale")
        
        text_output.append("-" * 40)
        
        # Add the price if available
        if sale_info.get("price"):
            price = sale_info["price"]
            text_output.append(f"Price: {price}")
        
        # Add the contact information if available
        if sale_info.get("contact"):
            contact = sale_info["contact"]
            # Extract email from mailto: URI
            if contact.startswith("mailto:"):
                email = contact[7:]
                text_output.append(f"Contact: {email}")
            else:
                text_output.append(f"Contact: {contact}")
        
        # Add the URL if available
        if sale_info.get("url"):
            url = sale_info["url"]
            text_output.append(f"More Info: {url}")
        
        # Add the expiration date if available
        if sale_info.get("expires"):
            expires = sale_info["expires"]
            text_output.append(f"Expires: {expires}")
        
        # Add the source if available
        if sale_info.get("source"):
            source = ", ".join(sale_info["source"])
            text_output.append(f"Source: {source}")
        
        return "\n".join(text_output)

    def render_error(self, error_message: str) -> str:
        """
        Render an error message as plain text.

        Args:
            error_message: The error message to render.

        Returns:
            The rendered text.
        """
        return f"Error: {error_message}"
