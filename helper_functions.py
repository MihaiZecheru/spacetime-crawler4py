from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
import re

# with a 64-bit simhash, a threshold of 3 maps to 95.3% similarity. 6 maps to 90.6% similarity.
SIMHASH_BIT_DIFFERENCE_THRESHOLD: int = 3
# word definition; turns non-lowercase or digit into separators.
TOKEN_RE = re.compile(r"[a-z0-9]+") 

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
        count = freqs.get(word)
        if count:
            freqs[word] += 1
        else:
            freqs[word] = 1
    return freqs

def calculate_checksum(content: list[str]) -> int:
    '''
    Converts content into a checksum using Fletcher-16 method. 

    :param content: list of words
    '''
    wordsum: int = 0
    ordersum: int = 0

    for word in content:
        word += '\0'
        for character in word: 
            wordsum += ord(character)
            ordersum += wordsum

    return ((ordersum % 255) << 8) | (wordsum % 255)

def is_exact_match(content: list[str], checksums: set[int]) -> bool:
    '''
    Compares the content's checksum to a list of existing checksums.
    - If there's a match, return True.
    - If there's no match, return False.
    - Due to Fletcher-16's modulus methodology, false positives may occur with a len(content)/65,025 chance.
    
    :param content: list of words
    :param checksums: set of checksums
    '''
    checksum: int = calculate_checksum(content)

    return checksum in checksums

def calculate_simhash(content: dict[str, int]) -> int:
    # TODO: implement simhash calculator
    
    return 0

def is_simhash_match(content: dict[str, int], simhashes: set[int]) -> bool:
    '''
    Compares the content's simhash to a list of existing simhashes.
    - If it exceeds any simhashes' SIMHASH_BIT_DIFFERENCE_THRESHOLD, return True.
    - Else, return False.
    
    :param content: dict of words with frequencies
    :param simhashes: set of simhashes, stored as integers
    '''
    simhash: int = calculate_simhash(content)

    return simhash in simhashes