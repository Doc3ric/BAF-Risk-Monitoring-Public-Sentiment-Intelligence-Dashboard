"""BAF Risk Monitor - Personal Risk Monitoring & Public Sentiment Intelligence Dashboard.
Dedicated exclusively to independent monitoring of BlockAlgo Frontier Technologies (BAF).
"""

import os
import sys
from datetime import datetime, timedelta
import zoneinfo
import yaml
import streamlit as st
import pandas as pd

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database.repository import Repository
from dashboard.overview import render_overview
from dashboard.charts import (
    plot_sentiment_trend,
    plot_complaint_volume,
    plot_category_breakdown,
    plot_source_distribution
)
from dashboard.latest_findings import render_latest_findings
from dashboard.sources_status import render_sources_status
from dashboard.evidence_detail import render_evidence_and_tools

MANILA_TZ = zoneinfo.ZoneInfo("Asia/Manila")

st.set_page_config(
    page_title="BAF Risk Monitor | Public Intelligence Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Financial Intelligence CSS
st.markdown(
    """
    <style>
    /* Global Background and Typography */
    .stApp {
        background-color: #0E1117;
        color: #E2E8F0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Metric Cards */
    .metric-card {
        background-color: #161B26;
        border: 1px solid #232D3F;
        border-radius: 8px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-label {
        color: #94A3B8;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        color: #F8FAFC;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 2px;
    }
    .metric-caption {
        color: #64748B;
        font-size: 0.78rem;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #121620;
        border-right: 1px solid #232D3F;
    }

    /* Tab and Button Adjustments */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #161B26;
        border-radius: 6px 6px 0 0;
        padding: 8px 16px;
        color: #94A3B8;
    }
    .stTabs [aria-selected="true"] {
        background-color: #232D3F !important;
        color: #60A5FA !important;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)


@st.cache_resource
def get_repository():
    settings_file = os.path.join(ROOT_DIR, "config", "settings.yaml")
    db_rel = "data/baf_risk_monitor.db"
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
            db_rel = cfg.get("app", {}).get("database_path", db_rel)
    db_path = os.path.join(ROOT_DIR, db_rel)
    repo = Repository(db_path=db_path)
    repo.init_db()
    return repo


def load_settings():
    settings_file = os.path.join(ROOT_DIR, "config", "settings.yaml")
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def main():
    repo = get_repository()
    settings = load_settings()

    # Pre-load state
    sources = repo.get_sources()
    active_alerts = repo.get_active_alerts()
    all_metrics = repo.get_daily_metrics()
    latest_metrics = all_metrics[-1] if all_metrics else None

    # Sidebar
    with st.sidebar:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 1.8rem;">🛡️</span>
                <div>
                    <h2 style="margin: 0; font-size: 1.25rem; color: #F8FAFC;">BAF Risk Monitor</h2>
                    <span style="font-size: 0.75rem; color: #60A5FA; font-weight: 600;">v1.0.0 | OSINT INTELLIGENCE</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            "<p style='color: #94A3B8; font-size: 0.8rem; margin-bottom: 15px;'>"
            "Monitoring Target: <strong>BlockAlgo Frontier (BAF)</strong>"
            "</p>",
            unsafe_allow_html=True
        )

        nav_choice = st.radio(
            "Intelligence Views",
            options=[
                "📊 Executive Overview",
                "📈 Historical Trends & Charts",
                "📋 Latest Findings & Feed",
                "📜 GitBook Policy Tracker & Diffs",
                "🔌 Sources Health & Connectors",
                "📥 Ingestion & Data Export"
            ]
        )

        st.markdown("<hr style='border-color: #232D3F; margin: 15px 0;'>", unsafe_allow_html=True)

        st.markdown("##### 📌 Monitored Official URLs")
        st.markdown(
            """
            - [BAF Introduction](https://baf-1.gitbook.io/baf/platform-overview/readme/introduction)
            - [BAF GitBook Root](https://baf-1.gitbook.io/baf/)
            """
        )

        st.markdown("<hr style='border-color: #232D3F; margin: 15px 0;'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="background-color: #0E1117; padding: 10px; border-radius: 6px; font-size: 0.74rem; color: #64748B; border: 1px solid #1E293B;">
                <strong>OSINT Compliance Notice:</strong><br>
                This personal tool tracks public information without paid commercial models. It does not certify financial safety or declare misconduct. Evidence is classified for objective human evaluation.
            </div>
            """,
            unsafe_allow_html=True
        )

    # Main Area Router
    if nav_choice == "📊 Executive Overview":
        render_overview(repo, settings, latest_metrics, active_alerts, sources)

    elif nav_choice == "📈 Historical Trends & Charts":
        st.markdown("### 📈 Historical Intelligence & Multi-Source Trends")

        # Time range filter
        filter_col1, filter_col2 = st.columns([2, 5])
        with filter_col1:
            range_opt = st.selectbox(
                "Filter Timeframe",
                options=["All Recorded Time", "Last 7 Days", "Last 30 Days", "Last 90 Days"],
                index=0
            )

        now_utc = datetime.now(timezone.utc)
        start_date_str = None
        if range_opt == "Last 7 Days":
            start_date_str = (now_utc - timedelta(days=7)).strftime("%Y-%m-%d")
        elif range_opt == "Last 30 Days":
            start_date_str = (now_utc - timedelta(days=30)).strftime("%Y-%m-%d")
        elif range_opt == "Last 90 Days":
            start_date_str = (now_utc - timedelta(days=90)).strftime("%Y-%m-%d")

        filtered_metrics = repo.get_daily_metrics(start_date=start_date_str)
        metrics_df = pd.DataFrame(filtered_metrics) if filtered_metrics else pd.DataFrame()

        filtered_items = repo.get_collected_items(start_date=start_date_str, limit=5000)
        items_df = pd.DataFrame(filtered_items) if filtered_items else pd.DataFrame()

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.plotly_chart(plot_sentiment_trend(metrics_df), use_container_width=True)
        with chart_col2:
            st.plotly_chart(plot_complaint_volume(metrics_df), use_container_width=True)

        chart_col3, chart_col4 = st.columns(2)
        with chart_col3:
            st.plotly_chart(plot_category_breakdown(items_df), use_container_width=True)
        with chart_col4:
            st.plotly_chart(plot_source_distribution(items_df), use_container_width=True)

    elif nav_choice == "📋 Latest Findings & Feed":
        render_latest_findings(repo, sources)

    elif nav_choice == "📜 GitBook Policy Tracker & Diffs":
        render_evidence_and_tools(repo)

    elif nav_choice == "🔌 Sources Health & Connectors":
        render_sources_status(repo, sources)

    elif nav_choice == "📥 Ingestion & Data Export":
        render_evidence_and_tools(repo)


if __name__ == "__main__":
    main()
