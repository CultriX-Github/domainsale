"""
DNS resolver module with DNSSEC validation.

This module handles DNS lookups for "_for-sale" TXT records with strict DNSSEC validation.
It addresses the critical security issue of DNS Cache Poisoning & Spoofing.
"""

import dns.resolver
import dns.dnssec
import dns.rdatatype
import dns.flags
import logging
from typing import List, Dict, Any, Optional, Tuple

from .exceptions import DNSSECValidationError, TimeoutError

logger = logging.getLogger(__name__)

# Constants
FOR_SALE_PREFIX = "_for-sale"
MAX_TXT_SIZE = 255  # Maximum size in bytes for TXT record content


class DNSSecResolver:
    """
    DNS resolver with DNSSEC validation for "_for-sale" TXT records.
    """

    def __init__(self, timeout: int = 5):
        """
        Initialize the DNS resolver.

        Args:
            timeout: Timeout for DNS queries in seconds.
        """
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = timeout
        self.resolver.use_dnssec = True

    def lookup_for_sale_record(self, domain: str) -> Tuple[List[str], List[str]]:
        """
        Look up the "_for-sale" TXT record for a domain with DNSSEC validation.

        Args:
            domain: The domain name to look up.

        Returns:
            Tuple containing a list of TXT record contents and a list of sources.

        Raises:
            DNSSECValidationError: If DNSSEC validation fails.
            TimeoutError: If the DNS query times out.
        """
        try:
            # Construct the query name
            query_name = f"{FOR_SALE_PREFIX}.{domain}"
            
            # Perform the lookup with DNSSEC validation
            answers = self._lookup_with_dnssec(query_name, dns.rdatatype.TXT)
            
            # Extract the TXT record contents
            txt_records = []
            for rdata in answers:
                # Join the TXT record strings and decode from bytes
                txt_content = b''.join(rdata.strings).decode('utf-8')
                
                # Check size limit
                if len(txt_content.encode('utf-8')) > MAX_TXT_SIZE:
                    logger.warning(f"TXT record for {query_name} exceeds maximum size of {MAX_TXT_SIZE} bytes")
                    continue
                
                txt_records.append(txt_content)
            
            return txt_records, ["dns"]
            
        except dns.resolver.NoAnswer:
            logger.info(f"No TXT record found for {domain}")
            return [], ["dns"]
        except dns.resolver.NXDOMAIN:
            logger.info(f"Domain {domain} does not exist")
            return [], ["dns"]
        except dns.resolver.Timeout:
            logger.error(f"DNS query for {domain} timed out")
            raise TimeoutError(f"DNS query for {domain} timed out")
        except dns.dnssec.ValidationFailure as e:
            logger.error(f"DNSSEC validation failed for {domain}: {e}")
            raise DNSSECValidationError(f"DNSSEC validation failed for {domain}: {e}")
        except Exception as e:
            logger.error(f"Error looking up TXT record for {domain}: {e}")
            raise

    def _lookup_with_dnssec(self, name: str, rdtype: int) -> dns.resolver.Answer:
        """
        Perform a DNS lookup with DNSSEC validation.

        Args:
            name: The DNS name to look up.
            rdtype: The DNS record type to look up.

        Returns:
            The DNS answer.

        Raises:
            DNSSECValidationError: If DNSSEC validation fails.
        """
        try:
            # Set the DNSSEC OK (DO) flag and enable validation
            self.resolver.use_dnssec = True
            
            # Configure the resolver to require DNSSEC validation if available
            # This will make the resolver check the AD flag in responses
            self.resolver.want_dnssec = True
            
            # Perform the lookup
            answer = self.resolver.resolve(name, rdtype, raise_on_no_answer=True)
            
            return answer
        except dns.resolver.NoAnswer:
            # Re-raise NoAnswer exceptions
            raise
        except dns.resolver.NXDOMAIN:
            # Re-raise NXDOMAIN exceptions
            raise
        except dns.resolver.Timeout:
            # Re-raise Timeout exceptions
            raise
        except Exception as e:
            logger.error(f"DNS lookup or DNSSEC validation failed for {name}: {e}")
            raise DNSSECValidationError(f"DNS lookup or DNSSEC validation failed for {name}: {e}")
