"""Latest findings feed and searchable intelligence records viewer.
Provides granular filtering by date, source, category, sentiment, and verification status.
"""

from datetime import datetime, timezone
import zoneinfo
import streamlit as st
import pandas as pd

MANILA_TZ = zoneinfo.ZoneInfo("Asia/Manila")


def format_published_date(iso_str):
    if not iso_str:
        return "Undisclosed / Documentation"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        manila_time = dt.astimezone(MANILA_TZ)
        return manila_time.strftime("%Y-%m-%d %I:%M %p PST")
    except Exception:
        return str(iso_str)[:19]


def format_collected_realtime(iso_str):
    if not iso_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        manila_time = dt.astimezone(MANILA_TZ)
        time_str = manila_time.strftime("%Y-%m-%d %I:%M:%S %p PST")
        diff_sec = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()
        if diff_sec < 60:
            rel = "Just now"
        elif diff_sec < 3600:
            rel = f"{int(diff_sec // 60)}m ago"
        elif diff_sec < 86400:
            rel = f"{int(diff_sec // 3600)}h ago"
        else:
            rel = f"{int(diff_sec // 86400)}d ago"
        return f"{time_str} ({rel})"
    except Exception:
        return str(iso_str)


def get_sentiment_badge_html(sentiment: str) -> str:
    color_map = {
        "POSITIVE": ("#10B981", "rgba(16, 185, 129, 0.2)"),
        "NEGATIVE": ("#EF4444", "rgba(239, 68, 68, 0.2)"),
        "NEUTRAL": ("#94A3B8", "rgba(148, 163, 184, 0.2)"),
        "MIXED": ("#F59E0B", "rgba(245, 158, 11, 0.2)"),
    }
    color, bg = color_map.get(sentiment, ("#94A3B8", "rgba(148, 163, 184, 0.2)"))
    return f'<span style="background-color: {bg}; color: {color}; font-size: 0.75rem; font-weight: 600; padding: 2px 8px; border-radius: 4px; border: 1px solid {color}33;">{sentiment}</span>'


def get_evidence_badge_html(status: str) -> str:
    color_map = {
        "OFFICIAL_STATEMENT": ("#3B82F6", "rgba(59, 130, 246, 0.2)"),
        "CORROBORATED": ("#10B981", "rgba(16, 185, 129, 0.2)"),
        "REPORTED_ALLEGATION": ("#EF4444", "rgba(239, 68, 68, 0.2)"),
        "PERSONAL_TESTIMONIAL": ("#F59E0B", "rgba(245, 158, 11, 0.2)"),
        "UNVERIFIED": ("#64748B", "rgba(100, 116, 139, 0.2)"),
        "UNABLE_TO_VERIFY": ("#475569", "rgba(71, 85, 105, 0.2)"),
    }
    color, bg = color_map.get(status, ("#94A3B8", "rgba(148, 163, 184, 0.2)"))
    formatted = status.replace("_", " ").title()
    return f'<span style="background-color: {bg}; color: {color}; font-size: 0.75rem; font-weight: 600; padding: 2px 8px; border-radius: 4px; border: 1px solid {color}33;">{formatted}</span>'


