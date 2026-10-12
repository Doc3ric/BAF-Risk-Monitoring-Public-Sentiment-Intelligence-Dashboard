"""Deduplication and similarity clustering for collected intelligence.
Prevents duplicate articles, syndicated stories, and copied forum complaints from inflating metrics.
"""

import re
import hashlib
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from typing import Optional, List, Dict, Any

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "ref", "source", "ref_src", "t", "s"
}


def normalize_url(url: str) -> str:
    """Normalize a URL by removing tracking query parameters and trailing slashes."""
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        filtered_query = [
            (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if k.lower() not in TRACKING_PARAMS
        ]
        new_query = urlencode(filtered_query)
        path = parsed.path.rstrip("/")
        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            parsed.params,
            new_query,
            ""  # drop fragments
        ))
        return normalized
    except Exception:
        return url.strip()


def clean_text_for_hashing(text: str) -> str:
    """Lowercase and retain only alphanumeric characters and spaces."""
    if not text:
        return ""
    lowered = text.lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return " ".join(cleaned.split())


def compute_content_hash(text: str) -> str:
    """Compute SHA-256 hash of normalized text."""
    cleaned = clean_text_for_hashing(text)
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


def compute_simhash(text: str, hash_bits: int = 64) -> str:
    """
    Compute a 64-bit SimHash for fuzzy near-duplicate matching of text.
    Uses word tokens and bigrams to ensure robust matching across syndicated articles.
    """
    cleaned = clean_text_for_hashing(text)
    tokens = [t for t in cleaned.split() if len(t) > 2]
    if not tokens:
        tokens = cleaned.split()
    if not tokens:
        return "0" * (hash_bits // 4)

    # Combine unigrams and bigrams
    features = list(tokens)
    for i in range(len(tokens) - 1):
        features.append(f"{tokens[i]}_{tokens[i+1]}")

    v = [0] * hash_bits
    for feat in features:
        # Weight longer features slightly more
        weight = 2 if "_" in feat else 1
        f_hash = int(hashlib.md5(feat.encode("utf-8")).hexdigest()[:16], 16)
        for i in range(hash_bits):
            bit = (f_hash >> i) & 1
            if bit == 1:
                v[i] += weight
            else:
                v[i] -= weight

    fingerprint = 0
    for i in range(hash_bits):
        if v[i] > 0:
            fingerprint |= (1 << i)

    return f"{fingerprint:016x}"


def simhash_distance(hex1: str, hex2: str) -> int:
    """Compute Hamming distance between two 64-bit SimHash hex strings."""
    try:
        val1 = int(hex1, 16)
        val2 = int(hex2, 16)
        x = val1 ^ val2
        return bin(x).count("1")
    except Exception:
        return 64


def find_or_create_duplicate_group(
    content_hash: str,
    simhash: str,
    existing_items: List[Dict[str, Any]],
    distance_threshold: int = 20
) -> str:
    """
    Find if item matches an existing duplicate group; returns existing group_id or a new one.
    """
    for item in existing_items:
        # Exact content hash match
        if item.get("content_hash") == content_hash:
            if item.get("duplicate_group_id"):
                return item["duplicate_group_id"]
            return item["id"]

        # Near-duplicate SimHash match
        item_simhash = item.get("simhash")
        if item_simhash and simhash:
            dist = simhash_distance(simhash, item_simhash)
            if dist <= distance_threshold:
                if item.get("duplicate_group_id"):
                    return item["duplicate_group_id"]
                return item["id"]

    # New unique group
    return content_hash[:16]
