"""Tests for offline VADER sentiment analysis with financial risk domain adjustments."""

from analysis.sentiment import analyze_sentiment


def test_positive_sentiment():
    text = "BlockAlgo Frontier announces successful third-party security audit and licensed milestone."
    label, compound, scores = analyze_sentiment(text)
    assert label == "POSITIVE"
    assert compound > 0.15


def test_negative_risk_sentiment():
    text = "BlockAlgo scam alert! Users report frozen funds, unable to withdraw, and customer support blocked tickets."
    label, compound, scores = analyze_sentiment(text)
    assert label == "NEGATIVE"
    assert compound < -0.15


def test_mixed_sentiment():
    text = "Great earnings and huge returns on BlockAlgo yesterday, but today my withdrawal failed and support is completely unresponsive."
    label, compound, scores = analyze_sentiment(text)
    assert label in ("MIXED", "NEGATIVE")
    assert scores["pos"] > 0.10
    assert scores["neg"] > 0.10


def test_neutral_sentiment():
    text = "BlockAlgo documentation section 4 outlines platform protocol specifications."
    label, compound, scores = analyze_sentiment(text)
    assert label == "NEUTRAL"
    assert abs(compound) < 0.20


def test_empty_text():
    label, compound, scores = analyze_sentiment("")
    assert label == "NEUTRAL"
    assert compound == 0.0
