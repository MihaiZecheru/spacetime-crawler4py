import requests
import cbor
import time

from utils.response import Response

RETRY_DELAY_SECONDS: int = 15

def download(url, config, logger=None):
    host, port = config.cache_server

    # Catch the error when the server is down and retry the URL every 15 seconds
    # until the server is back up
    while True:
        try:
            resp = requests.get(
                f"http://{host}:{port}/",
                params=[("q", f"{url}"), ("u", f"{config.user_agent}")],
                timeout=30)
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if logger:
                logger.warning(f"Cache server unreachable ({e.__class__.__name__}) for {url}. "
                               f"Retrying in {RETRY_DELAY_SECONDS}s.")
            time.sleep(RETRY_DELAY_SECONDS)
    try:
        if resp and resp.content:
            return Response(cbor.loads(resp.content))
    except (EOFError, ValueError) as e:
        pass
    logger.error(f"Spacetime Response error {resp} with url {url}.")
    return Response({
        "error": f"Spacetime Response error {resp} with url {url}.",
        "status": resp.status_code,
        "url": url})
