from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup



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
        count = freqs.get(word)
        if count:
            freqs[word] += 1
        else:
            freqs[word] = 0
    return freqs

def fletcher_checksum(content: list[str]) -> int:
    '''
    Converts content into a checksum using Fletcher-16 method. 

    :param content: list of words
    '''
    wordsum: int = 0
    ordersum: int = 0

    for word in content:
        for character in word: 
            wordsum += ord(character)
            ordersum += wordsum

    return (ordersum % 255 << 8) | wordsum % 255

def is_exact_match(content: list[str], checksums: list[int]) -> bool:
    '''
    Compares the content's checksum to a list of existing checksums.
    - If there's a match, return True.
    - If there's no match, return False.

    :param content: list of words
    :param checksums: list of checksums
    '''
    checksum: int = fletcher_checksum(content)

    return checksum in checksums

def is_simhash_match(content: dict[str, int], simhashes: int) -> bool:
    '''
    
    
    :param: content - dict of words with frequencies, sorted by most common
    '''
    return False