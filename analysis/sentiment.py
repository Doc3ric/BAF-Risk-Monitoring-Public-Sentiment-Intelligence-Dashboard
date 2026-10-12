"""Local sentiment analysis engine using VADER with financial risk domain adjustments.
Zero commercial API calls, runs completely offline on Windows.
"""

from typing import Dict, Any, Tuple
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer: SentimentIntensityAnalyzer = None


def get_analyzer() -> SentimentIntensityAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
        # Enrich lexicon with OSINT/cryptocurrency risk terms
        custom_lexicon = {
            "scam": -3.8,
            "scams": -3.8,
            "scammer": -3.8,
            "scammers": -3.8,
            "ponzi": -4.0,
            "rugpull": -4.0,
            "scheme": -2.5,
            "fraud": -3.8,
            "fraudulent": -3.8,
            "frozen": -2.8,
            "freeze": -2.5,
            "freezes": -2.5,
            "withholding": -2.8,
            "stolen": -3.5,
            "loss": -2.2,
            "trapped": -2.7,
            "unlicensed": -3.2,
            "illegal": -3.5,
            "warning": -2.2,
            "warnings": -2.2,
            "advisory": -2.2,
            "complaint": -2.5,
            "complaints": -2.5,
            "complain": -2.5,
            "failed": -2.5,
            "failure": -2.5,
            "blocked": -2.5,
            "unresponsive": -2.8,
            "ghosted": -2.8,
            "delay": -2.2,
            "delays": -2.2,
            "delayed": -2.2,
            "pyramid": -3.6,
            "dispute": -2.0,
            "lacks": -2.0,
            "contradicting": -2.5,
            "fake": -3.0,
            "simulated": -2.0,
            "vip": -0.5,
            "extortion": -3.8,
            "fee trap": -3.5,
            "audited": 1.5,
            "licensed": 2.0,
            "recovered": 2.2,
            "refunded": 2.2,
        }
        _analyzer.lexicon.update(custom_lexicon)
    return _analyzer


def analyze_sentiment(text: str) -> Tuple[str, float, Dict[str, float]]:
    """
    Analyze sentiment of text.
    Returns:
        (sentiment_label, compound_score, raw_scores)
    where sentiment_label is 'POSITIVE', 'NEGATIVE', 'NEUTRAL', or 'MIXED'.
    """
    if not text or not text.strip():
        return "NEUTRAL", 0.0, {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}

    analyzer = get_analyzer()
    scores = analyzer.polarity_scores(text)
    compound = round(scores["compound"], 4)
    pos = scores["pos"]
    neg = scores["neg"]

    # If strongly negative compound score, classify as NEGATIVE
    if compound <= -0.20:
        label = "NEGATIVE"
    # If strongly positive compound score, classify as POSITIVE
    elif compound >= 0.25:
        label = "POSITIVE"
    # If both positive and negative signals present with mixed/moderate compound
    elif neg >= 0.12 and pos >= 0.12:
        label = "MIXED"
    elif compound < -0.05 or neg >= 0.15:
        label = "NEGATIVE"
    elif compound > 0.05 or pos >= 0.15:
        label = "POSITIVE"
    else:
        label = "NEUTRAL"

    return label, compound, scores
