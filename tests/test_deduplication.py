"""Tests for deduplication, URL normalization, content hashing, and SimHash distance."""

from analysis.deduplication import (
    normalize_url,
    compute_content_hash,
    compute_simhash,
    simhash_distance,
    find_or_create_duplicate_group
)


def test_normalize_url():
    url1 = "https://example.com/article/?utm_source=twitter&utm_medium=social#section1"
    url2 = "https://example.com/article"
    assert normalize_url(url1) == "https://example.com/article"
    assert normalize_url(url2) == "https://example.com/article"

    url3 = "https://WWW.Example.COM/path/?fbclid=12345&ref=homepage/"
    assert normalize_url(url3) == "https://www.example.com/path"


def test_content_hashing():
    text1 = "BlockAlgo platform has delayed user withdrawals."
    text2 = "BlockAlgo   Platform HAS delayed user withdrawals!!!"
    # Normalization should produce identical hashes despite spacing/casing/punctuation
    assert compute_content_hash(text1) == compute_content_hash(text2)

    text3 = "BlockAlgo announces new marketing partnership."
    assert compute_content_hash(text1) != compute_content_hash(text3)


def test_simhash_near_duplicate_detection():
    base_text = (
        "Urgent warning: BlockAlgo Frontier has frozen accounts and withdrawal delays are mounting across telegram groups. "
        "Users report customer support has stopped responding."
    )
    # Slightly syndicated copy with minor wording change
    copied_text = (
        "Urgent alert: BlockAlgo Frontier has frozen accounts and withdrawal delays are mounting across telegram chats. "
        "Several users report customer support stopped responding."
    )
    unrelated_text = (
        "Today the weather in Tokyo is sunny and warm with mild winds blowing from the east."
    )

    hash1 = compute_simhash(base_text)
    hash2 = compute_simhash(copied_text)
    hash_unrelated = compute_simhash(unrelated_text)

    dist_near = simhash_distance(hash1, hash2)
    dist_unrelated = simhash_distance(hash1, hash_unrelated)

    # Near duplicates have significantly smaller Hamming distance than unrelated texts
    assert dist_near <= 20
    assert dist_unrelated >= 28
    assert dist_near < dist_unrelated


def test_find_or_create_duplicate_group():
    existing_items = [
        {
            "id": "item_1",
            "content_hash": "hash_abc",
            "simhash": "ffffffff00000000",
            "duplicate_group_id": "group_1"
        }
    ]

    # Exact content match returns existing group
    group = find_or_create_duplicate_group("hash_abc", "ffffffff00000000", existing_items)
    assert group == "group_1"

    # Near duplicate SimHash (distance 1) returns existing group
    near_simhash = "ffffffff00000001"
    group_near = find_or_create_duplicate_group("hash_different", near_simhash, existing_items)
    assert group_near == "group_1"

    # Completely new text returns a new distinct group ID
    new_simhash = "00000000ffffffff"
    group_new = find_or_create_duplicate_group("hash_new_9999", new_simhash, existing_items)
    assert group_new != "group_1"
