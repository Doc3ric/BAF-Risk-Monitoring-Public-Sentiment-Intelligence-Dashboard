"""Forensic Audit & Red Flags view for BAF Risk Monitor.
Presents side-by-side technical verification of platform claims vs OSINT evidence.
"""

import streamlit as st
import pandas as pd
from analysis.technical_audit import run_technical_audit


def render_forensic_audit():
    st.markdown("### 🔬 OSINT Technical Forensic Audit & Red Flag Matrix")
    st.markdown(
        "<p style='color: #94A3B8; font-size: 0.95rem;'>"
        "Direct evidence-based cross-examination comparing <strong>BlockAlgo Frontier's published claims</strong> "
        "against <strong>verified technical and regulatory findings</strong>."
        "</p>",
        unsafe_allow_html=True
    )

    checks = run_technical_audit()

    critical_count = sum(1 for c in checks if c["risk_level"] == "CRITICAL")
    high_count = sum(1 for c in checks if c["risk_level"] == "HIGH")

    # High-level summary
    st.markdown(
        f"""
        <div style="background-color: rgba(239, 68, 68, 0.12); border: 1px solid #EF4444; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="color: #F87171; margin: 0 0 4px 0; font-size: 1.15rem;">⚠️ FORENSIC VERDICT: HIGH CONCERN (MULTIPLE CRITICAL RED FLAGS)</h4>
                    <p style="color: #CBD5E1; margin: 0; font-size: 0.9rem;">
                        Failed {critical_count} critical technical and regulatory tests. Zero on-chain proof of quantitative arbitrage trading.
                    </p>
                </div>
                <div style="display: flex; gap: 8px;">
                    <span style="background-color: #EF4444; color: #FFF; padding: 4px 10px; border-radius: 4px; font-weight: 700; font-size: 0.85rem;">
                        {critical_count} CRITICAL
                    </span>
                    <span style="background-color: #F59E0B; color: #000; padding: 4px 10px; border-radius: 4px; font-weight: 700; font-size: 0.85rem;">
                        {high_count} HIGH
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Forensic checks cards
    for check in checks:
        badge_color = check["badge_color"]
        st.markdown(
            f"""
            <div style="background-color: #161B26; border: 1px solid #2D3748; border-left: 5px solid {badge_color}; border-radius: 6px; padding: 18px 20px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h4 style="margin: 0; color: #F8FAFC; font-size: 1.1rem;">{check['name']}</h4>
                    <span style="background-color: {badge_color}; color: #FFFFFF; padding: 3px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 700;">
                        {check['verdict']}
                    </span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 12px;">
                    <div style="background-color: #0E1117; padding: 12px 14px; border-radius: 6px; border: 1px solid #1E293B;">
                        <span style="color: #94A3B8; font-size: 0.78rem; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 4px;">Company Claim (GitBook / Promo)</span>
                        <p style="color: #E2E8F0; font-size: 0.88rem; margin: 0; line-height: 1.4;">{check['claim']}</p>
                    </div>
                    <div style="background-color: #0E1117; padding: 12px 14px; border-radius: 6px; border: 1px solid #1E293B;">
                        <span style="color: #F87171; font-size: 0.78rem; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 4px;">Independent Forensic Finding</span>
                        <p style="color: #E2E8F0; font-size: 0.88rem; margin: 0; line-height: 1.4;">{check['reality']}</p>
                    </div>
                </div>
                <div style="background-color: #1A2234; padding: 8px 12px; border-radius: 4px; font-family: monospace; font-size: 0.82rem; color: #94A3B8;">
                    <strong>Technical Evidence:</strong> {check['evidence']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
