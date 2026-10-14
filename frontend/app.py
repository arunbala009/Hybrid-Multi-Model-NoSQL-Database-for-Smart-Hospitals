"""
Smart Hospital Operations & Analytics Platform
=============================================
Streamlit Frontend Entry Point
Academic Project: Hybrid Multi-Model NoSQL Database for Smart Hospitals
"""

import os
import sys
from pathlib import Path
import streamlit as st

# Ensure repository root is in sys.path so 'frontend' package is resolvable
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from frontend.api_client import HospitalAPIClient
    from frontend.components.overview_view import render_overview
    from frontend.components.patients_view import render_patients
    from frontend.components.doctors_view import render_doctors
    from frontend.components.encounters_view import render_encounters
    from frontend.components.rooms_view import render_rooms
    from frontend.components.graph_view import render_graph_explorer
    from frontend.components.analytics_view import render_analytics
    from frontend.components.demo_view import render_demo
except ModuleNotFoundError:
    from api_client import HospitalAPIClient
    from components.overview_view import render_overview
    from components.patients_view import render_patients
    from components.doctors_view import render_doctors
    from components.encounters_view import render_encounters
    from components.rooms_view import render_rooms
    from components.graph_view import render_graph_explorer
    from components.analytics_view import render_analytics
    from components.demo_view import render_demo


# Page Configuration
st.set_page_config(
    page_title="Smart Hospital | Hybrid Multi-Model NoSQL",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Hospital Aesthetic
st.markdown("""
<style>
    /* Metric Card Styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #14B8A6;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        color: #94A3B8;
        font-weight: 500;
    }
    /* Section Headings */
    h1, h2, h3 {
        color: #F8FAFC !important;
        font-weight: 700 !important;
    }
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 6px;
    }
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid #1E293B;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Initialize API Client (reads BACKEND_URL or st.secrets or defaults to http://localhost:8000)
    client = HospitalAPIClient()

    # Sidebar Header & Navigation
    with st.sidebar:
        st.markdown("## 🏥 Smart Hospital")
        st.markdown("**Hybrid Multi-Model NoSQL**")
        st.caption("Neo4j Graph Database + Embedded Document JSON")
        st.markdown("---")

        # Health & Backend Connection Status
        health = client.check_health()
        if health["success"]:
            hdata = health["data"] or {}
            db_info = hdata.get("database", {})
            db_state = db_info.get("state", "connected") if isinstance(db_info, dict) else str(db_info)
            st.success(f"🟢 **Backend Online** ({client.base_url})\n\nDB Status: `{db_state}`")
        else:
            st.error(f"🔴 **Backend Offline** ({client.base_url})\n\n{health['error']}")
            st.caption("Ensure FastAPI is running: `uvicorn backend.app.main:app --port 8000`")

        st.markdown("---")
        st.markdown("### Navigation")
        page = st.radio(
            "Select Dashboard View",
            [
                "Overview",
                "Patients",
                "Doctors & Departments",
                "Encounters & Charting",
                "Rooms & Bed Allocation",
                "Graph Relationship Explorer",
                "Hospital Analytics",
                "Demo Dataset & Seeding"
            ],
            index=0,
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### 🎓 Academic Project Info")
        st.markdown(
            "- **Graph Model**: Neo4j AuraDB\n"
            "- **Document Model**: JSON Clinical Records\n"
            "- **Backend**: FastAPI & Pydantic\n"
            "- **Frontend**: Streamlit & Plotly\n"
            "- **Data**: Synthetic / Fictional"
        )
        st.caption("Review Stage: Prototype Evaluation")

    # Main Content Dispatcher
    if page == "Overview":
        render_overview(client)
    elif page == "Patients":
        render_patients(client)
    elif page == "Doctors & Departments":
        render_doctors(client)
    elif page == "Encounters & Charting":
        render_encounters(client)
    elif page == "Rooms & Bed Allocation":
        render_rooms(client)
    elif page == "Graph Relationship Explorer":
        render_graph_explorer(client)
    elif page == "Hospital Analytics":
        render_analytics(client)
    elif page == "Demo Dataset & Seeding":
        render_demo(client)


if __name__ == "__main__":
    main()
