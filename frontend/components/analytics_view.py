"""
Hospital Analytics View Component
=================================
Deep-dive clinical intelligence, physician caseload distributions,
department operational metrics, and epidemiological co-occupancy patterns.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
try:
    from frontend.api_client import HospitalAPIClient
except ModuleNotFoundError:
    from api_client import HospitalAPIClient


def render_analytics(client: HospitalAPIClient):
    st.subheader("📈 Clinical & Operational Analytics Dashboard")
    st.caption("Cross-entity graph analytics and clinical trajectory intelligence powered by Cypher.")

    tab_physicians, tab_depts, tab_beds, tab_pathways, tab_contacts = st.tabs([
        "👨‍⚕️ Physician Caseloads",
        "🏢 Department Operations",
        "🛏️ Bed Capacity & Occupancy",
        "🛣️ Treatment Trajectories",
        "🔬 Simulated Contact Patterns"
    ])

    # =========================================================================
    # TAB 1: Physician Caseloads
    # =========================================================================
    with tab_physicians:
        st.markdown("#### Physician Caseload and Practice Volumes")
        with st.spinner("Analyzing physician caseloads..."):
            wl_res = client.get_doctor_workload()

        if not wl_res["success"]:
            st.error(f"Failed to load physician analytics: {wl_res['error']}")
        else:
            w_data = wl_res["data"] or {}
            items = w_data.get("items", [])
            query_time = w_data.get("query_time_ms", 0)
            st.caption(f"⚡ Cypher query execution: {query_time} ms | Evaluated Doctors: {len(items)}")

            if items:
                df_wl = pd.DataFrame(items)

                c1, c2 = st.columns(2)
                with c1:
                    fig1 = px.bar(
                        df_wl,
                        x="doctor_name",
                        y="total_encounters",
                        color="specialty",
                        title="Total Encounters by Physician and Specialty",
                        labels={"doctor_name": "Physician", "total_encounters": "Encounters Handled"},
                        text_auto=True
                    )
                    fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC", xaxis_tickangle=-30)
                    st.plotly_chart(fig1, use_container_width=True)

                with c2:
                    fig2 = px.bar(
                        df_wl,
                        x="doctor_name",
                        y="active_patients",
                        color="department",
                        title="Current Active Inpatients per Physician",
                        labels={"doctor_name": "Physician", "active_patients": "Active Inpatients"},
                        text_auto=True
                    )
                    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC", xaxis_tickangle=-30)
                    st.plotly_chart(fig2, use_container_width=True)

                st.markdown("##### Detailed Physician Workload Matrix")
                st.dataframe(
                    df_wl[["doctor_name", "specialty", "department", "total_encounters", "active_patients"]],
                    column_config={
                        "doctor_name": "Physician",
                        "specialty": "Medical Specialty",
                        "department": "Department",
                        "total_encounters": "Lifetime Encounters",
                        "active_patients": "Currently Under Care"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No doctor caseload data available.")

    # =========================================================================
    # TAB 2: Department Operations
    # =========================================================================
    with tab_depts:
        st.markdown("#### Clinical Department Demand & Resource Allocation")
        with st.spinner("Loading department operational data..."):
            ds_res = client.get_department_statistics()

        if not ds_res["success"]:
            st.error(f"Failed to load department statistics: {ds_res['error']}")
        else:
            d_data = ds_res["data"] or {}
            depts = d_data.get("departments", [])

            if depts:
                df_dept = pd.DataFrame(depts)

                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    fig_d1 = px.pie(
                        df_dept,
                        names="department_name",
                        values="total_encounters",
                        title="Patient Encounter Volume by Department",
                        hole=0.45
                    )
                    fig_d1.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC")
                    st.plotly_chart(fig_d1, use_container_width=True)

                with col_d2:
                    fig_d2 = px.bar(
                        df_dept,
                        x="department_name",
                        y="total_physicians",
                        color="active_cases",
                        title="Medical Staffing vs Active Caseload",
                        labels={"department_name": "Department", "total_physicians": "Assigned Doctors", "active_cases": "Active Inpatients"},
                        text_auto=True
                    )
                    fig_d2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC")
                    st.plotly_chart(fig_d2, use_container_width=True)

                st.dataframe(
                    df_dept[["department_name", "building", "floor", "total_physicians", "total_encounters", "active_cases"]],
                    column_config={
                        "department_name": "Department",
                        "building": "Wing / Building",
                        "floor": "Floor Level",
                        "total_physicians": "Doctors",
                        "total_encounters": "Total Visits",
                        "active_cases": "Active Admissions"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No department records found.")

    # =========================================================================
    # TAB 3: Bed Capacity & Occupancy
    # =========================================================================
    with tab_beds:
        st.markdown("#### Ward Bed Capacity and Real-Time Hospital Utilization")
        with st.spinner("Analyzing hospital ward beds..."):
            ro_res = client.get_room_occupancy()

        if not ro_res["success"]:
            st.error(f"Failed to load room analytics: {ro_res['error']}")
        else:
            ro_data = ro_res["data"] or {}
            rooms = ro_data.get("rooms", [])

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Wards / Rooms", ro_data.get("total_rooms", 0))
            m2.metric("Total Bed Capacity", ro_data.get("total_bed_capacity", 0))
            m3.metric("Current Occupants", ro_data.get("current_bed_occupancy", 0))
            m4.metric("Hospital Occupancy Rate", f"{ro_data.get('occupancy_rate_percent', 0)}%")

            if rooms:
                df_rooms = pd.DataFrame(rooms)
                fig_ro = px.bar(
                    df_rooms,
                    x="room_number",
                    y=["current_occupants", "capacity"],
                    barmode="group",
                    title="Room Bed Capacity vs Current Occupancy",
                    labels={"value": "Beds", "room_number": "Room", "variable": "Metric"}
                )
                fig_ro.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC", xaxis_tickangle=-45)
                st.plotly_chart(fig_ro, use_container_width=True)
            else:
                st.info("No room data recorded.")

    # =========================================================================
    # TAB 4: Treatment Trajectories
    # =========================================================================
    with tab_pathways:
        st.markdown("#### Clinical Trajectories and Diagnostic Patterns")
        with st.spinner("Retrieving patient treatment pathway trajectories..."):
            tp_res = client.get_treatment_pathways()

        if not tp_res["success"]:
            st.error(f"Failed to load pathways: {tp_res['error']}")
        else:
            pathways = (tp_res["data"] or {}).get("pathways", [])
            if pathways:
                df_tp = pd.DataFrame(pathways)

                col_tp1, col_tp2 = st.columns(2)
                with col_tp1:
                    fig_types = px.pie(
                        df_tp,
                        names="encounter_type",
                        title="Distribution of Encounter Types",
                        hole=0.4
                    )
                    fig_types.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC")
                    st.plotly_chart(fig_types, use_container_width=True)

                with col_tp2:
                    # Explode diagnoses
                    all_diags = []
                    for d_list in df_tp["diagnoses"]:
                        if isinstance(d_list, list):
                            all_diags.extend(d_list)
                    if all_diags:
                        df_diags = pd.Series(all_diags).value_counts().reset_index()
                        df_diags.columns = ["Diagnosis", "Cases"]
                        fig_diag = px.bar(
                            df_diags.head(8),
                            x="Cases",
                            y="Diagnosis",
                            orientation="h",
                            title="Top Diagnostic Conditions",
                            text_auto=True
                        )
                        fig_diag.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC", yaxis=dict(autorange="reversed"))
                        st.plotly_chart(fig_diag, use_container_width=True)
                    else:
                        st.info("No recorded diagnoses to display.")

                st.markdown("##### Longitudinal Trajectory Records")
                st.dataframe(
                    df_tp[["patient_id", "patient_name", "encounter_id", "encounter_type", "status", "start_time", "physician", "department", "room_number"]],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No treatment pathways recorded.")

    # =========================================================================
    # TAB 5: Simulated Contact Patterns
    # =========================================================================
    with tab_contacts:
        st.markdown("#### Simulated Room Co-Occupancy & Overlap Intelligence")
        st.warning(
            "⚠️ **Epidemiological Modeling Note**: This simulation identifies distinct patients who shared inpatient room spaces "
            "within overlapping time boundaries. It does NOT establish clinical infection or transmission."
        )

        with st.spinner("Analyzing temporal co-occupancy intervals..."):
            rs_res = client.get_room_sharing()

        if not rs_res["success"]:
            st.error(f"Failed to load room sharing analytics: {rs_res['error']}")
        else:
            rs_data = rs_res["data"] or {}
            pairs = rs_data.get("overlapping_encounters", [])
            st.metric("Detected Overlapping Patient Cohorts", len(pairs))

            if pairs:
                df_pairs = pd.DataFrame(pairs)
                fig_rooms = px.histogram(
                    df_pairs,
                    x="room_number",
                    color="room_type",
                    title="Room Co-Occupancy Incident Frequency by Ward Type",
                    labels={"room_number": "Room Number", "count": "Co-Occupancy Stays"}
                )
                fig_rooms.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC")
                st.plotly_chart(fig_rooms, use_container_width=True)

                st.dataframe(
                    df_pairs[["room_number", "room_type", "patient_1_name", "patient_1_admit", "patient_2_name", "patient_2_admit"]],
                    column_config={
                        "room_number": "Room",
                        "room_type": "Care Type",
                        "patient_1_name": "Inpatient 1",
                        "patient_1_admit": "P1 Start",
                        "patient_2_name": "Inpatient 2",
                        "patient_2_admit": "P2 Start"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No overlapping room encounters found.")
