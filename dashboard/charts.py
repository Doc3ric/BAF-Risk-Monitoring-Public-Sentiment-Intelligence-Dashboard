"""Interactive Plotly charts for BAF Risk Monitor.
Provides financial-intelligence styled visualizations with dark theme and restrained accents.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Financial-intelligence dark theme palette
THEME_BG = "#0E1117"
CARD_BG = "#161B26"
GRID_COLOR = "#2A324B"
TEXT_COLOR = "#E2E8F0"

COLOR_POS = "#10B981"   # Emerald Green
COLOR_NEG = "#EF4444"   # Crimson Red
COLOR_NEU = "#64748B"   # Slate Gray
COLOR_MIX = "#F59E0B"   # Amber
COLOR_PRIMARY = "#3B82F6" # Royal Blue
COLOR_ACCENT = "#8B5CF6"  # Purple


def get_base_layout(title: str) -> Dict[str, Any]:
    return dict(
        title=dict(text=title, font=dict(family="Inter, system-ui, sans-serif", size=15, color=TEXT_COLOR)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_COLOR, size=12),
        margin=dict(l=40, r=30, t=50, b=40),
        xaxis=dict(
            gridcolor=GRID_COLOR,
            linecolor=GRID_COLOR,
            showgrid=True,
            tickfont=dict(color=TEXT_COLOR)
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR,
            linecolor=GRID_COLOR,
            showgrid=True,
            tickfont=dict(color=TEXT_COLOR)
        ),
        legend=dict(
            bgcolor="rgba(22, 27, 38, 0.8)",
            bordercolor=GRID_COLOR,
            borderwidth=1,
            font=dict(color=TEXT_COLOR)
        )
    )


def plot_sentiment_trend(metrics_df: pd.DataFrame) -> go.Figure:
    """Plot daily positive vs negative vs neutral mentions over time."""
    fig = go.Figure()

    if metrics_df.empty:
        fig.add_annotation(
            text="No historical metrics recorded yet.<br>Run collection to populate observations.",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(color="#94A3B8", size=14)
        )
        fig.update_layout(**get_base_layout("Sentiment Mentions Over Time"))
        return fig

    fig.add_trace(go.Bar(
        x=metrics_df["date"],
        y=metrics_df["positive_mentions"],
        name="Positive Mentions",
        marker_color=COLOR_POS,
        opacity=0.85
    ))

    fig.add_trace(go.Bar(
        x=metrics_df["date"],
        y=metrics_df["negative_mentions"],
        name="Negative Mentions",
        marker_color=COLOR_NEG,
        opacity=0.85
    ))

    fig.add_trace(go.Bar(
        x=metrics_df["date"],
        y=metrics_df["mixed_mentions"],
        name="Mixed / Uncertain",
        marker_color=COLOR_MIX,
        opacity=0.85
    ))

    fig.add_trace(go.Scatter(
        x=metrics_df["date"],
        y=metrics_df["total_items_collected"],
        mode="lines+markers",
        name="Total Items",
        line=dict(color=COLOR_PRIMARY, width=2, dash="dot"),
        marker=dict(size=5)
    ))

    layout = get_base_layout("Daily Positive vs. Negative Sentiment Mentions")
    layout["barmode"] = "group"
    fig.update_layout(**layout)
    return fig


def plot_complaint_volume(metrics_df: pd.DataFrame) -> go.Figure:
    """Plot daily complaint volume and corroborated events."""
    fig = go.Figure()

    if metrics_df.empty:
        fig.add_annotation(
            text="No complaint data recorded yet.",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(color="#94A3B8", size=14)
        )
        fig.update_layout(**get_base_layout("Daily Complaint Volume & Corroborated Events"))
        return fig

    fig.add_trace(go.Scatter(
        x=metrics_df["date"],
        y=metrics_df["complaint_volume"],
        mode="lines+markers",
        name="Complaint Volume",
        line=dict(color=COLOR_NEG, width=3),
        fill="tozeroy",
        fillcolor="rgba(239, 68, 68, 0.15)",
        marker=dict(size=6, color=COLOR_NEG)
    ))

    fig.add_trace(go.Bar(
        x=metrics_df["date"],
        y=metrics_df["corroborated_events"],
        name="Corroborated Events",
        marker_color=COLOR_ACCENT,
        opacity=0.7
    ))

    fig.add_trace(go.Bar(
        x=metrics_df["date"],
        y=metrics_df["doc_changes_detected"],
        name="Documentation Changes",
        marker_color=COLOR_MIX,
        opacity=0.7
    ))

    layout = get_base_layout("Daily Complaint Volume & Warning Signals")
    fig.update_layout(**layout)
    return fig


def plot_category_breakdown(items_df: pd.DataFrame) -> go.Figure:
    """Plot distribution of issue categories."""
    fig = go.Figure()

    if items_df.empty or "primary_category" not in items_df.columns:
        fig.add_annotation(
            text="No categorized items found.",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(color="#94A3B8", size=14)
        )
        fig.update_layout(**get_base_layout("Intelligence Category Breakdown"))
        return fig

    cat_counts = items_df["primary_category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]

    # Format category names
    cat_counts["Formatted"] = cat_counts["Category"].str.replace("_", " ").str.title()

    fig = px.bar(
        cat_counts,
        x="Count",
        y="Formatted",
        orientation="h",
        color="Count",
        color_continuous_scale="Viridis",
        title="Intelligence Records by Topic Category"
    )

    layout = get_base_layout("Distribution of Intelligence Records by Category")
    layout["yaxis"]["autorange"] = "reversed"
    layout["coloraxis_showscale"] = False
    fig.update_layout(**layout)
    return fig


def plot_source_distribution(items_df: pd.DataFrame) -> go.Figure:
    """Plot items collected by source name."""
    fig = go.Figure()

    if items_df.empty or "source_name" not in items_df.columns:
        fig.add_annotation(
            text="No source distribution available.",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(color="#94A3B8", size=14)
        )
        fig.update_layout(**get_base_layout("Items Collected by Source"))
        return fig

    src_counts = items_df["source_name"].fillna("Unknown Source").value_counts().reset_index()
    src_counts.columns = ["Source", "Count"]

    fig = px.pie(
        src_counts,
        values="Count",
        names="Source",
        hole=0.45,
        color_discrete_sequence=[COLOR_PRIMARY, COLOR_ACCENT, COLOR_POS, COLOR_MIX, COLOR_NEG]
    )

    layout = get_base_layout("Proportion of Records by Monitored Source")
    fig.update_layout(**layout)
    return fig
