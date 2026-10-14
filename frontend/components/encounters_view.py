"""
Encounters & Clinical History View Component
============================================
Manages clinical admissions, outpatient visits, discharge tracking,
and document-style medical records (vital signs, clinical notes, lab tests).
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from frontend.api_client import HospitalAPIClient


def render_encounters(client: HospitalAPIClient):
    st.subheader("📋 Clinical Encounters & Medical Charting")
    st.caption("Hybrid Graph Admissions & Embedded Semi-Structured JSON Health Records.")

    tab_list, tab_detail, tab_create = st.tabs([
        "📑 Encounters Registry",
        "🩺 Clinical Chart & Vitals",
        "➕ New Encounter Admission"
    ])

    # =========================================================================
    # TAB 1: Encounters Registry
    # =========================================================================
    with tab_list:
        c_f1, c_f2, c_f3 = st.columns(3)
        with c_f1:
            filter_status = st.selectbox(
                "Filter Status",
                ["All", "Active", "Discharged", "Completed", "Transferred"],
                index=0,
                key="enc_filter_status"
            )
        with c_f2:
            filter_type = st.selectbox(
                "Filter Type",
                ["All", "Inpatient", "Outpatient", "Emergency"],
                index=0,
                key="enc_filter_type"
            )
        with c_f3:
            filter_pid = st.text_input("Filter by Patient ID", placeholder="e.g. P1001", key="enc_filter_pid")

        c_p1, c_p2 = st.columns([1, 1])
        with c_p1:
            page_size = st.selectbox("Page Size", [10, 25, 50], index=0, key="enc_page_size")
        with c_p2:
            page_num = st.number_input("Page", min_value=1, value=1, step=1, key="enc_page_num")

        skip = (page_num - 1) * page_size

        with st.spinner("Fetching encounters..."):
            res = client.get_encounters(
                skip=skip,
                limit=page_size,
                status=filter_status if filter_status != "All" else None,
                encounter_type=filter_type if filter_type != "All" else None,
                patient_id=filter_pid.strip() if filter_pid.strip() else None
            )

        if not res["success"]:
            st.error(f"Error fetching encounters: {res['error']}")
        else:
            data = res["data"] or {}
            items = data.get("items", [])
            total = data.get("total", 0)

            st.write(f"Showing **{len(items)}** of **{total}** recorded encounters (Page {page_num})")

            if items:
                df = pd.DataFrame(items)
                cols = ["encounter_id", "patient_name", "doctor_name", "encounter_type", "status", "room_number", "start_time", "reason_for_visit"]
                avail_cols = [c for c in cols if c in df.columns]

                st.dataframe(
                    df[avail_cols],
                    column_config={
                        "encounter_id": "Encounter ID",
                        "patient_name": "Patient",
                        "doctor_name": "Physician",
                        "encounter_type": "Type",
                        "status": "Status",
                        "room_number": "Room",
                        "start_time": "Admitted / Began",
                        "reason_for_visit": "Clinical Reason"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No encounters match the specified criteria.")

    # =========================================================================
    # TAB 2: Clinical Chart & Vitals Inspection
    # =========================================================================
    with tab_detail:
        st.markdown("#### Detailed Clinical Chart & Discharge Management")
        target_eid = st.text_input("Enter Encounter ID to Inspect", placeholder="e.g. ENC5001", key="inspect_eid")

        if target_eid:
            with st.spinner(f"Loading chart for {target_eid}..."):
                e_res = client.get_encounter(target_eid.strip())

            if not e_res["success"]:
                st.warning(f"Encounter not found: {e_res['error']}")
            else:
                edata = e_res["data"]
                st.success(f"Encounter: **{edata.get('encounter_id')}** — {edata.get('patient_name')} ({edata.get('patient_id')})")

                # Key Header Info
                h1, h2, h3, h4 = st.columns(4)
                h1.metric("Encounter Type", edata.get("encounter_type", "N/A"))
                h2.metric("Current Status", edata.get("status", "N/A"))
                h3.metric("Physician", edata.get("doctor_name", "N/A"))
                h4.metric("Room", edata.get("room_number") or "Outpatient")

                st.write(f"**Reason for Visit:** {edata.get('reason_for_visit')}")
                st.caption(f"Start: `{edata.get('start_time')}` | End: `{edata.get('end_time') or 'Active'}`")

                st.markdown("---")
                # Diagnoses & Prescriptions
                col_d, col_p = st.columns(2)
                with col_d:
                    st.markdown("##### 🩺 Diagnoses (Graph Relationships)")
                    diags = edata.get("diagnoses", [])
                    if diags:
                        for d in diags:
                            st.markdown(f"- **{d.get('name', 'Diagnosis')}** (`{d.get('code', 'ICD')}`) — Status: *{d.get('status', 'Confirmed')}*")
                    else:
                        st.info("No formal diagnosis attached.")

                with col_p:
                    st.markdown("##### 💊 Prescribed Medications")
                    meds = edata.get("prescriptions", [])
                    if meds:
                        for m in meds:
                            st.markdown(f"- **{m.get('name')}** | Dose: {m.get('dosage')} | Freq: {m.get('frequency')}")
                    else:
                        st.info("No medications prescribed.")

                # Embedded JSON Clinical Record
                st.markdown("---")
                st.markdown("##### 🧬 Embedded Document-Style Clinical Record (NoSQL JSON)")
                clin_rec = edata.get("clinical_record")
                if clin_rec and isinstance(clin_rec, dict):
                    # Vital Signs
                    vitals = clin_rec.get("vital_signs")
                    if vitals:
                        st.markdown("**Vital Signs Observation:**")
                        bp = vitals.get("blood_pressure") or {}
                        vc1, vc2, vc3, vc4 = st.columns(4)
                        vc1.metric("Body Temp", f"{vitals.get('temperature_celsius', 'N/A')} °C")
                        vc2.metric("Heart Rate", f"{vitals.get('heart_rate_bpm', 'N/A')} bpm")
                        vc3.metric("Blood Pressure", f"{bp.get('systolic_mmhg', '-')}/{bp.get('diastolic_mmhg', '-')} mmHg")
                        vc4.metric("SpO2", f"{vitals.get('oxygen_saturation_percent', 'N/A')}%")

                    # Clinical Notes
                    notes = clin_rec.get("clinical_notes")
                    if notes:
                        st.markdown("**Physician Clinical Notes:**")
                        st.markdown(f"**Chief Complaint:** {notes.get('chief_complaint', 'N/A')}")
                        st.markdown(f"**Assessment & Plan:** {notes.get('assessment_and_plan', 'N/A')}")
                        if notes.get("discharge_summary"):
                            st.info(f"**Discharge Summary:** {notes.get('discharge_summary')}")

                    # Test Results
                    tests = clin_rec.get("test_results", [])
                    if tests:
                        st.markdown("**Laboratory / Diagnostic Panels:**")
                        df_tests = pd.DataFrame(tests)
                        st.dataframe(df_tests, use_container_width=True, hide_index=True)

                    # Treatment Summary
                    treatment = clin_rec.get("treatment_summary")
                    if treatment:
                        st.markdown("**Treatment & Nursing Plan:**")
                        procs = treatment.get("procedures_performed", [])
                        if procs:
                            st.write(f"- **Procedures:** {', '.join(procs)}")
                        care = treatment.get("nursing_care_plan")
                        if care:
                            st.write(f"- **Care Plan:** {care}")
                else:
                    st.info("No embedded semi-structured clinical document present on this encounter.")

                # Discharge / Status Update Action Form
                st.markdown("---")
                with st.expander("📝 Update Encounter Status / Discharge Patient", expanded=False):
                    with st.form(f"form_discharge_{target_eid}"):
                        new_status = st.selectbox(
                            "Update Status",
                            ["Active", "Discharged", "Completed", "Transferred"],
                            index=["Active", "Discharged", "Completed", "Transferred"].index(edata.get("status", "Active"))
                            if edata.get("status") in ["Active", "Discharged", "Completed", "Transferred"] else 0
                        )
                        discharge_ts = st.text_input(
                            "Discharge / End Timestamp (ISO-8601)",
                            value=datetime.now(timezone.utc).isoformat() if new_status == "Discharged" and not edata.get("end_time") else (edata.get("end_time") or "")
                        )
                        discharge_note = st.text_area("Discharge Summary / Clinical Note Update", placeholder="Patient stable, instructed on medication compliance...")
                        btn_update_enc = st.form_submit_button("💾 Commit Status Update")

                        if btn_update_enc:
                            up_payload = {
                                "status": new_status,
                                "end_time": discharge_ts.strip() if discharge_ts.strip() else None
                            }
                            # If discharge note provided, update clinical record
                            if discharge_note.strip():
                                current_cr = clin_rec if (clin_rec and isinstance(clin_rec, dict)) else {}
                                c_notes = current_cr.get("clinical_notes") or {}
                                c_notes["discharge_summary"] = discharge_note.strip()
                                current_cr["clinical_notes"] = c_notes
                                up_payload["clinical_record"] = current_cr

                            up_res = client.update_encounter(target_eid.strip(), up_payload)
                            if up_res["success"]:
                                st.success("Encounter updated successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to update encounter: {up_res['error']}")

    # =========================================================================
    # TAB 3: New Encounter Admission
    # =========================================================================
    with tab_create:
        st.markdown("#### Log New Encounter / Inpatient Admission")
        st.caption("Creates an encounter node, establishes graph edges, and attaches initial document-style charting.")

        with st.form("form_create_encounter", clear_on_submit=True):
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                in_eid = st.text_input("Encounter ID (Optional)", placeholder="e.g. ENC5036 (auto if blank)")
                in_pid = st.text_input("Patient ID *", placeholder="e.g. P1001")
            with ec2:
                in_did = st.text_input("Doctor ID *", placeholder="e.g. DOC201")
                in_type = st.selectbox("Encounter Type *", ["Inpatient", "Outpatient", "Emergency"])
            with ec3:
                in_room = st.text_input("Room ID (Required for Inpatient)", placeholder="e.g. RM101")
                in_status = st.selectbox("Initial Status *", ["Active", "Completed"])

            in_reason = st.text_input("Reason for Visit *", placeholder="Acute respiratory distress / Routine cardiology checkup")

            st.markdown("##### Clinical Assessment & Vital Signs")
            vc1, vc2, vc3, vc4, vc5 = st.columns(5)
            with vc1:
                v_temp = st.number_input("Temp (°C)", min_value=32.0, max_value=44.0, value=37.0, step=0.1)
            with vc2:
                v_hr = st.number_input("Heart Rate (bpm)", min_value=30, max_value=250, value=75)
            with vc3:
                v_sys = st.number_input("Systolic BP", min_value=50, max_value=280, value=120)
            with vc4:
                v_dia = st.number_input("Diastolic BP", min_value=30, max_value=180, value=80)
            with vc5:
                v_spo2 = st.number_input("SpO2 (%)", min_value=50, max_value=100, value=98)

            c_plan = st.text_area("Physician Assessment & Plan", placeholder="Initial triage: administer IV fluids, request chest X-ray and full blood count.")

            st.markdown("##### Primary Diagnosis Linkage (Optional)")
            dc1, dc2 = st.columns(2)
            with dc1:
                diag_name = st.text_input("Diagnosis Name", placeholder="e.g. Essential Hypertension")
            with dc2:
                diag_icd = st.text_input("ICD-10 Code", placeholder="e.g. I10")

            btn_submit_enc = st.form_submit_button("✨ Log Clinical Encounter")

            if btn_submit_enc:
                if not in_pid.strip() or not in_did.strip() or not in_reason.strip():
                    st.error("Validation Error: Patient ID, Doctor ID, and Reason for Visit are required.")
                elif in_type == "Inpatient" and not in_room.strip():
                    st.error("Validation Error: Inpatient encounters require an allocated Room ID.")
                else:
                    now_str = datetime.now(timezone.utc).isoformat()
                    payload = {
                        "patient_id": in_pid.strip(),
                        "doctor_id": in_did.strip(),
                        "encounter_type": in_type,
                        "status": in_status,
                        "start_time": now_str,
                        "reason_for_visit": in_reason.strip(),
                        "room_id": in_room.strip() if in_room.strip() else None,
                        "primary_diagnosis": diag_name.strip() if diag_name.strip() else None,
                        "primary_icd10": diag_icd.strip() if diag_icd.strip() else None,
                        "clinical_record": {
                            "vital_signs": {
                                "temperature_celsius": float(v_temp),
                                "heart_rate_bpm": int(v_hr),
                                "blood_pressure": {
                                    "systolic_mmhg": int(v_sys),
                                    "diastolic_mmhg": int(v_dia)
                                },
                                "respiratory_rate_bpm": 16,
                                "oxygen_saturation_percent": int(v_spo2),
                                "recorded_at": now_str
                            },
                            "clinical_notes": {
                                "chief_complaint": in_reason.strip(),
                                "assessment_and_plan": c_plan.strip() if c_plan.strip() else "Under clinical evaluation."
                            }
                        }
                    }
                    if in_eid.strip():
                        payload["encounter_id"] = in_eid.strip()

                    with st.spinner("Submitting encounter admission to backend..."):
                        c_res = client.create_encounter(payload)

                    if c_res["success"]:
                        st.success(f"Encounter recorded successfully! Encounter ID: `{c_res['data'].get('encounter_id')}`")
                    else:
                        st.error(f"Encounter registration failed: {c_res['error']}")
