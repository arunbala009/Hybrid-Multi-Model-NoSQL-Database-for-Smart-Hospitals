"""
Rooms & Bed Management View Component
=====================================
Monitors inpatient rooms, ward types, bed capacities, and real-time occupancy.
Distinguishes active admissions from historical encounters.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from frontend.api_client import HospitalAPIClient


def render_rooms(client: HospitalAPIClient):
    st.subheader("🛏️ Hospital Rooms & Bed Allocation")
    st.caption("Live inpatient occupancy tracking distinguishing active admissions from historical stays.")

    # 1. Fetch Rooms Data
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        type_filter = st.selectbox(
            "Filter Room Type",
            ["All Types", "ICU", "General Ward", "Private", "Isolation"],
            index=0,
            key="room_filter_type"
        )
    with col_f2:
        floor_filter = st.selectbox(
            "Filter Floor",
            ["All Floors", "Floor 1", "Floor 2", "Floor 3", "Floor 4"],
            index=0,
            key="room_filter_floor"
        )

    r_type = None if type_filter == "All Types" else type_filter
    r_floor = None if floor_filter == "All Floors" else int(floor_filter.split(" ")[1])

    with st.spinner("Fetching room inventory..."):
        r_res = client.get_rooms(room_type=r_type, floor=r_floor)
        occ_res = client.get_room_occupancy()

    if not r_res["success"]:
        st.error(f"Error fetching room data: {r_res['error']}")
        return

    rooms = (r_res["data"] or {}).get("items", [])
    total_rooms = len(rooms)
    total_capacity = sum(r.get("capacity", 0) for r in rooms)
    total_active_inpatients = sum(r.get("current_occupancy", 0) for r in rooms)
    available_beds = max(0, total_capacity - total_active_inpatients)
    overall_rate = round((total_active_inpatients / total_capacity * 100), 1) if total_capacity > 0 else 0.0

    # 2. KPI Banner
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Rooms In Scope", total_rooms)
    k2.metric("Total Bed Capacity", total_capacity)
    k3.metric("Active Inpatients", total_active_inpatients)
    k4.metric("Available Beds", available_beds)
    k5.metric("Occupancy Rate", f"{overall_rate}%")

    st.markdown("---")

    # 3. Room Inventory Table & Visuals
    if rooms:
        df = pd.DataFrame(rooms)
        
        # Add visual badges
        df["occupancy_label"] = df.apply(
            lambda row: f"{row.get('current_occupancy', 0)} / {row.get('capacity', 0)} beds", axis=1
        )
        df["status_indicator"] = df["is_available"].apply(lambda v: "🟢 Available" if v else "🔴 Fully Occupied")

        st.dataframe(
            df[["room_number", "room_type", "floor", "capacity", "current_occupancy", "occupancy_label", "status_indicator"]],
            column_config={
                "room_number": "Room Number",
                "room_type": "Care Category",
                "floor": "Floor",
                "capacity": "Total Beds",
                "current_occupancy": "Active Patients",
                "occupancy_label": "Utilization",
                "status_indicator": "Bed Status"
            },
            use_container_width=True,
            hide_index=True
        )

        # Visual distribution
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_types = px.bar(
                df,
                x="room_type",
                y="capacity",
                color="room_type",
                title="Bed Capacity by Room Acuity Type",
                labels={"capacity": "Beds", "room_type": "Acuity Level"}
            )
            fig_types.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC")
            st.plotly_chart(fig_types, use_container_width=True)

        with col_c2:
            fig_floor = px.pie(
                df,
                names="floor",
                values="capacity",
                title="Bed Distribution Across Hospital Floors",
                hole=0.4
            )
            fig_floor.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC")
            st.plotly_chart(fig_floor, use_container_width=True)

        # 4. Room Historical vs Active Stays Inspector
        st.markdown("---")
        st.markdown("#### 🔍 Room History & Co-Occupancy Inspector")
        st.caption("Inspect a specific room to review all current active admissions vs historical past discharges.")
        
        selected_room_id = st.selectbox(
            "Select Room to inspect historical encounters",
            [f"{r.get('room_id')} - Room {r.get('room_number')} ({r.get('room_type')})" for r in rooms],
            key="inspect_room_select"
        )

        if selected_room_id:
            room_id = selected_room_id.split(" - ")[0]
            # Fetch room sharing / encounters associated with this room
            with st.spinner("Analyzing room timeline and occupant history..."):
                sharing_res = client.get_room_sharing(room_id=room_id)

            if sharing_res["success"] and sharing_res["data"]:
                pairs = sharing_res["data"].get("room_sharing_pairs", [])
                st.write(f"Analyzed Room: `{room_id}` | Overlapping Patient Cohorts: **{len(pairs)}**")
                if pairs:
                    df_pairs = pd.DataFrame(pairs)
                    st.dataframe(
                        df_pairs[["patient1_name", "patient2_name", "overlap_start", "overlap_end", "overlap_hours"]],
                        column_config={
                            "patient1_name": "Patient 1",
                            "patient2_name": "Patient 2",
                            "overlap_start": "Overlap Period Start",
                            "overlap_end": "Overlap Period End",
                            "overlap_hours": "Duration (Hours)"
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No co-occupancy or overlapping inpatient stays detected for this room.")
            else:
                st.info("No historical co-occupancy data recorded for this room.")
    else:
        st.info("No rooms found for the selected filters.")
