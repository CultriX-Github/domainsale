"""
RDAP client module for cross-checking domain sale status.

This module handles RDAP lookups to cross-check the "for-sale" status of a domain.
It addresses the medium severity issue of Ambiguity & Abuse Potential.
"""

import logging
import requests
from typing import Dict, Any, Optional, List, Tuple
import time

from .exceptions import RDAPError, TimeoutError

logger = logging.getLogger(__name__)

# Constants
RDAP_BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"
FOR_SALE_STATUS_TAG = "for-sale"
DEFAULT_TIMEOUT = 5  # seconds


class RDAPClient:
    """
    RDAP client for cross-checking domain sale status.
    """

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the RDAP client.

        Args:
            timeout: Timeout for RDAP queries in seconds.
        """
        self.timeout = timeout
        self._bootstrap_servers = {}
        self._bootstrap_timestamp = 0
        self._bootstrap_ttl = 3600  # 1 hour

    def check_for_sale_status(self, domain: str) -> bool:
        """
        Check if a domain has a "for-sale" status tag in its RDAP data.

        Args:
            domain: The domain name to check.

        Returns:
            True if the domain has a "for-sale" status tag, False otherwise.

        Raises:
            RDAPError: If the RDAP lookup fails.
            TimeoutError: If the RDAP query times out.
        """
        try:
            # Get RDAP data for the domain
            rdap_data = self._get_rdap_data(domain)
            
            # Check if the domain has a "for-sale" status tag
            if "status" in rdap_data and isinstance(rdap_data["status"], list):
                return FOR_SALE_STATUS_TAG in rdap_data["status"]
            
            return False
        except requests.Timeout:
            logger.error(f"RDAP query for {domain} timed out")
            raise TimeoutError(f"RDAP query for {domain} timed out")
        except RDAPError:
            # Re-raise RDAPError
            raise
        except Exception as e:
            logger.error(f"Error checking RDAP status for {domain}: {e}")
            raise RDAPError(f"Error checking RDAP status for {domain}: {e}")

    def _get_rdap_data(self, domain: str) -> Dict[str, Any]:
        """
        Get RDAP data for a domain.

        Args:
            domain: The domain name to get RDAP data for.

        Returns:
            The RDAP data for the domain.

        Raises:
            RDAPError: If the RDAP lookup fails.
        """
        try:
            # Get the RDAP server URL for the domain
            rdap_server_url = self._get_rdap_server_url(domain)
            if not rdap_server_url:
                logger.warning(f"No RDAP server found for {domain}")
                raise RDAPError(f"No RDAP server found for {domain}")
            
            # Construct the RDAP query URL
            rdap_query_url = f"{rdap_server_url}/domain/{domain}"
            
            # Make the RDAP query
            response = requests.get(
                rdap_query_url,
                headers={"Accept": "application/rdap+json"},
                timeout=self.timeout
            )
            
            # Check if the query was successful
            if response.status_code != 200:
                logger.warning(f"RDAP query for {domain} failed with status code {response.status_code}")
                raise RDAPError(f"RDAP query for {domain} failed with status code {response.status_code}")
            
            # Parse the RDAP data
            rdap_data = response.json()
            
            return rdap_data
        except requests.RequestException as e:
            logger.warning(f"RDAP query for {domain} failed: {e}")
            raise RDAPError(f"RDAP query for {domain} failed: {e}")
        except Exception as e:
            logger.error(f"Error getting RDAP data for {domain}: {e}")
            raise RDAPError(f"Error getting RDAP data for {domain}: {e}")

    def _get_rdap_server_url(self, domain: str) -> Optional[str]:
        """
        Get the RDAP server URL for a domain.

        Args:
            domain: The domain name to get the RDAP server URL for.

        Returns:
            The RDAP server URL for the domain, or None if no server is found.

        Raises:
            RDAPError: If the RDAP bootstrap lookup fails.
        """
        try:
            # Check if we need to refresh the bootstrap servers
            current_time = time.time()
            if not self._bootstrap_servers or current_time - self._bootstrap_timestamp > self._bootstrap_ttl:
                self._refresh_bootstrap_servers()
            
            # Get the TLD from the domain
            tld = domain.split(".")[-1]
            
            # Check if we have an RDAP server for this TLD
            if tld in self._bootstrap_servers:
                return self._bootstrap_servers[tld][0]
            
            # If not, try to find a server for the domain
            for suffix, servers in self._bootstrap_servers.items():
                if domain.endswith(f".{suffix}"):
                    return servers[0]
            
            return None
        except Exception as e:
            logger.error(f"Error getting RDAP server URL for {domain}: {e}")
            raise RDAPError(f"Error getting RDAP server URL for {domain}: {e}")

    def _refresh_bootstrap_servers(self) -> None:
        """
        Refresh the RDAP bootstrap servers.

        Raises:
            RDAPError: If the RDAP bootstrap lookup fails.
        """
        try:
            # Get the RDAP bootstrap data
            response = requests.get(RDAP_BOOTSTRAP_URL, timeout=self.timeout)
            
            # Check if the query was successful
            if response.status_code != 200:
                logger.warning(f"RDAP bootstrap lookup failed with status code {response.status_code}")
                raise RDAPError(f"RDAP bootstrap lookup failed with status code {response.status_code}")
            
            # Parse the bootstrap data
            bootstrap_data = response.json()
            
            # Extract the RDAP server URLs
            self._bootstrap_servers = {}
            for service in bootstrap_data.get("services", []):
                if len(service) >= 2:
                    for tld in service[0]:
                        self._bootstrap_servers[tld] = service[1]
            
            # Update the timestamp
            self._bootstrap_timestamp = time.time()
        except requests.RequestException as e:
            logger.warning(f"RDAP bootstrap lookup failed: {e}")
            raise RDAPError(f"RDAP bootstrap lookup failed: {e}")
        except Exception as e:
            logger.error(f"Error refreshing RDAP bootstrap servers: {e}")
            raise RDAPError(f"Error refreshing RDAP bootstrap servers: {e}")
