"""
Demo Dataset & Seeding Controller Component
===========================================
Displays synthetic dataset catalog, data preview specifications,
and manages controlled, authenticated dry-run and live database seeding.
"""

import streamlit as st
import pandas as pd
from frontend.api_client import HospitalAPIClient


def render_demo(client: HospitalAPIClient):
    st.subheader("🧪 Synthetic Demo Dataset & Safe Seeding Controller")
    st.caption("Deterministic synthetic hospital dataset catalog with strict write safety controls.")

    tab_preview, tab_seed = st.tabs([
        "📖 Synthetic Dataset Catalog",
        "⚙️ Controlled Database Seeder"
    ])

    # =========================================================================
    # TAB 1: Synthetic Dataset Catalog
    # =========================================================================
    with tab_preview:
        st.markdown("#### Synthetic Healthcare Dataset Specifications")
        st.info(
            "ℹ️ **Academic & Synthetic Data Compliance**: All clinical profiles, physician credentials, "
            "vitals, and encounter histories are entirely synthetic and fictional for academic evaluation."
        )

        with st.spinner("Fetching dataset catalog specification..."):
            res = client.get_demo_status()

        if not res["success"]:
            st.error(f"Failed to load dataset status: {res['error']}")
        else:
            spec = (res["data"] or {}).get("dataset_specification", {})

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Fictional Patients", spec.get("total_patients", 20))
            m2.metric("Staff Doctors", spec.get("total_doctors", 8))
            m3.metric("Departments", spec.get("total_departments", 4))
            m4.metric("Inpatient Rooms", spec.get("total_rooms", 15))
            m5.metric("Clinical Encounters", spec.get("total_encounters", 35))

            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("##### Clinical Specialties Represented")
                specialties = spec.get("specialties", ["Cardiology", "Neurology", "Orthopedics", "Emergency Medicine"])
                for s in specialties:
                    st.markdown(f"- 🩺 **{s}**")

                st.markdown("##### Room Acuity Categories")
                room_types = spec.get("room_types", ["ICU", "General Ward", "Private", "Isolation"])
                for rt in room_types:
                    st.markdown(f"- 🛏️ **{rt}**")

            with col_b:
                st.markdown("##### Document-Style Health Record Schemas")
                st.markdown("- **Vital Signs:** Temp, Heart Rate, Blood Pressure (Sys/Dia), Resp Rate, SpO2")
                st.markdown("- **Clinical Notes:** Chief Complaint, Assessment & Plan, Discharge Summary")
                st.markdown("- **Diagnostic Panels:** Cardiac Panel, Metabolic Panel, Lipid Profile, CBC")
                st.markdown("- **Treatment Records:** Medications Administered, Bedside Procedures, Nursing Care Plans")

    # =========================================================================
    # TAB 2: Controlled Database Seeder
    # =========================================================================
    with tab_seed:
        st.markdown("#### Database Seeding Administration")
        
        st.warning(
            "🔒 **SAFETY LOCK**: Live database writes must be approved before execution. "
            "By default, all operations run in **Dry Run mode** to validate schema integrity without modifying any records in Neo4j."
        )

        with st.form("form_seeder"):
            st.markdown("##### 1. Execution Mode")
            mode = st.radio(
                "Select Execution Mode",
                [
                    "Dry Run (Validation Only — Zero Database Writes)",
                    "Live Database Seeding (Inserts Nodes & Edges into Connected Database)"
                ],
                index=0,
                key="seed_mode_selection"
            )
            is_dry_run = "Dry Run" in mode

            st.markdown("##### 2. Authentication & Confirmation")
            token_input = st.text_input(
                "Admin / Demo Access Token *",
                type="password",
                placeholder="Enter configured DEMO_SEED_TOKEN...",
                help="The token configured in the backend environment. Never exposed in URLs, logs, or UI."
            )

            confirm_check = st.checkbox(
                "I explicitly confirm that the target database instance has been reviewed and approved for this action.",
                key="confirm_seed_target"
            )

            btn_execute = st.form_submit_button("🚀 Run Seeder Action", type="primary" if not is_dry_run else "secondary")

            if btn_execute:
                if not token_input.strip():
                    st.error("Authentication Error: Demo / Admin token is required.")
                elif not confirm_check:
                    st.error("Confirmation Error: You must explicitly confirm approval of the target database.")
                else:
                    status_text = "Executing dry-run validation..." if is_dry_run else "Performing live database seeding..."
                    with st.spinner(status_text):
                        seed_res = client.seed_demo_data(token=token_input.strip(), dry_run=is_dry_run)

                    if not seed_res["success"]:
                        st.error(f"Seeder Execution Failed: {seed_res['error']}")
                    else:
                        data = seed_res["data"] or {}
                        if is_dry_run:
                            st.success("✅ Dry Run Completed Successfully! (Zero writes occurred)")
                            st.json(data)
                        else:
                            st.success("🎉 Live Database Seeding Completed Successfully!")
                            st.json(data)
                            st.info("Navigate to the Overview or Patients page to explore the populated hospital database.")
