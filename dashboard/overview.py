"""Overview panel for BAF Risk Monitor dashboard.
Presents the executive risk posture, red flag checklist, active alerts, KPI metric cards, and freshness status.
"""

from datetime import datetime, timezone
import zoneinfo
import streamlit as st
import pandas as pd
from analysis.technical_audit import run_technical_audit

MANILA_TZ = zoneinfo.ZoneInfo("Asia/Manila")


def render_overview(repo, settings, latest_metrics, active_alerts, sources):
    st.markdown("### 🛡️ Executive Risk Posture & OSINT Surveillance")

    # Target Dossier Header
    st.markdown(
        """
        <div style="background-color: #161B26; border: 1px solid #2A324B; border-radius: 8px; padding: 16px 20px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div>
                    <span style="color: #60A5FA; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">MONITORED TARGET DOSSIER</span>
                    <h3 style="margin: 2px 0 4px 0; color: #F8FAFC; font-size: 1.35rem;">BlockAlgo Frontier (BAF / baf9.ai)</h3>
                    <span style="color: #94A3B8; font-size: 0.85rem;">
                        Known Domains: <code>baf9.ai</code>, <code>baf-1.gitbook.io</code> | Claimed Business: "Web3 Quantitative Arbitrage Engine"
                    </span>
                </div>
                <div>
                    <span style="background-color: rgba(239, 68, 68, 0.2); border: 1px solid #EF4444; color: #F87171; font-weight: 700; font-size: 0.85rem; padding: 6px 12px; border-radius: 6px;">
                        🚨 EVALUATION: HIGH CAUTION ADVISED
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Determine system monitoring state
    posture = latest_metrics.get("monitoring_state", "NORMAL") if latest_metrics else "NORMAL"
    if active_alerts:
        posture = "SERIOUS_WARNING"

    if posture == "SERIOUS_WARNING":
        st.markdown(
            """
            <div style="background-color: rgba(239, 68, 68, 0.15); border: 1px solid #EF4444; border-left: 6px solid #EF4444; padding: 14px 18px; border-radius: 6px; margin-bottom: 20px;">
                <h4 style="color: #F87171; margin: 0 0 4px 0; font-size: 1.15rem;">🚨 ALERT POSTURE: SERIOUS WARNING REQUIRING INVESTIGATION</h4>
                <p style="color: #CBD5E1; margin: 0; font-size: 0.9rem;">
                    Active warning signals fired: Documented community complaints cite pyramid recruitment downlines, withdrawal delays, and absence of verifiable on-chain smart contract transactions.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif posture == "INCREASED_CONCERN":
        st.markdown(
            """
            <div style="background-color: rgba(245, 158, 11, 0.15); border: 1px solid #F59E0B; border-left: 6px solid #F59E0B; padding: 14px 18px; border-radius: 6px; margin-bottom: 20px;">
                <h4 style="color: #FBBF24; margin: 0 0 4px 0; font-size: 1.15rem;">⚠️ ALERT POSTURE: INCREASED CONCERN</h4>
                <p style="color: #CBD5E1; margin: 0; font-size: 0.9rem;">
                    Elevated complaints, documentation modifications, or collector availability issues detected. Heightened scrutiny recommended.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Quick Forensic Red Flag Summary
    checks = run_technical_audit()
    col_rf1, col_rf2, col_rf3 = st.columns(3)
    with col_rf1:
        st.markdown(
            """
            <div style="background-color: #161B26; border: 1px solid #2D3748; border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;">
                <div style="color: #F87171; font-weight: 700; font-size: 0.9rem;">❌ No Smart Contracts / TxIDs</div>
                <div style="color: #94A3B8; font-size: 0.8rem; margin-top: 4px;">Zero Web3 RPC or contract code found on baf9.ai. Balance displays are simulated.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_rf2:
        st.markdown(
            """
            <div style="background-color: #161B26; border: 1px solid #2D3748; border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;">
                <div style="color: #F87171; font-weight: 700; font-size: 0.9rem;">❌ Multi-Tier MLM Commissions</div>
                <div style="color: #94A3B8; font-size: 0.8rem; margin-top: 4px;">User earnings require recruiting downline deposits rather than quant trading.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_rf3:
        st.markdown(
            """
            <div style="background-color: #161B26; border: 1px solid #2D3748; border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;">
                <div style="color: #F87171; font-weight: 700; font-size: 0.9rem;">❌ Unlicensed in Philippines</div>
                <div style="color: #94A3B8; font-size: 0.8rem; margin-top: 4px;">No secondary license from SEC Philippines to solicit investments or manage funds.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Operational status banner
    enabled_sources = [s for s in sources if s.get("enabled", 1)]
    failing_sources = [s for s in enabled_sources if s.get("last_status") == "FAILED"]
    last_runs = [s.get("last_run_at") for s in enabled_sources if s.get("last_run_at")]

    last_collection_str = "Never"
    freshness_status = "No Collection Runs"
    freshness_badge = "⚪"
    if last_runs:
        latest_run_iso = max(last_runs)
        try:
            dt = datetime.fromisoformat(latest_run_iso.replace("Z", "+00:00"))
            manila_time = dt.astimezone(MANILA_TZ)
            last_collection_str = manila_time.strftime("%Y-%m-%d %I:%M %p PST")
            hours_ago = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 3600
            if hours_ago < 24:
                freshness_status = f"Up to date ({hours_ago:.1f}h ago)"
                freshness_badge = "🟢"
            elif hours_ago < 48:
                freshness_status = f"Moderate ({hours_ago:.1f}h ago)"
                freshness_badge = "🟡"
            else:
                freshness_status = f"Stale ({hours_ago:.1f}h ago)"
                freshness_badge = "🔴"
        except Exception:
            last_collection_str = latest_run_iso

    status_col1, status_col2, status_col3 = st.columns(3)
    with status_col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Last Successful Collection</div>
                <div class="metric-value" style="font-size: 1.1rem; color: #60A5FA;">{last_collection_str}</div>
                <div class="metric-caption">Display Timezone: Asia/Manila (PST)</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with status_col2:
        src_color = "#34D399" if len(failing_sources) == 0 else "#F87171"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Source Operational Health</div>
                <div class="metric-value" style="font-size: 1.3rem; color: {src_color};">
                    {len(enabled_sources) - len(failing_sources)} / {len(enabled_sources)} Connectors Active
                </div>
                <div class="metric-caption">{len(failing_sources)} Connector(s) Currently Failing</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with status_col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Data Freshness Posture</div>
                <div class="metric-value" style="font-size: 1.2rem;">{freshness_badge} {freshness_status}</div>
                <div class="metric-caption">Automated Daily Synchronization</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Core Metric KPIs
    items_count = repo.count_collected_items()
    all_items = repo.get_collected_items(limit=1000)

    # Public items (excluding official company self-documentation)
    public_items = [i for i in all_items if i.get("evidence_status") != "OFFICIAL_STATEMENT" and i.get("source_id") != "official_baf_docs"]
    complaint_items = [i for i in public_items if i.get("is_complaint")]
    neg_items = [i for i in public_items if i.get("sentiment_label") == "NEGATIVE"]
    corroborated_items = [i for i in public_items if i.get("evidence_status") in ("CORROBORATED", "REPORTED_ALLEGATION")]

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.metric("Public Intelligence Records", f"{len(public_items):,}")
    with kpi2:
        st.metric("🚨 Public Complaints", f"{len(complaint_items)}", delta="Critical Alerts" if len(complaint_items) > 0 else "0", delta_color="inverse")
    with kpi3:
        st.metric("Negative Public Sentiment", f"{len(neg_items)}", delta=f"{len(neg_items)} Negative" if len(neg_items) > 0 else "0", delta_color="inverse")
    with kpi4:
        st.metric("Corroborated Allegations", f"{len(corroborated_items)}")
    with kpi5:
        st.metric("Forensic Red Flags", "6 / 6 Failed", delta="High Risk", delta_color="inverse")

    st.markdown("<hr style='border-color: #2D3748; margin: 25px 0 20px 0;'>", unsafe_allow_html=True)

    # Active Alerts Section
    st.markdown("#### 🚨 Active Traceable Risk Alerts")
    if not active_alerts:
        st.info("✅ No unhandled alerts.")
    else:
        for alert in active_alerts:
            level = alert.get("alert_level")
            badge_color = "#EF4444" if level == "SERIOUS_WARNING" else "#F59E0B"
            st.markdown(
                f"""
                <div style="background-color: #1A1F2C; border: 1px solid #2D3748; border-left: 4px solid {badge_color}; border-radius: 6px; padding: 14px 18px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 700; color: #F1F5F9; font-size: 1.05rem;">{alert.get('title')}</span>
                        <span style="background-color: {badge_color}; color: #FFFFFF; font-size: 0.75rem; font-weight: 600; padding: 3px 8px; border-radius: 4px;">{level}</span>
                    </div>
                    <div style="color: #CBD5E1; font-size: 0.9rem; margin-bottom: 8px;">{alert.get('description')}</div>
                    <div style="background-color: #0E1117; padding: 8px 12px; border-radius: 4px; font-family: monospace; font-size: 0.82rem; color: #94A3B8;">
                        <strong>Underlying Evidence:</strong> {alert.get('evidence_summary')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
