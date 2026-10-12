"""Overview panel for BAF Risk Monitor dashboard.
Presents the executive risk posture, active alerts, KPI metric cards, and freshness status.
"""

from datetime import datetime, timezone
import zoneinfo
import streamlit as st
import pandas as pd

MANILA_TZ = zoneinfo.ZoneInfo("Asia/Manila")


def render_overview(repo, settings, latest_metrics, active_alerts, sources):
    st.markdown("### Executive Risk Posture & Operational Intelligence")

    # Determine system monitoring state
    posture = latest_metrics.get("monitoring_state", "NORMAL") if latest_metrics else "NORMAL"

    if posture == "SERIOUS_WARNING":
        st.markdown(
            """
            <div style="background-color: rgba(239, 68, 68, 0.15); border: 1px solid #EF4444; border-left: 6px solid #EF4444; padding: 16px 20px; border-radius: 6px; margin-bottom: 20px;">
                <h3 style="color: #F87171; margin: 0 0 6px 0; font-size: 1.25rem;">⚠️ POSTURE: SERIOUS WARNING REQUIRING INVESTIGATION</h3>
                <p style="color: #CBD5E1; margin: 0; font-size: 0.95rem;">
                    Critical warning triggers have fired (e.g. surge in withdrawal failure reports, regulatory warning, or severe payment blocks).
                    Immediate manual cross-verification of evidence is advised.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif posture == "INCREASED_CONCERN":
        st.markdown(
            """
            <div style="background-color: rgba(245, 158, 11, 0.15); border: 1px solid #F59E0B; border-left: 6px solid #F59E0B; padding: 16px 20px; border-radius: 6px; margin-bottom: 20px;">
                <h3 style="color: #FBBF24; margin: 0 0 6px 0; font-size: 1.25rem;">⚠️ POSTURE: INCREASED CONCERN</h3>
                <p style="color: #CBD5E1; margin: 0; font-size: 0.95rem;">
                    Elevated complaints, documentation modifications, or collector availability issues detected. Heightened scrutiny recommended.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style="background-color: rgba(16, 185, 129, 0.15); border: 1px solid #10B981; border-left: 6px solid #10B981; padding: 16px 20px; border-radius: 6px; margin-bottom: 20px;">
                <h3 style="color: #34D399; margin: 0 0 6px 0; font-size: 1.25rem;">🛡️ POSTURE: NORMAL MONITORING</h3>
                <p style="color: #CBD5E1; margin: 0; font-size: 0.95rem;">
                    No acute withdrawal clusters or regulatory enforcement actions identified. Automated daily surveillance active.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Calculate status & freshness
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

    # Operational status banner
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
                    {len(enabled_sources) - len(failing_sources)} / {len(enabled_sources)} Active
                </div>
                <div class="metric-caption">{len(failing_sources)} Source(s) Currently Failing</div>
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
    pos_count = latest_metrics.get("positive_mentions", 0) if latest_metrics else 0
    neg_count = latest_metrics.get("negative_mentions", 0) if latest_metrics else 0
    neu_mix_count = (latest_metrics.get("neutral_mentions", 0) + latest_metrics.get("mixed_mentions", 0)) if latest_metrics else 0
    complaint_count = latest_metrics.get("complaint_volume", 0) if latest_metrics else 0
    corroborated_count = latest_metrics.get("corroborated_events", 0) if latest_metrics else 0
    doc_changes_count = latest_metrics.get("doc_changes_detected", 0) if latest_metrics else 0

    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
    with kpi1:
        st.metric("Total BAF Items", f"{items_count:,}")
    with kpi2:
        st.metric("Positive Sentiment", f"{pos_count}", delta=None)
    with kpi3:
        st.metric("Negative Sentiment", f"{neg_count}", delta=f"-{neg_count}" if neg_count > 0 else "0", delta_color="inverse")
    with kpi4:
        st.metric("Neutral / Mixed", f"{neu_mix_count}")
    with kpi5:
        st.metric("Complaint Reports", f"{complaint_count}", delta="Actionable" if complaint_count > 0 else "None", delta_color="inverse")
    with kpi6:
        st.metric("Corroborated Alerts", f"{corroborated_count}", delta=f"{doc_changes_count} doc diffs")

    st.markdown("<hr style='border-color: #2D3748; margin: 25px 0 20px 0;'>", unsafe_allow_html=True)

    # Active Alerts Section
    st.markdown("#### 🚨 Active Traceable Risk Alerts")
    if not active_alerts:
        st.info("✅ No active risk triggers currently fired. Normal monitoring parameters satisfied.")
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
