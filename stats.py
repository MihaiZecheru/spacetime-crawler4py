import atexit, json, os, threading
from collections import Counter

STATS_FILE = "stats.json" # save to STATS_FILE
SAVE_EVERY = 25           # save every SAVE_EVERY pages

# English stop word set. Fragments caused by tokenizer splitting apostrophes are also caught.
STOP_WORDS: set[str] = set("""
a about above after again against all am an and any are aren't as at be because been before being below between both but by can't cannot could couldn't did didn't do does doesn't doing don't down during each few for from further had hadn't has hasn't have haven't having he he'd he'll he's her here here's hers herself him himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself let's me more most mustn't my myself no nor not of off on once only or other ought our ours ourselves out over own same shan't she she'd she'll she's should shouldn't so some such than that that's the their theirs them themselves then there there's these they they'd they'll they're they've this those through to too under until up very was wasn't we we'd we'll we're we've were weren't what what's when when's where where's which while who who's whom why why's with won't would wouldn't you you'd you'll you're you've your yours yourself yourselves
""".split()) | {"aren", "couldn", "didn", "doesn", "don", "hadn", "hasn", "haven", "isn", "mustn", "shan", "shouldn", "wasn", "weren", "wouldn", "ll", "ve", "re"}

_lock = threading.RLock() # reentrant: tick() -> save_state() relocks

unique_pages: set[str] = set()   # set of unique defragmented URLs
longest_page: list = ["", 0]     # current longest page's url and token count
word_counts: Counter = Counter() # counts of common words, excluding STOP_WORDS and 1-chars
_sets = None                     # scraper's visited sets, saved with our stats
_ticks = 0                       # number of pages (not necessarily unqiue) processed

# adds a url to unique_pages
def record_unique_page(url: str) -> None:
    with _lock:
        unique_pages.add(url)

# updates longest_page with unfiltered word count for Q2, and filtered word count for Q3
def record_page_content(url: str, tokens: list[str]) -> None:
    with _lock:
        if len(tokens) > longest_page[1]:
            longest_page[0], longest_page[1] = url, len(tokens)
        for t in tokens:
            if len(t) > 1 and t not in STOP_WORDS:
                word_counts[t] += 1

# count SAVE_EVERY ticks before saving
def tick() -> None:
    global _ticks
    with _lock:
        _ticks += 1
        if _ticks % SAVE_EVERY == 0:
            save_state()

# attempt to save relevant data to STATS_FILE
def save_state() -> None:
    # safely exits if init() wasn't ran yet
    if _sets is None:
        return

    # save data to STATS_FILE.tmp and attempts to swap with old STATS_FILE.
    try:
        with _lock:
            urls, checksums, simhashes = _sets
            data = {
                "unique_pages": list(unique_pages),
                "longest_page": longest_page,
                "word_counts": dict(word_counts),
                "visited_urls": list(urls),
                "checksums": list(checksums),
                "simhashes": [f"{s:064x}" for s in list(simhashes)], # 256-bit int as hexadecimal
            }
            tmp = STATS_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump(data, f)
            os.replace(tmp, STATS_FILE) # atomic swap; keeps STATS_FILE intact if mid-write crash

    # catches failed saves to resist crashes
    except Exception as e: 
        print("stats save failed:", repr(e))

# loads any existing STATS_FILE, recovering its data. Also ensures one last save upon program exit.
def init(urls: set, checksums: set, simhashes: set) -> None:
    global _sets
    _sets = (urls, checksums, simhashes)
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE) as f:
            d = json.load(f)
        unique_pages.update(d["unique_pages"])
        longest_page[:] = d["longest_page"]
        word_counts.update(d["word_counts"])
        urls.update(d["visited_urls"])
        checksums.update(d["checksums"])
        simhashes.update(int(h, 16) for h in d["simhashes"])
    atexit.register(save_state)

# clears all stats and the scraper's visited sets, and deletes the STATS_FILE (stats.json) (used for --restart)
def reset() -> None:
    global _ticks
    with _lock:
        unique_pages.clear()
        longest_page[:] = ["", 0]
        word_counts.clear()
        _ticks = 0
        if _sets is not None:
            for s in _sets:
                s.clear()
        if os.path.exists(STATS_FILE):
            os.remove(STATS_FILE)