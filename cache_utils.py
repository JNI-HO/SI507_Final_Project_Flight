import json
import os
import requests


CACHE_FILENAME = "airport_cache.json"


def load_cache(filename: str = CACHE_FILENAME) -> dict:
    """
    Load the JSON cache file if it exists, otherwise return an empty dict.

    Parameters
    ----------
    filename : str
        Path to the cache file.

    Returns
    -------
    dict
        Cache dictionary.
    """
    if not os.path.exists(filename):
        return {}

    try:
        with open(filename, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except (json.JSONDecodeError, OSError):
        cache = {}

    return cache


def save_cache(cache: dict, filename: str = CACHE_FILENAME) -> None:
    """
    Save the cache dictionary to a JSON file.

    Parameters
    ----------
    cache : dict
        The cache data to save.
    filename : str
        Path to the cache file.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _guess_wiki_title(airport_name: str) -> str:
    """
    A very rough guess for a Wikipedia page title based on airport name.

    This may not always be correct, but it's probably OK for a small demo.

    Example:
    'Detroit Metropolitan Wayne County Airport' -> 'Detroit_Metropolitan_Wayne_County_Airport'
    """
    return airport_name.replace(" ", "_")


def fetch_airport_wiki(airport, cache: dict | None = None, filename: str = CACHE_FILENAME) -> tuple[dict, dict]:
    """
    Fetch (or retrieve from cache) a small piece of extra info about an airport.

    For now, this tries to download the raw HTML of the guessed Wikipedia page
    and stores it in the cache with the airport IATA code as the key.

    Parameters
    ----------
    airport : Airport
        An Airport object (from your flight_network module).
    cache : dict or None
        Existing cache dictionary. If None, this function will load the cache
        from disk and also return the updated cache.
    filename : str
        Cache filename to read/write.

    Returns
    -------
    info : dict
        A dictionary like {"wiki_url": ..., "html": ... or None}.
    cache : dict
        The updated cache dictionary.
    """
    if cache is None:
        cache = load_cache(filename)

    code = airport.code

    if code in cache:
        return cache[code], cache

    base_url = "https://en.wikipedia.org/wiki/"
    title = _guess_wiki_title(airport.name)
    url = base_url + title

    html_text = None

    try:
        headers = {"User-Agent": "UMSI-507-Project (your_email@umich.edu)"}
        resp = requests.get(url, timeout=10, headers = headers)
        resp.raise_for_status()
        html_text = resp.text
    except Exception:
        html_text = None

    info = {
        "wiki_url": url,
        "html": html_text,
    }

    cache[code] = info
    save_cache(cache, filename)

    return info, cache
