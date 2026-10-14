"""
Doctors & Departments View Component
====================================
Physician registry, department staffing analysis, and caseload tracking.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from frontend.api_client import HospitalAPIClient


def render_doctors(client: HospitalAPIClient):
    st.subheader("👨‍⚕️ Medical Staff & Clinical Departments")
    st.caption("Physician credentials, specialty divisions, and department caseload allocations.")

    tab_docs, tab_depts, tab_workload, tab_create = st.tabs([
        "🩺 Physician Directory",
        "🏢 Department Overview",
        "📊 Workload & Staffing Analytics",
        "➕ Add New Physician"
    ])

    # =========================================================================
    # TAB 1: Physician Directory
    # =========================================================================
    with tab_docs:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_spec = st.text_input("Filter by Specialty", placeholder="e.g. Cardiology, Neurology...", key="doc_filter_spec")
        with col_f2:
            dept_res = client.get_departments()
            dept_options = {"All Departments": None}
            if dept_res["success"] and dept_res["data"]:
                for d in dept_res["data"].get("items", []):
                    dept_options[f"{d.get('name')} ({d.get('department_id')})"] = d.get("department_id")
            selected_dept_label = st.selectbox("Filter by Department", list(dept_options.keys()), key="doc_filter_dept")
            selected_dept_id = dept_options[selected_dept_label]

        with st.spinner("Fetching doctors..."):
            doc_res = client.get_doctors(
                specialty=filter_spec.strip() if filter_spec.strip() else None,
                department_id=selected_dept_id
            )

        if not doc_res["success"]:
            st.error(f"Error fetching doctors: {doc_res['error']}")
        else:
            items = (doc_res["data"] or {}).get("items", [])
            st.write(f"Total Doctors Listed: **{len(items)}**")

            if items:
                df = pd.DataFrame(items)
                cols_to_show = ["doctor_id", "first_name", "last_name", "specialty", "license_number", "department_name", "years_of_experience", "email"]
                available_cols = [c for c in cols_to_show if c in df.columns]

                st.dataframe(
                    df[available_cols],
                    column_config={
                        "doctor_id": "Doctor ID",
                        "first_name": "First Name",
                        "last_name": "Last Name",
                        "specialty": "Specialty",
                        "license_number": "License #",
                        "department_name": "Department",
                        "years_of_experience": "Years Exp.",
                        "email": "Email"
                    },
                    use_container_width=True,
                    hide_index=True
                )

                st.markdown("---")
                st.markdown("##### 📝 Edit Physician Profile")
                doc_to_edit_id = st.selectbox(
                    "Select Doctor to update",
                    [f"{d.get('doctor_id')} - Dr. {d.get('first_name')} {d.get('last_name')}" for d in items],
                    key="select_doc_edit"
                )
                if doc_to_edit_id:
                    sel_id = doc_to_edit_id.split(" - ")[0]
                    curr_doc = next((d for d in items if d.get("doctor_id") == sel_id), None)
                    if curr_doc:
                        with st.form(f"form_edit_doctor_{sel_id}"):
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                e_spec = st.text_input("Specialty", value=curr_doc.get("specialty", ""))
                                e_exp = st.number_input("Years of Experience", min_value=0, max_value=60, value=int(curr_doc.get("years_of_experience") or 0))
                            with ec2:
                                e_email = st.text_input("Email", value=curr_doc.get("email") or "")
                                e_phone = st.text_input("Phone", value=curr_doc.get("phone") or "")

                            btn_save_doc = st.form_submit_button("💾 Save Doctor Updates")
                            if btn_save_doc:
                                up_payload = {
                                    "specialty": e_spec.strip(),
                                    "years_of_experience": int(e_exp),
                                    "email": e_email.strip() if e_email else None,
                                    "phone": e_phone.strip() if e_phone else None
                                }
                                up_doc_res = client.update_doctor(sel_id, up_payload)
                                if up_doc_res["success"]:
                                    st.success(f"Physician {sel_id} updated successfully.")
                                    st.rerun()
                                else:
                                    st.error(f"Update failed: {up_doc_res['error']}")
            else:
                st.info("No doctors found with the specified filters.")

    # =========================================================================
    # TAB 2: Department Overview
    # =========================================================================
    with tab_depts:
        st.markdown("#### Clinical Departments & Staffing Allocations")
        with st.spinner("Fetching departments..."):
            d_res = client.get_departments()

        if not d_res["success"]:
            st.error(f"Error loading departments: {d_res['error']}")
        else:
            depts = (d_res["data"] or {}).get("items", [])
            if depts:
                df_dept = pd.DataFrame(depts)
                st.dataframe(
                    df_dept[["department_id", "name", "building", "floor", "phone_extension", "doctor_count"]],
                    column_config={
                        "department_id": "Department ID",
                        "name": "Department Name",
                        "building": "Building Wing",
                        "floor": "Floor Level",
                        "phone_extension": "Phone Extension",
                        "doctor_count": "Assigned Doctors"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No departments found in the system.")

    # =========================================================================
    # TAB 3: Workload & Staffing Analytics
    # =========================================================================
    with tab_workload:
        st.markdown("#### Physician Caseloads and Encounter Volumes")
        col_w1, col_w2 = st.columns(2)

        with col_w1:
            with st.spinner("Calculating physician caseloads..."):
                wl_res = client.get_doctor_workload()
            if wl_res["success"] and wl_res["data"] and wl_res["data"].get("items"):
                items = wl_res["data"]["items"]
                df_wl = pd.DataFrame(items)
                fig_wl = px.bar(
                    df_wl,
                    x="doctor_name",
                    y="total_encounters",
                    color="department" if "department" in df_wl.columns else ("department_name" if "department_name" in df_wl.columns else None),
                    labels={"doctor_name": "Doctor", "total_encounters": "Total Encounters Handled"},
                    title="Encounters per Physician by Department",
                    text_auto=True
                )
                fig_wl.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC", xaxis_tickangle=-30)
                st.plotly_chart(fig_wl, use_container_width=True)
            else:
                st.info("No workload analytics available yet.")

        with col_w2:
            with st.spinner("Calculating department statistics..."):
                ds_res = client.get_department_statistics()
            if ds_res["success"] and ds_res["data"] and ds_res["data"].get("departments"):
                dstats = ds_res["data"]["departments"]
                df_ds = pd.DataFrame(dstats)
                doc_cnt_col = "total_physicians" if "total_physicians" in df_ds.columns else ("doctor_count" if "doctor_count" in df_ds.columns else None)
                fig_ds = px.bar(
                    df_ds,
                    x="department_name",
                    y="total_encounters",
                    color=doc_cnt_col,
                    labels={"department_name": "Department", "total_encounters": "Patient Encounters", (doc_cnt_col or "total_physicians"): "Staff Doctors"},
                    title="Total Encounters per Clinical Department",
                    text_auto=True
                )
                fig_ds.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC")
                st.plotly_chart(fig_ds, use_container_width=True)
            else:
                st.info("No department workload analytics available yet.")

    # =========================================================================
    # TAB 4: Add New Physician
    # =========================================================================
    with tab_create:
        st.markdown("#### Physician Credentialing & Onboarding")
        st.caption("Register a new doctor and link them directly to a clinical department in Neo4j.")

        with st.form("form_create_doctor", clear_on_submit=True):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                new_doc_id = st.text_input("Doctor ID (Optional)", placeholder="e.g. DOC209 (auto if empty)")
                new_doc_fn = st.text_input("First Name *", placeholder="Robert")
            with fc2:
                new_doc_ln = st.text_input("Last Name *", placeholder="Chen")
                new_doc_spec = st.text_input("Specialty *", placeholder="Cardiology")
            with fc3:
                new_doc_lic = st.text_input("License # *", placeholder="MD-CARD-9930")
                new_doc_exp = st.number_input("Years of Experience", min_value=0, max_value=60, value=8)

            fc4, fc5 = st.columns(2)
            with fc4:
                new_doc_email = st.text_input("Email", placeholder="r.chen@smarthospital.org")
                new_doc_phone = st.text_input("Phone", placeholder="+1-555-0219")
            with fc5:
                # Department select
                dept_map = {"(None)": None}
                d_list = client.get_departments()
                if d_list["success"] and d_list["data"]:
                    for dep in d_list["data"].get("items", []):
                        dept_map[f"{dep.get('name')} ({dep.get('department_id')})"] = dep.get("department_id")
                chosen_dept_label = st.selectbox("Department Affiliation", list(dept_map.keys()))
                chosen_dept_id = dept_map[chosen_dept_label]

            btn_submit_doc = st.form_submit_button("✨ Register Physician")

            if btn_submit_doc:
                if not new_doc_fn.strip() or not new_doc_ln.strip():
                    st.error("Validation Error: First Name and Last Name are required.")
                elif not new_doc_spec.strip() or not new_doc_lic.strip():
                    st.error("Validation Error: Specialty and License Number are required.")
                else:
                    payload = {
                        "first_name": new_doc_fn.strip(),
                        "last_name": new_doc_ln.strip(),
                        "specialty": new_doc_spec.strip(),
                        "license_number": new_doc_lic.strip(),
                        "years_of_experience": int(new_doc_exp),
                        "email": new_doc_email.strip() if new_doc_email.strip() else None,
                        "phone": new_doc_phone.strip() if new_doc_phone.strip() else None,
                        "department_id": chosen_dept_id
                    }
                    if new_doc_id.strip():
                        payload["doctor_id"] = new_doc_id.strip()

                    with st.spinner("Submitting physician onboarding to backend..."):
                        c_res = client.create_doctor(payload)

                    if c_res["success"]:
                        st.success(f"Doctor registered successfully! ID: `{c_res['data'].get('doctor_id')}`")
                    else:
                        st.error(f"Doctor registration failed: {c_res['error']}")
