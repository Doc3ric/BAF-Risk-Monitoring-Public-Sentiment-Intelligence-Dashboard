"""Source health monitor and live collector runner.
Displays source availability, error logs, and allows triggering on-demand collection.
"""

from datetime import datetime
import zoneinfo
import streamlit as st
import pandas as pd

from scripts.collect_daily import run_all_collectors

MANILA_TZ = zoneinfo.ZoneInfo("Asia/Manila")


def format_timestamp(iso_str):
    if not iso_str:
        return "Never"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(MANILA_TZ).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(iso_str)


def render_sources_status(repo, sources):
    st.markdown("### 🔌 Data Sources Health & Connector Monitor")

    col_btn1, col_btn2 = st.columns([2, 5])
    with col_btn1:
        if st.button("🔄 Execute Full Data Collection Now", type="primary", use_container_width=True):
            with st.spinner("Executing pipeline across all permitted public connectors..."):
                result = run_all_collectors()
                st.success("Collection pipeline run finished!")
                st.rerun()

    with col_btn2:
        st.markdown(
            "<p style='color: #94A3B8; font-size: 0.85rem; padding-top: 8px;'>"
            "Triggers synchronous retrieval from BAF GitBook, GDELT, Google News RSS, and Reddit without commercial APIs."
            "</p>",
            unsafe_allow_html=True
        )

    st.markdown("<hr style='border-color: #2D3748; margin: 15px 0 20px 0;'>", unsafe_allow_html=True)

    # Monitored Sources Status Grid
    st.markdown("#### Configured Source Connectors & Legal Terms")

    for s in sources:
        status = s.get("last_status", "PENDING")
        if status == "SUCCESS":
            badge = '<span style="background-color: rgba(16, 185, 129, 0.2); color: #10B981; padding: 2px 8px; border-radius: 4px; font-weight: 600;">ACTIVE / SUCCESS</span>'
        elif status == "EMPTY":
            badge = '<span style="background-color: rgba(59, 130, 246, 0.2); color: #60A5FA; padding: 2px 8px; border-radius: 4px; font-weight: 600;">ACTIVE / 0 MATCHES</span>'
        elif status == "FAILED":
            badge = '<span style="background-color: rgba(239, 68, 68, 0.2); color: #EF4444; padding: 2px 8px; border-radius: 4px; font-weight: 600;">FAILED</span>'
        else:
            badge = '<span style="background-color: rgba(148, 163, 184, 0.2); color: #94A3B8; padding: 2px 8px; border-radius: 4px; font-weight: 600;">PENDING</span>'

        last_run = format_timestamp(s.get("last_run_at"))
        err = s.get("last_error")

        st.markdown(
            f"""
            <div style="background-color: #161B26; border: 1px solid #2D3748; border-radius: 6px; padding: 14px 18px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div>
                        <span style="font-size: 1.05rem; font-weight: 600; color: #F8FAFC;">{s.get('name')}</span>
                        <span style="color: #64748B; font-size: 0.8rem; margin-left: 8px;">({s.get('id')})</span>
                    </div>
                    <div>{badge}</div>
                </div>
                <div style="color: #94A3B8; font-size: 0.85rem; margin-bottom: 6px;">
                    <strong>Access Method:</strong> {s.get('access_method')} | <strong>API Key Required:</strong> {'Yes' if s.get('requires_key') else 'No (Zero-Budget Compliant)'}
                </div>
                <div style="color: #CBD5E1; font-size: 0.83rem;">
                    <strong>Last Run:</strong> {last_run}
                    {f" | <span style='color: #F87171;'><strong>Error:</strong> {err}</span>" if err else ""}
                </div>
                {f'<div style="margin-top: 6px; font-size: 0.8rem;"><a href="{s.get("url")}" target="_blank" style="color: #38BDF8;">Target URL: {s.get("url")}</a></div>' if s.get("url") else ""}
            </div>
            """,
            unsafe_allow_html=True
        )

    # Recent Collection Runs Table
    st.markdown("<hr style='border-color: #2D3748; margin: 20px 0;'>", unsafe_allow_html=True)
    st.markdown("#### Execution History (Collection Runs)")
    runs = repo.get_collection_runs(limit=25)
    if not runs:
        st.info("No collection runs recorded yet.")
    else:
        df_runs = pd.DataFrame(runs)
        display_df = pd.DataFrame({
            "Run ID": df_runs["id"],
            "Source": df_runs["source_name"].fillna(df_runs["source_id"]),
            "Started At (PST)": df_runs["started_at"].apply(format_timestamp),
            "Status": df_runs["status"],
            "Found": df_runs["items_found"],
            "Saved": df_runs["items_saved"],
            "Error Details": df_runs["error_message"].fillna("None")
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)
