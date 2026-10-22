import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from helper_functions import *

PAGE_TEXT_THRESHOLD_FOR_ACCEPTANCE: int = 50

def get_urls_in_page(soup: BeautifulSoup) -> list[str]:
    """Get all the <a>.href that's in the page using beautiful soup"""
    urls = []
    for anchor in soup.find_all("a"):
        url = anchor.get("href")
        if (url):
            urls.append(url)

def get_text_in_page(soup: BeautifulSoup):
    return soup.get_text(separator=" ", strip=True).split(" ")

def calculate_word_frequencies(words: list[str]) -> dict[str, int]:
    freqs = {}
    for word in words:
        count = freqs.get(word)
        if count:
            freqs[word] += 1
        else:
            freqs[word] = 0
    return freqs

def defragment_url(url: str, base_url: str) -> str:
    """Defragment a :url:

    :param url: The URL to defragment (could be a reference or absolute)
    :param base_url: The URL of the page where you found :url:"
    """
    p = urlparse(urljoin(base_url, url))
    return f"{p.scheme}://{p.netloc}{p.path}?{p.query}"

# TODO: move all of the above functions to helper_functions.py

visited_urls: set[str] = set()

def scraper(url, resp):
    links: list = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    """Currently has the following features:
        - URL defragmentation
        - Filter out pages with little to no text
        - Near/true dupe detection
        - Bad statuses
        - Tracks visited URLs
    """
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    # Handle defragmentation of URLs, 
    # filter out little/no text pages, near/true dupes, bad statuses

    visited_urls.add(url)
    if (resp.status != 200):
        print_with_color("ERROR:", resp.error)
        return list()

    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    text: list[str] = get_text_in_page(soup)
    urls: list[str] = [defragment_url(url) for url in get_urls_in_page(soup)]
    frequencies = calculate_word_frequencies(text)
    
    if len(text) < PAGE_TEXT_THRESHOLD_FOR_ACCEPTANCE:
        return list()

    if is_exact_match(text) or is_simhash_match(frequencies):
        return list()

    return list(urls)

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    if url in visited_urls:
        return False

    # TODO: handle domain restrictions and traps
    if urlparse(url).netloc in []

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
