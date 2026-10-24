import re
from helper_functions import *

PAGE_TEXT_THRESHOLD_FOR_ACCEPTANCE: int = 50
MAX_PAGE_CONTENT_BYTES: int = 5 * 1024 * 1024 # 5MB
# regex domain filter, allowing any subdomain, restricted domains, and required top-domains.
DOMAIN_RE = re.compile(r"^(?:[a-z0-9-]+\.)*(ics|cs|informatics|stat)\.uci\.edu$")

visited_urls: set[str] = set()
visited_checksums: set[int] = set()
visited_simhashes: set[int] = set()

def scraper(url, resp):
    links: list = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(base_url, resp):
    """Currently has the following features:
        - URL defragmentation
        - Filter out pages with little to no text
        - Near/true dupe detection
        - Bad statuses
        - Tracks visited URLs
    """
    # Implementation required.
    # base_url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    # Handle defragmentation of URLs, redirect content type check, size limit,
    # filter out little/no text pages, near/true dupes, bad statuses

    visited_urls.add(base_url)
    if resp.status != 200:
        print_red("DNP: Bad status", base_url, resp.error)
        return list()

    # Check for empty pages
    if resp.raw_response is None or not resp.raw_response.content:
        print_red("DNP: Empty page", base_url)
        return list()

    # Ignore non text/html pages that got through is_valid()
    if "text/html" not in resp.raw_response.headers.get("Content-Type", "").lower():
        print_red("DNP: Not a text/html page", base_url)
        return list()

    # Skip very large files
    if len(resp.raw_response.content) > MAX_PAGE_CONTENT_BYTES:
        print_red("DNP: Page too large", base_url)
        return list()

    # Validate the redirect target and mark it visited
    final_url = urldefrag(resp.raw_response.url)[0]
    if final_url != base_url:
        if not is_valid(final_url):  # outside domain, trap, or already crawled
            print_red("DNP: Bad/duplicate redirect", base_url, "->", final_url)
            return list()
        visited_urls.add(final_url)

    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    # Use final_url instead of base_url here to scrape the redirect instead of the original URL
    urls: list[str] = [defrag_and_clean_url(url, final_url) for url in get_urls_in_page(soup)]
    text: list[str] = get_text_in_page(soup)

    # Skip low-text files
    if len(text) < PAGE_TEXT_THRESHOLD_FOR_ACCEPTANCE:
        print_red("DNP: Low-text page", base_url)
        return list()

    frequencies = calculate_word_frequencies(text)

    if is_exact_match(text, visited_checksums) or is_simhash_match(frequencies, visited_simhashes):
        print_red("DNP: Similar/exact page already scraped", base_url)
        return list()
    else:
        visited_checksums.add(calculate_checksum(text))
        visited_simhashes.add(calculate_simhash(frequencies))

    # Green text
    print("\033[32mSuccessfully scraped\033[0m", base_url,
        f"(redirect to {final_url})" if final_url != base_url else "")
    return list(urls)

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    # skip already-visited URLs
    if url in visited_urls:
        return False

    # skip non-ASCII URLs
    if not url.isascii():
        return False

    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False

        # skip empty domains and incorrectly-formatted host URLs, using DOMAIN_RE regex filter
        if not DOMAIN_RE.match((parsed.hostname or "").lower()):
            return False

# TODO: tweak what queries should be marked as a trap through test run data
# ** Handle traps section **
        # separate path from query sections for later use
        path = parsed.path.lower()
        query = parsed.query.lower()

        # skip 200+ length URLs, since they may be traps
        if len(url) > 200:
            return False

        # skip paths w/ segments repeated 3+ times (e.g. /a/b/a/b/a/b/) 
        segments = [s for s in path.split("/") if s] # split segments, drop empty segments
        if any(segments.count(s) >= 3 for s in set(segments)):
            return False

        # 
        if re.fullmatch(r"/\d{4}/\d{1,2}(/\d{1,2})?/?", path):
            return False

        # 
        if re.search(r"/page/\d+", path):
            return False

        # 
        if re.search(r"\d{4}-\d{1,2}(-\d{1,2})?", query):
            return False

# ** End of handle traps section **

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
        print("TypeError for ", parsed)
        raise
