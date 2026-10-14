"""
Smart Hospital Chart Helper
===========================
Renders Plotly charts reliably across both direct and tunneled environments.
Uses CDN-backed Plotly embedding to eliminate large 4.7MB chunk downloads over reverse tunnels.
"""

import streamlit as st


def render_plotly_chart(fig, height: int = 420):
    """
    Renders an interactive Plotly figure.
    Uses CDN-backed HTML iframe to prevent browser 'failed to fetch dynamically imported module'
    errors caused by reverse proxy bandwidth/buffer limits on the 4.7MB PlotlyChart.js bundle.
    Falls back to native st.plotly_chart if HTML export is unavailable.
    """
    try:
        html = fig.to_html(include_plotlyjs="cdn", full_html=False)
        st.components.v1.html(html, height=height)
    except Exception:
        try:
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.plotly_chart(fig)
