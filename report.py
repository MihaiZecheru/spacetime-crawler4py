import json
from collections import Counter
from urllib.parse import urlparse

# load the json file
with open("stats.json") as f:
    d = json.load(f)

# display the count of found unique pages
print("Unique pages:", len(d["unique_pages"]))

# display longest page found
url, n = d["longest_page"]
print(f"Longest page: {url} ({n} words)")

# display top 50 words, using Counter.most_common function
print("Top 50 words:")
for word, count in Counter(d["word_counts"]).most_common(50):
    print(f"{word}, {count}")

# isolate unique subdomains from ics.uci.edu unique_pages 
subs = Counter()
for u in d["unique_pages"]:
    host = (urlparse(u).hostname or "").lower()
    # leading dot matters since "informatics.uci.edu".endswith("ics.uci.edu") is True
    if host == "ics.uci.edu" or host.endswith(".ics.uci.edu"):
        subs[host] += 1

# display unique subdomains of ics.uci.edu found 
print("ics.uci.edu subdomains:")
for host in sorted(subs):
    print(f"http://{host}, {subs[host]}")