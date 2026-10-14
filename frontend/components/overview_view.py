"""
Overview Page Component
=======================
Renders operational hospital KPIs, real-time admission metrics, and workload visualizations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
try:
    from frontend.api_client import HospitalAPIClient
except ModuleNotFoundError:
    from api_client import HospitalAPIClient


def render_overview(client: HospitalAPIClient):
    st.subheader("🏥 Hospital Operational Overview")
    st.caption("Real-time clinical metrics powered by Neo4j graph traversals and aggregate Cypher queries.")

    # 1. Fetch Overview KPIs
    with st.spinner("Fetching hospital KPIs..."):
        res = client.get_overview_analytics()

    if not res["success"]:
        st.error(f"Failed to load analytics: {res['error']}")
        st.info("Ensure the FastAPI backend is running on the configured host.")
        return

    data = res["data"] or {}
    total_patients = data.get("total_patients", 0)
    total_doctors = data.get("total_doctors", 0)
    total_departments = data.get("total_departments", 0)
    total_encounters = data.get("total_encounters", 0)
    active_admissions = data.get("active_admissions", 0)
    total_rooms = data.get("total_rooms", 0)
    query_time_ms = data.get("query_time_ms", 0)

    # 2. Render Metric Cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Registered Patients", total_patients)
    c2.metric("Medical Staff", total_doctors)
    c3.metric("Departments", total_departments)
    c4.metric("Total Encounters", total_encounters)
    c5.metric("Active Admissions", active_admissions)
    c6.metric("Total Rooms", total_rooms)

    st.caption(f"⚡ Cypher execution time: {query_time_ms} ms (Neo4j server result availability)")
    st.markdown("---")

    # 3. Workload and Department Charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 👨‍⚕️ Physician Caseload Distribution")
        doc_res = client.get_doctor_workload()
        if doc_res["success"] and doc_res["data"] and doc_res["data"].get("items"):
            items = doc_res["data"]["items"]
            df_docs = pd.DataFrame(items)
            fig = px.bar(
                df_docs,
                x="doctor_name",
                y="total_encounters",
                color="specialty",
                labels={"doctor_name": "Physician", "total_encounters": "Encounters Handled", "specialty": "Specialty"},
                title="Encounters per Physician",
                text_auto=True
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F8FAFC",
                xaxis_tickangle=-30
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No doctor caseload data available yet. Seed the database to view live metrics.")

    with col_right:
        st.markdown("#### 🏢 Department Case Volumes")
        dept_res = client.get_department_statistics()
        if dept_res["success"] and dept_res["data"] and dept_res["data"].get("departments"):
            depts = dept_res["data"]["departments"]
            df_dept = pd.DataFrame(depts)
            fig_dept = px.pie(
                df_dept,
                names="department_name",
                values="total_encounters",
                title="Clinical Encounters by Department",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Teal
            )
            fig_dept.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#F8FAFC"
            )
            st.plotly_chart(fig_dept, use_container_width=True)
        else:
            st.info("No department volume data available yet.")

    # 4. Ward Bed Utilization
    st.markdown("#### 🛏️ Live Inpatient Room & Bed Utilization")
    room_res = client.get_room_occupancy()
    if room_res["success"] and room_res["data"] and room_res["data"].get("rooms"):
        rdata = room_res["data"]
        r_cols = st.columns(4)
        r_cols[0].metric("Occupied Rooms", rdata.get("occupied_rooms", 0))
        r_cols[1].metric("Total Bed Capacity", rdata.get("total_bed_capacity", 0))
        r_cols[2].metric("Current Patients In Beds", rdata.get("current_bed_occupancy", 0))
        r_cols[3].metric("Occupancy Rate", f"{rdata.get('occupancy_rate_percent', 0.0)}%")

        df_rooms = pd.DataFrame(rdata["rooms"])
        st.dataframe(
            df_rooms[["room_number", "room_type", "floor", "capacity", "current_occupants", "is_available"]],
            column_config={
                "room_number": "Room Sign",
                "room_type": "Care Acuity",
                "floor": "Floor Level",
                "capacity": "Bed Capacity",
                "current_occupants": "Current Occupants",
                "is_available": "Bed Available?"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No room occupancy records available.")
