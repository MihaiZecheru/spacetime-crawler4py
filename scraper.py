import re
from helper_functions import *

PAGE_TEXT_THRESHOLD_FOR_ACCEPTANCE: int = 50

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

    # Handle defragmentation of URLs, 
    # filter out little/no text pages, near/true dupes, bad statuses

    visited_urls.add(base_url)
    if (resp.status != 200):
        print_red("ERROR:", base_url, resp.error)
        return list()

    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    text: list[str] = get_text_in_page(soup)
    urls: list[str] = [defrag_and_clean_url(url, base_url) for url in get_urls_in_page(soup)]
    frequencies = calculate_word_frequencies(text)
    
    if len(text) < PAGE_TEXT_THRESHOLD_FOR_ACCEPTANCE:
        return list()

    if is_exact_match(text, visited_checksums) or is_simhash_match(frequencies, visited_simhashes):
        return list()
    else:
        visited_checksums.add(fletcher_checksum(text))
        # TODO: visited_simhashes.add(...(frequencies))

    return list(urls)

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    if url in visited_urls:
        return False

    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False

        # Handle domain restrictions
        if not re.match(
            r"^.*ics\.uci\.edu|cs\.uci\.edu|informatics\.uci\.edu|stat\.uci\.edu(.*)$",
            parsed.netloc
        ): return False

# TODO: finish trap handling      
# ** Handle traps section **
        # Possible calendar blocker - might not be good because of sites like these:
        # https://ics.uci.edu/2022/06/27/ics-project-expo-strengthens-industry-engagement-and-showcases-student-talent/
        # It's like a newsletter, so it might be worth scraping and might not cause an infinte loop,
        # unless there's a way to keep advancing the day +1 and -1 infinetely
        if re.match(r"\/\d+\/\d+\/\d+\/", parsed.path.lower()):
            return False

        # Prevent infinite pagination by stopping "/page/3" URLs
        if re.match(r"\/page\/\d+\/?", parsed.path.lower()):
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
