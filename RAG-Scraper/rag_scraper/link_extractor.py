from enum import Enum, auto
from typing import Set
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

class LinkType(Enum):
    ALL = auto()
    INTERNAL = auto()
    EXTERNAL = auto()

class LinkExtractor:
    @staticmethod
    def scrape_url(url: str, link_type: LinkType = LinkType.ALL, depth: int = 0, visited_urls: Set[str] = None) -> Set[str]:
        """
        Scrape a given URL for unique links within a specified element, 
        with recursive depth support.

        :param url: The URL of the website to scrape.
        :param link_type: The type of links to scrape (ALL, INTERNAL, EXTERNAL).
        :param depth: The recursion depth for extracting links.
        :param visited_urls: A set to keep track of visited URLs.
        :return: A set of unique link URLs found.
        """
        if visited_urls is None:
            visited_urls = set()

        if url in visited_urls or depth < 0:
            return set()

        visited_urls.add(url)

        base_url = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(url))
        extracted_links = set()

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                absolute_url = urljoin(url, href)
                domain = urlparse(absolute_url).netloc

                if link_type == LinkType.INTERNAL and domain == urlparse(base_url).netloc:
                    extracted_links.add(absolute_url)
                elif link_type == LinkType.EXTERNAL and domain != urlparse(base_url).netloc:
                    extracted_links.add(absolute_url)
                elif link_type == LinkType.ALL:
                    extracted_links.add(absolute_url)

            # Recursive scraping if depth > 0
            if depth > 0:
                for link in extracted_links.copy():
                    extracted_links.update(LinkExtractor.scrape_url(link, link_type, depth - 1, visited_urls))

            return extracted_links
        except requests.RequestException as e:
            print(f"Request failed for {url}: {e}")
            return set()

