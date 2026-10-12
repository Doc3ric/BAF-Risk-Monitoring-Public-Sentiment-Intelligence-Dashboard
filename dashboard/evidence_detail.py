"""Official Documentation Diff Viewer, Manual Intelligence Ingestion, and Backup/Export Tools.
Enables inspection of BAF GitBook changes, manual entry of SEC advisories, and CSV/database exports.
"""

import io
from datetime import datetime, timezone
import zoneinfo
import streamlit as st
import pandas as pd

from collectors.manual_import import ManualImportCollector

MANILA_TZ = zoneinfo.ZoneInfo("Asia/Manila")


def format_timestamp(iso_str):
    if not iso_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(MANILA_TZ).strftime("%Y-%m-%d %H:%M:%S PST")
    except Exception:
        return str(iso_str)


def render_evidence_and_tools(repo):
    tab1, tab2, tab3 = st.tabs([
        "📜 BAF GitBook Policy Tracker & Diffs",
        "📥 Manual Intelligence & Regulatory Ingestion",
        "💾 Data Export & Database Backups"
    ])

    # ==========================================
    # Tab 1: Official Documentation Tracker
    # ==========================================
    with tab1:
        st.markdown("#### Official GitBook Documentation Snapshots & Text Diffs")
        st.markdown(
            "<p style='color: #94A3B8; font-size: 0.9rem;'>"
            "Tracks changes to BAF platform terms, reward structures, withdrawal policies, and fee rules over time."
            "</p>",
            unsafe_allow_html=True
        )

        snapshots = repo.get_doc_snapshots(limit=30)
        if not snapshots:
            st.info("No documentation snapshots captured yet. Run collection to establish a baseline snapshot.")
        else:
            for snap in snapshots:
                snap_time = format_timestamp(snap.get("snapshot_timestamp"))
                diff_summary = snap.get("diff_summary", "No diff recorded.")
                has_change = diff_summary and "No text change detected" not in diff_summary

                border_color = "#F59E0B" if has_change else "#2D3748"
                badge_text = "MODIFIED" if has_change else "BASELINE / UNCHANGED"
                badge_bg = "rgba(245, 158, 11, 0.2)" if has_change else "rgba(100, 116, 139, 0.2)"
                badge_color = "#FBBF24" if has_change else "#94A3B8"

                with st.expander(f"Snapshot #{snap['id']} - {snap.get('title', 'BAF Docs')} ({snap_time})"):
                    st.markdown(f"**Target URL:** `{snap.get('url')}`")
                    st.markdown(f"**Content SHA-256 Hash:** `{snap.get('content_hash')}`")
                    st.markdown(f"**Status:** <span style='background-color: {badge_bg}; color: {badge_color}; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem;'>{badge_text}</span>", unsafe_allow_html=True)

                    st.markdown("##### Diff Analysis / Change Log:")
                    st.code(diff_summary, language="diff")

                    if st.checkbox(f"Show raw snapshot text #{snap['id']}", key=f"show_raw_{snap['id']}"):
                        st.text_area("Extracted Text Content", value=snap.get("raw_text", ""), height=200, key=f"raw_text_{snap['id']}")

    # ==========================================
    # Tab 2: Manual Ingestion
    # ==========================================
    with tab2:
        st.markdown("#### Ingest Offline Intelligence or Regulatory Advisories")
        st.markdown(
            "<p style='color: #94A3B8; font-size: 0.9rem;'>"
            "Used for official advisories (e.g. SEC Philippines, DTI, legal dockets) or offline research findings."
            "</p>",
            unsafe_allow_html=True
        )

        with st.form("manual_import_form"):
            col_in1, col_in2 = st.columns(2)
            with col_in1:
                in_title = st.text_input("Title / Advisory Headline *", placeholder="e.g. SEC Philippines Advisory on Unregistered Entity")
                in_url = st.text_input("Source URL *", placeholder="https://www.sec.gov.ph/advisories/...")
                in_source = st.text_input("Originating Entity / Source", value="SEC Philippines Advisory")
            with col_in2:
                in_category = st.selectbox(
                    "Issue Category",
                    options=[
                        "corporate_regulatory_developments",
                        "withdrawal_issues",
                        "deposit_payment_problems",
                        "fee_and_reward_changes",
                        "recruitment_and_referrals",
                        "earnings_and_return_claims",
                        "independent_reporting"
                    ],
                    index=0
                )
                in_evidence = st.selectbox(
                    "Evidence Status",
                    options=[
                        "CORROBORATED",
                        "OFFICIAL_STATEMENT",
                        "REPORTED_ALLEGATION",
                        "PERSONAL_TESTIMONIAL",
                        "UNVERIFIED"
                    ],
                    index=0
                )
                in_author = st.text_input("Author / Agency", value="Securities and Exchange Commission")

            in_content = st.text_area("Finding Excerpt / Text Content *", height=120, placeholder="Paste official text or summary of allegations...")

            submitted = st.form_submit_button("📥 Ingest Manual Record", type="primary")
            if submitted:
                if not in_title.strip() or not in_content.strip():
                    st.error("Please provide both Title and Content.")
                else:
                    collector = ManualImportCollector()
                    res = collector.import_single_item(
                        repo=repo,
                        title=in_title.strip(),
                        url=in_url.strip() or "https://manual.local/finding",
                        content=in_content.strip(),
                        source_label=in_source.strip(),
                        author=in_author.strip(),
                        forced_category=in_category,
                        forced_evidence_status=in_evidence
                    )
                    if res.get("saved"):
                        st.success(f"Record successfully saved! (ID: {res['item_id']})")
                    else:
                        st.warning("Duplicate record detected; ignored.")
                    st.rerun()

        st.markdown("<hr style='border-color: #2D3748; margin: 25px 0 20px 0;'>", unsafe_allow_html=True)
        st.markdown("##### Batch Import CSV File")
        uploaded_csv = st.file_uploader("Upload CSV (Required headers: title, url, content, source, category, evidence_status)", type=["csv"])
        if uploaded_csv:
            if st.button("Process Batch CSV"):
                content_str = uploaded_csv.getvalue().decode("utf-8")
                collector = ManualImportCollector()
                res = collector.import_from_csv(repo, content_str)
                st.success(f"Batch import completed: {res['saved_count']} new items saved from {res['total_rows']} rows.")
                st.rerun()

    # ==========================================
    # Tab 3: Data Export & Backup
    # ==========================================
    with tab3:
        st.markdown("#### Local SQLite Data Backup & CSV Intelligence Export")

        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            st.markdown("##### 📄 Export Intelligence Records to CSV")
            all_items = repo.get_collected_items(limit=10000)
            if all_items:
                df_items = pd.DataFrame(all_items)
                # Drop raw internal metadata for clean CSV
                if "raw_metadata" in df_items.columns:
                    df_items = df_items.drop(columns=["raw_metadata"])
                csv_bytes = df_items.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download Raw Observations CSV",
                    data=csv_bytes,
                    file_name=f"baf_intelligence_records_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    type="primary"
                )
            else:
                st.info("No collected items to export.")

        with col_ex2:
            st.markdown("##### 📊 Export Daily Metrics to CSV")
            all_metrics = repo.get_daily_metrics()
            if all_metrics:
                df_metrics = pd.DataFrame(all_metrics)
                metrics_csv = df_metrics.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download Daily Metrics CSV",
                    data=metrics_csv,
                    file_name=f"baf_daily_metrics_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No daily metrics to export.")

        st.markdown("<hr style='border-color: #2D3748; margin: 25px 0 20px 0;'>", unsafe_allow_html=True)
        st.markdown("##### 💾 Database Backup & Restore Instructions")
        if st.button("Create Transactionally Consistent SQLite Backup"):
            backup_path = repo.backup_database()
            st.success(f"Backup created successfully at `{backup_path}`!")

        st.markdown(
            """
            ```powershell
            # Manual CLI Backup command:
            python scripts/backup_database.py

            # Manual CLI Restore command:
            python scripts/restore_database.py data/backups/baf_risk_monitor_backup_<TIMESTAMP>.db
            ```
            """
        )
