"""
Motorsport-Themed Styling, CSS Injections, and Plotly Graph Themes.
Provides high-octane F1 visual identity: carbon black, racing red accents,
crisp telemetry fonts, glowing metric cards, and responsive layouts.
"""

import plotly.graph_objects as go
import streamlit as st

F1_THEME_CSS = """
<style>
/* Main container styling */
.stApp {
    background-color: #0B0C10;
    color: #E0E2EC;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #12131C !important;
    border-right: 1px solid #232533;
}

/* Custom telemetry metric cards */
.f1-card {
    background: linear-gradient(135deg, #161724 0%, #1A1C2C 100%);
    border: 1px solid #282A3E;
    border-top: 3px solid #E10600;
    border-radius: 8px;
    padding: 18px 20px;
    margin-bottom: 14px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
    transition: transform 0.15s ease, border-color 0.15s ease;
}

.f1-card:hover {
    border-color: #E10600;
    transform: translateY(-2px);
}

.f1-card-label {
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #8C90A4;
    margin-bottom: 4px;
}

.f1-card-value {
    font-size: 1.85rem;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.5px;
    font-family: 'Consolas', 'Courier New', monospace;
}

.f1-card-sub {
    font-size: 0.78rem;
    color: #00D2BE;
    margin-top: 4px;
}

/* Badges */
.badge-demo {
    background: #E10600;
    color: #FFFFFF;
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 1px;
    display: inline-block;
}

.badge-live {
    background: #00D2BE;
    color: #0B0C10;
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 1px;
    display: inline-block;
}

/* Tab headers */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: transparent;
    border-bottom: 1px solid #282A3E;
}

.stTabs [data-baseweb="tab"] {
    background-color: #161724;
    border: 1px solid #232536;
    border-radius: 6px 6px 0 0;
    color: #A0A4B8;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 0.85rem;
}

.stTabs [aria-selected="true"] {
    background-color: #E10600 !important;
    color: #FFFFFF !important;
    border-color: #E10600 !important;
}

/* Tables styling */
div[data-testid="stDataFrame"] {
    border: 1px solid #282A3E;
    border-radius: 6px;
    background-color: #12131C;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(180deg, #E10600 0%, #B30000 100%);
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    font-weight: 700;
    letter-spacing: 0.8px;
    padding: 6px 18px;
    transition: all 0.2s ease;
}

.stButton>button:hover {
    background: #FF1801;
    color: #FFFFFF;
    box-shadow: 0 0 12px rgba(225, 6, 0, 0.6);
}
</style>
"""

def inject_f1_theme():
    """Injects high-octane F1 dark theme styling into the Streamlit session."""
    st.markdown(F1_THEME_CSS, unsafe_allow_html=True)

def apply_f1_plot_theme(fig: go.Figure, title: str = "", height: int = 420) -> go.Figure:
    """
    Applies custom motorsport dark theme to any Plotly chart.
    """
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#12131C",
        plot_bgcolor="#161724",
        margin=dict(l=45, r=25, t=55 if title else 25, b=45),
        height=height,
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(size=14, color="#FFFFFF", family="Segoe UI, sans-serif"),
            x=0.01,
            y=0.96
        ),
        legend=dict(
            bgcolor="rgba(22, 23, 36, 0.85)",
            bordercolor="#282A3E",
            borderwidth=1,
            font=dict(color="#D0D4E4", size=11),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hoverlabel=dict(
            bgcolor="#1A1C2C",
            bordercolor="#E10600",
            font=dict(color="#FFFFFF", size=11, family="Consolas, monospace")
        )
    )
    fig.update_xaxes(
        gridcolor="#232538",
        zerolinecolor="#2E314A",
        tickfont=dict(color="#8E92A8", size=10),
        title_font=dict(color="#B5B9D0", size=11)
    )
    fig.update_yaxes(
        gridcolor="#232538",
        zerolinecolor="#2E314A",
        tickfont=dict(color="#8E92A8", size=10),
        title_font=dict(color="#B5B9D0", size=11)
    )
    return fig

def render_metric_card(label: str, value: str, subtext: str = "", delta_color: str = "#00D2BE") -> str:
    """Returns HTML for an F1 styled metric card."""
    sub_html = f'<div class="f1-card-sub" style="color: {delta_color};">{subtext}</div>' if subtext else ""
    return f"""
    <div class="f1-card">
        <div class="f1-card-label">{label}</div>
        <div class="f1-card-value">{value}</div>
        {sub_html}
    </div>
    """
