"""
Patients View Component
=======================
Handles patient directory browsing, search, pagination, detailed care history,
validated patient registration, and safe patient record deletion.
"""

import streamlit as st
import pandas as pd
from typing import Optional
try:
    from frontend.api_client import HospitalAPIClient
except ModuleNotFoundError:
    from api_client import HospitalAPIClient


def render_patients(client: HospitalAPIClient):
    st.subheader("👥 Patient Directory & Clinical Records")
    st.caption("Longitudinal patient index and master identity management.")

    tab_list, tab_detail, tab_create = st.tabs([
        "📋 Patient Directory",
        "🔍 Patient Profile & History",
        "➕ Register New Patient"
    ])

    # =========================================================================
    # TAB 1: Patient Directory
    # =========================================================================
    with tab_list:
        c_search, c_limit, c_page = st.columns([3, 1, 1])
        with c_search:
            search_query = st.text_input(
                "Search Patients",
                placeholder="Search by first name, last name, or ID...",
                key="patient_search_query"
            )
        with c_limit:
            page_size = st.selectbox("Page Size", [10, 25, 50], index=0, key="patient_page_size")
        with c_page:
            page_num = st.number_input("Page", min_value=1, value=1, step=1, key="patient_page_num")

        skip = (page_num - 1) * page_size

        with st.spinner("Loading patient records..."):
            res = client.get_patients(skip=skip, limit=page_size, search=search_query if search_query else None)

        if not res["success"]:
            st.error(f"Error loading patients: {res['error']}")
        else:
            data = res["data"] or {}
            items = data.get("items", [])
            total = data.get("total", 0)

            st.write(f"Showing **{len(items)}** of **{total}** registered patients (Page {page_num})")

            if items:
                df = pd.DataFrame(items)
                cols_to_show = ["patient_id", "first_name", "last_name", "dob", "gender", "blood_group", "contact_phone", "emergency_contact"]
                available_cols = [c for c in cols_to_show if c in df.columns]
                
                st.dataframe(
                    df[available_cols],
                    column_config={
                        "patient_id": "Patient ID",
                        "first_name": "First Name",
                        "last_name": "Last Name",
                        "dob": "Date of Birth",
                        "gender": "Gender",
                        "blood_group": "Blood Group",
                        "contact_phone": "Phone",
                        "emergency_contact": "Emergency Contact"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No patients found matching the criteria.")

    # =========================================================================
    # TAB 2: Patient Profile & Care History
    # =========================================================================
    with tab_detail:
        st.markdown("#### Patient Longitudinal Care Profile")
        target_pid = st.text_input(
            "Enter Patient ID to inspect",
            placeholder="e.g., P1001",
            key="inspect_patient_id"
        )

        if target_pid:
            with st.spinner(f"Retrieving profile for {target_pid}..."):
                p_res = client.get_patient(target_pid.strip())
                h_res = client.get_patient_history(target_pid.strip())

            if not p_res["success"]:
                st.warning(f"Patient not found: {p_res['error']}")
            else:
                pdata = p_res["data"]
                st.success(f"Loaded: **{pdata.get('first_name')} {pdata.get('last_name')}** ({pdata.get('patient_id')})")

                # Demographic summary
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Date of Birth", pdata.get("dob", "N/A"))
                m2.metric("Gender", pdata.get("gender", "N/A"))
                m3.metric("Blood Group", pdata.get("blood_group", "N/A"))
                m4.metric("Phone", pdata.get("contact_phone", "N/A"))

                with st.expander("📝 Edit Patient Demographics", expanded=False):
                    with st.form(f"edit_patient_{target_pid}"):
                        edit_fn = st.text_input("First Name", value=pdata.get("first_name", ""))
                        edit_ln = st.text_input("Last Name", value=pdata.get("last_name", ""))
                        edit_phone = st.text_input("Contact Phone", value=pdata.get("contact_phone") or "")
                        edit_em = st.text_input("Emergency Contact", value=pdata.get("emergency_contact") or "")
                        edit_bg = st.selectbox(
                            "Blood Group",
                            ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
                            index=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].index(pdata.get("blood_group", "O+"))
                            if pdata.get("blood_group") in ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] else 6
                        )
                        btn_update = st.form_submit_button("💾 Save Changes")

                        if btn_update:
                            up_payload = {
                                "first_name": edit_fn.strip(),
                                "last_name": edit_ln.strip(),
                                "contact_phone": edit_phone.strip() if edit_phone else None,
                                "emergency_contact": edit_em.strip() if edit_em else None,
                                "blood_group": edit_bg
                            }
                            up_res = client.update_patient(target_pid.strip(), up_payload)
                            if up_res["success"]:
                                st.success("Patient record successfully updated!")
                                st.rerun()
                            else:
                                st.error(f"Update failed: {up_res['error']}")

                # Encounters History
                st.markdown("##### Clinical Encounter History")
                if h_res["success"] and h_res["data"]:
                    hdata = h_res["data"]
                    encounters = hdata.get("encounters", [])
                    if encounters:
                        st.write(f"Total recorded visits: **{len(encounters)}**")
                        for enc in encounters:
                            enc_id = enc.get("encounter_id", "ENC")
                            enc_status = enc.get("status", "Active")
                            status_badge = "🟢 Active" if enc_status == "Active" else ("🔵 Discharged" if enc_status == "Discharged" else f"⚪ {enc_status}")

                            with st.expander(f"Visit: {enc.get('encounter_type')} — {enc.get('reason_for_visit')} ({status_badge})"):
                                c_a, c_b = st.columns(2)
                                with c_a:
                                    st.write(f"**Encounter ID:** `{enc_id}`")
                                    st.write(f"**Attending Doctor:** {enc.get('doctor_name', 'N/A')}")
                                    st.write(f"**Start Time:** {enc.get('start_time', 'N/A')}")
                                    st.write(f"**End Time:** {enc.get('end_time', 'Ongoing' if enc_status == 'Active' else 'N/A')}")
                                with c_b:
                                    st.write(f"**Department:** {enc.get('department_name', 'N/A')}")
                                    st.write(f"**Room Allocated:** {enc.get('room_number', 'Outpatient / N/A')}")
                                    diags = enc.get("diagnoses", [])
                                    if diags:
                                        st.write(f"**Diagnoses:** {', '.join([d.get('description', '') for d in diags if isinstance(d, dict)])}")
                                    else:
                                        st.write("**Diagnoses:** None recorded")

                                # Embedded Clinical Document
                                clin_rec = enc.get("clinical_record")
                                if clin_rec and isinstance(clin_rec, dict):
                                    st.markdown("###### Document-Style Clinical Record (Semi-Structured JSON)")
                                    vitals = clin_rec.get("vital_signs")
                                    if vitals:
                                        bp = vitals.get("blood_pressure", {})
                                        st.caption(
                                            f"🌡️ Temp: {vitals.get('temperature_celsius')}°C | "
                                            f"❤️ Heart Rate: {vitals.get('heart_rate_bpm')} bpm | "
                                            f"🩺 BP: {bp.get('systolic_mmhg')}/{bp.get('diastolic_mmhg')} mmHg | "
                                            f"🫁 SpO2: {vitals.get('oxygen_saturation_percent')}%"
                                        )
                                    notes = clin_rec.get("clinical_notes")
                                    if notes:
                                        st.info(f"**Assessment & Plan:** {notes.get('assessment_and_plan', 'None')}")
                    else:
                        st.info("No past clinical encounters on file for this patient.")
                else:
                    st.info("Encounter history is empty or unlinked.")

                # Safe Deletion Section
                st.markdown("---")
                with st.expander("⚠️ Danger Zone: Delete Patient Record", expanded=False):
                    st.warning("Hospital safety rules prevent deleting patients with active admissions or ongoing care history.")
                    confirm_del = st.checkbox(f"Confirm intent to delete patient record `{target_pid.strip()}`", key="chk_del_patient")
                    if st.button("🗑️ Delete Patient Record", type="primary", disabled=not confirm_del):
                        del_res = client.delete_patient(target_pid.strip())
                        if del_res["success"]:
                            st.success(f"Patient {target_pid} was deleted successfully.")
                            st.rerun()
                        else:
                            st.error(f"Cannot delete patient: {del_res['error']}")

    # =========================================================================
    # TAB 3: Register New Patient
    # =========================================================================
    with tab_create:
        st.markdown("#### Patient Onboarding & Identity Registration")
        st.caption("Fictional synthetic persona registration adhering to ISO-8601 formatting.")

        with st.form("form_create_patient", clear_on_submit=True):
            col_id, col_fn, col_ln = st.columns(3)
            with col_id:
                new_pid = st.text_input("Patient ID (Optional)", placeholder="e.g. P1021 (auto if empty)")
            with col_fn:
                new_fn = st.text_input("First Name *", placeholder="Alice")
            with col_ln:
                new_ln = st.text_input("Last Name *", placeholder="Wong")

            col_dob, col_gen, col_bg = st.columns(3)
            with col_dob:
                new_dob = st.text_input("Date of Birth (YYYY-MM-DD) *", placeholder="1992-04-12")
            with col_gen:
                new_gen = st.selectbox("Gender *", ["Female", "Male", "Other"])
            with col_bg:
                new_bg = st.selectbox("Blood Group *", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])

            col_ph, col_em = st.columns(2)
            with col_ph:
                new_phone = st.text_input("Contact Phone", placeholder="+1-555-0144")
            with col_em:
                new_em = st.text_input("Emergency Contact *", placeholder="Bob Wong (+1-555-0145)")

            submit_patient = st.form_submit_button("✨ Register Patient")

            if submit_patient:
                fn_clean = new_fn.strip()
                ln_clean = new_ln.strip()
                dob_clean = new_dob.strip()
                em_clean = new_em.strip()
                ph_clean = new_phone.strip()

                if len(fn_clean) < 2 or fn_clean.isdigit() or not any(c.isalpha() for c in fn_clean):
                    st.error("Validation Error: First Name must contain at least 2 characters and cannot be numeric-only.")
                elif len(ln_clean) < 2 or ln_clean.isdigit() or not any(c.isalpha() for c in ln_clean):
                    st.error("Validation Error: Last Name must contain at least 2 characters and cannot be numeric-only.")
                elif not dob_clean:
                    st.error("Validation Error: Date of birth (YYYY-MM-DD) is required.")
                elif len(em_clean) < 2 or not any(c.isalpha() for c in em_clean):
                    st.error("Validation Error: A meaningful Emergency Contact name is required.")
                else:
                    payload = {
                        "first_name": fn_clean,
                        "last_name": ln_clean,
                        "dob": dob_clean,
                        "gender": new_gen,
                        "blood_group": new_bg,
                        "contact_phone": ph_clean if ph_clean else None,
                        "emergency_contact": em_clean
                    }
                    if new_pid.strip():
                        payload["patient_id"] = new_pid.strip()

                    with st.spinner("Submitting patient registration to backend..."):
                        c_res = client.create_patient(payload)

                    if c_res["success"]:
                        st.success(f"Patient created successfully! Patient ID: `{c_res['data'].get('patient_id')}`")
                    else:
                        st.error(f"Registration failed: {c_res['error']}")
