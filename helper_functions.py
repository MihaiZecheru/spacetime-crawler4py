from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
import hashlib

# specify 64-bit simhashes
SIMHASH_BIT_COUNT: int = 64
# with a 64-bit simhash, a threshold of 3 maps to 95.3% similarity. 6 maps to 90.6% similarity.
SIMHASH_BIT_DIFFERENCE_THRESHOLD: int = 3

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
    - If there's a high similarity match, return True, otherwise False.

    :param content: list of words
    :param checksums: set of checksums
    '''
    return calculate_checksum(content) in checksums

def _hash_word(word: str) -> int:
    # hash() is stable within a session
    return hash(word) & 0xFFFFFFFFFFFFFFFF # mask to get a non-negative 64-bit value

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

    # generate a 64-bit fingerprint by turning all positives to 1. Default is 0. 
    simhash: int = 0
    for i in range(SIMHASH_BIT_COUNT):
        if counters[i] > 0:     # if the counter is positive:
            simhash |= (1 << i) # set the simhash bit of index i to 1 using OR
    return simhash

def is_simhash_match(content: dict[str, int], simhashes: set[int]) -> bool:
    '''
    Compares the content's simhash to a list of existing simhashes.
    - If it exceeds any simhashes' SIMHASH_BIT_DIFFERENCE_THRESHOLD, return True.
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

def get_text_in_page(soup: BeautifulSoup):
    return soup.get_text(separator=" ", strip=True).split(" ")

def defrag_and_clean_url(url: str, base_url: str) -> str:
    """Defragment a :url:

    :param url: The URL to defragment (could be a reference or absolute)
    :param base_url: The URL of the page where you found :url:"
    """
    return urldefrag(urljoin(base_url, url))[0]

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