def render_latest_findings(repo, sources):
    st.markdown("### 📋 Monitored Intelligence Findings & Evidence Feed")

    # Filter Bar
    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
    with col1:
        search_query = st.text_input("🔍 Search Keyword / Title", placeholder="Filter by text...")
    with col2:
        cat_filter = st.selectbox(
            "Topic Category",
            options=["ALL", "withdrawal_issues", "deposit_payment_problems", "refund_complaints",
                     "customer_support_complaints", "fee_and_reward_changes", "recruitment_and_referrals",
                     "earnings_and_return_claims", "platform_downtime", "corporate_regulatory_developments",
                     "independent_reporting"],
            index=0
        )
    with col3:
        sent_filter = st.selectbox("Sentiment", options=["ALL", "POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED"], index=0)
    with col4:
        ev_filter = st.selectbox(
            "Evidence Status",
            options=["ALL", "OFFICIAL_STATEMENT", "CORROBORATED", "REPORTED_ALLEGATION",
                     "PERSONAL_TESTIMONIAL", "UNVERIFIED", "UNABLE_TO_VERIFY"],
            index=0
        )

    col_sub1, col_sub2, col_sub3 = st.columns([2, 1, 1])
    with col_sub1:
        # Filter out official baf from source options if user doesn't want it
        source_options = ["ALL"] + [s["id"] for s in sources if s["id"] != "official_baf_docs"]
        source_filter = st.selectbox("Monitored Source", options=source_options, format_func=lambda x: "All Public Sources" if x == "ALL" else next((s["name"] for s in sources if s["id"] == x), x))
    with col_sub2:
        complaints_only = st.checkbox("🚨 Complaints Only", value=True)
    with col_sub3:
        hide_official = st.checkbox("Hide Official BAF Docs", value=True)

    # Query items with selected filters
    items = repo.get_collected_items(
        category=None if cat_filter == "ALL" else cat_filter,
        sentiment=None if sent_filter == "ALL" else sent_filter,
        evidence_status=None if ev_filter == "ALL" else ev_filter,
        source_id=None if source_filter == "ALL" else source_filter,
        is_complaint=True if complaints_only else None,
        search_query=search_query if search_query.strip() else None,
        limit=150
    )

    if hide_official:
        items = [i for i in items if i.get("evidence_status") != "OFFICIAL_STATEMENT" and i.get("source_id") != "official_baf_docs"]

    st.markdown(f"<div style='color: #94A3B8; font-size: 0.9rem; margin-bottom: 12px;'>Showing <strong>{len(items)}</strong> observation(s) matching criteria:</div>", unsafe_allow_html=True)

    if not items:
        st.markdown(
            """
            <div style="background-color: #1A1F2C; border: 1px dashed #374151; border-radius: 8px; padding: 30px; text-align: center; color: #94A3B8;">
                <p style="font-size: 1.1rem; margin-bottom: 8px;">No matching intelligence records found.</p>
                <p style="font-size: 0.85rem; color: #64748B;">Try broadening your filters, or execute a new collection run.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # Render finding cards
    for item in items:
        pub_formatted = format_published_date(item.get("published_at"))
        col_formatted = format_collected_realtime(item.get("collected_at"))
        cat_formatted = item.get("primary_category", "").replace("_", " ").title()
        sent_badge = get_sentiment_badge_html(item.get("sentiment_label", "NEUTRAL"))
        ev_badge = get_evidence_badge_html(item.get("evidence_status", "UNVERIFIED"))
        score = item.get("sentiment_score", 0.0)
        source_name = item.get("source_name") or item.get("source_id", "Unknown")

        st.markdown(
            f"""
            <div style="background-color: #161B26; border: 1px solid #2D3748; border-radius: 6px; padding: 16px 20px; margin-bottom: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <div>
                        <span style="font-weight: 600; color: #60A5FA; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.5px;">[{source_name}]</span>
                        <h4 style="color: #F8FAFC; margin: 4px 0 6px 0; font-size: 1.05rem;">{item.get('title')}</h4>
                    </div>
                    <div style="display: flex; gap: 6px; align-items: center;">
                        {sent_badge}
                        {ev_badge}
                    </div>
                </div>
                <p style="color: #CBD5E1; font-size: 0.92rem; line-height: 1.45; margin-bottom: 10px;">
                    {item.get('content_excerpt')}
                </p>
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: #94A3B8; border-top: 1px solid #232D3F; padding-top: 8px; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: center;">
                        <span style="background-color: #1E293B; padding: 2px 6px; border-radius: 4px; color: #CBD5E1;">Category: {cat_formatted}</span>
                        <span>Polarity: <strong>{score:+.2f}</strong></span>
                        <span>📅 <strong>Date Posted:</strong> <span style="color: #93C5FD;">{pub_formatted}</span></span>
                        <span>⚡ <strong>Collected (Real-time):</strong> <span style="color: #34D399; font-weight: 600;">{col_formatted}</span></span>
                    </div>
                    <div>
                        <a href="{item.get('url')}" target="_blank" style="color: #38BDF8; text-decoration: none; font-weight: 500;">
                            🔗 View Source ↗
                        </a>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
