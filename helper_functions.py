from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
import re
import hashlib

# specify 256-bit simhashes
SIMHASH_BIT_COUNT: int = 256
# with a 256 simhash, 12 bits = ~95.3% similarity, and 24 bits = ~90.6%
SIMHASH_BIT_DIFFERENCE_THRESHOLD: int = 12
# word definition; turns non-lowercase or digit into separators.
TOKEN_RE = re.compile(r"[a-z0-9]+")

""" HASHING FUNCTIONS BELOW """

def calculate_checksum(content: list[str]) -> str:
    '''
    Converts content into a checksum using SHA256. 

    :param content: list of words
    '''
    return hashlib.sha256("\0".join(content).encode("utf-8")).hexdigest()

def is_exact_match(content: list[str], checksums: set[str]) -> bool:
    '''
    Compares the content's checksum to a list of existing checksums.
    - If there's an exact match, return True, otherwise False.

    :param content: list of words
    :param checksums: set of checksums
    '''
    return calculate_checksum(content) in checksums


def _hash_word(word: str) -> int:
    # convert word into a 256-bit bytes using SHA256.
    digest = hashlib.sha256(word.encode("utf-8")).digest()
    # convert bytes into integer, first byte being MSB.
    return int.from_bytes(digest, "big")

def _hamming_distance(newSim: int, existingSim: int) -> int:
    '''returns how many bits are different in the simhashes.'''
    x: int = newSim ^ existingSim # XOR operation, returning 1's for differences and 0's for matches.
    count: int = 0
    while x:
        x &= x - 1 # x AND x-1, effectively deleting the lowest bit set to 1.
        count += 1 # increment the count of 1's. 
    return count

def calculate_simhash(content: dict[str, int]) -> int:
    counters: list[int] = [0] * SIMHASH_BIT_COUNT

    # combine all word-frequencies into one counter of size SIMHASH_BIT_COUNT.
    for word, freq in content.items():
        h = _hash_word(word) # Hash the word
        for i in range(SIMHASH_BIT_COUNT):
            if (h >> i) & 1:        # starting from the right, if the bit at index i is 1:
                counters[i] += freq # increment the counter at index i by freq
            else:                   # else:
                counters[i] -= freq # decrement the counter at index i by freq

    # generate a SIMHASH_BIT_COUNT-bit fingerprint by turning all positives to 1. Default is 0. 
    simhash: int = 0
    for i in range(SIMHASH_BIT_COUNT):
        if counters[i] > 0:     # if the counter is positive:
            simhash |= (1 << i) # set the simhash bit of index i to 1 using OR
    return simhash

def is_simhash_match(content: dict[str, int], simhashes: set[int]) -> bool:
    '''
    Compares the content's simhash to a list of existing simhashes.
    - If the amount of different bits <= SIMHASH_BIT_DIFFERENCE_THRESHOLD (too similar), return True.
    - Else, return False.
    
    :param content: dict of words with frequencies
    :param simhashes: set of simhashes, stored as integers
    '''
    simhash: int = calculate_simhash(content) # fetch simhash of content
    for existing in simhashes:
        if _hamming_distance(simhash, existing) <= SIMHASH_BIT_DIFFERENCE_THRESHOLD:
            return True
    return False

""" MISC. HELPER FUNCTIONS BELOW """

def print_red(*args, **kwargs) -> None:
    message = " ".join(str(a) for a in args)
    print(f"\033[31m{message}\033[0m", **kwargs)

def get_text_in_page(soup: BeautifulSoup) -> list[str]:
    # delete any script, style, and noscript tags from the parsing
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # apply TOKEN_RE word definition to text extracted by soup and return the processed text
    return TOKEN_RE.findall(soup.get_text(separator=" ").lower())

def defrag_and_clean_url(url: str, base_url: str) -> str:
    """Defragment a :url:

    :param url: The URL to defragment (could be a reference or absolute)
    :param base_url: The URL of the page where you found :url:"
    """
    # attempt to defrag the URL
    try:
        return urldefrag(urljoin(base_url, url))[0]

    # catch errors caused by malformed URLs, returning a null URL that is handled by scraper.py
    except ValueError:
        return ""

def get_urls_in_page(soup: BeautifulSoup) -> list[str]:
    """Get all the <a>.href that's in the page using beautiful soup"""
    urls = []
    for anchor in soup.find_all("a"):
        url = anchor.get("href")
        if (url):
            urls.append(url)
    return urls

def calculate_word_frequencies(words: list[str]) -> dict[str, int]:
    freqs = {}
    for word in words:
        freqs[word] = freqs.get(word, 0) + 1 # default to 0 on first sight, then add 1
    return freqs
