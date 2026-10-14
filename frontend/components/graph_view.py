"""
Graph Explorer View Component
=============================
Interactive graph visualization of clinical relationships, patient pathways,
and simulated co-occupancy contact tracing using NetworkX and Plotly.
"""

import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from typing import Optional, Dict, Any, List
from frontend.api_client import HospitalAPIClient


def build_plotly_graph(G: nx.Graph, title: str) -> go.Figure:
    """Renders a NetworkX graph using Plotly 2D scatter with spring layout."""
    if len(G.nodes) == 0:
        fig = go.Figure()
        fig.update_layout(
            title="No graph nodes available",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8"
        )
        return fig

    # Compute 2D spring layout
    pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)

    # Build Edges trace
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1.5, color="#64748B"),
        hoverinfo="none",
        mode="lines"
    )

    # Build Nodes trace
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []

    color_map = {
        "Patient": "#14B8A6",     # Teal
        "Encounter": "#3B82F6",   # Blue
        "Doctor": "#8B5CF6",      # Purple
        "Department": "#F97316",  # Orange
        "Room": "#10B981",        # Emerald
        "Diagnosis": "#EF4444",   # Crimson
        "Other": "#94A3B8"        # Slate
    }

    size_map = {
        "Patient": 24,
        "Encounter": 18,
        "Doctor": 22,
        "Department": 26,
        "Room": 20,
        "Diagnosis": 16,
        "Other": 14
    }

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        data = G.nodes[node]
        ntype = data.get("type", "Other")
        label = data.get("label", str(node))
        details = data.get("details", "")

        node_color.append(color_map.get(ntype, "#94A3B8"))
        node_size.append(size_map.get(ntype, 16))
        node_text.append(f"<b>[{ntype}] {label}</b><br>{details}")

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        hoverinfo="text",
        text=[G.nodes[n].get("short_label", "") for n in G.nodes()],
        textposition="top center",
        textfont=dict(size=10, color="#E2E8F0"),
        hovertext=node_text,
        marker=dict(
            showscale=False,
            color=node_color,
            size=node_size,
            line=dict(width=2, color="#0F172A")
        )
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=title,
            titlefont=dict(size=16, color="#F8FAFC"),
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=20, r=20, t=50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor="rgba(15, 23, 42, 0.6)",
            plot_bgcolor="rgba(15, 23, 42, 0.6)"
        )
    )
    return fig


def render_graph_explorer(client: HospitalAPIClient):
    st.subheader("🕸️ Graph Relationship Explorer")
    st.caption("Native Neo4j graph topology, multi-hop traversals, and clinical care trajectories.")

    # Legend summary
    st.markdown(
        "<div style='display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 12px; font-size: 13px;'>"
        "<span>🟢 <b>Patient</b> (#14B8A6)</span>"
        "<span>🔵 <b>Encounter</b> (#3B82F6)</span>"
        "<span>🟣 <b>Doctor</b> (#8B5CF6)</span>"
        "<span>🟠 <b>Department</b> (#F97316)</span>"
        "<span>🟢 <b>Room</b> (#10B981)</span>"
        "<span>🔴 <b>Diagnosis</b> (#EF4444)</span>"
        "</div>",
        unsafe_allow_html=True
    )

    mode = st.radio(
        "Choose Graph Exploration Mode",
        ["Patient Care Pathways", "Simulated Room-Sharing & Contact Tracing"],
        horizontal=True,
        key="graph_mode_radio"
    )

    # =========================================================================
    # MODE 1: Patient Care Pathways
    # =========================================================================
    if mode == "Patient Care Pathways":
        st.markdown("#### Longitudinal Patient Care Pathway Graph")
        st.caption("Traces Patient -> Encounter -> Doctor / Department / Room / Diagnoses relationships.")

        col_p1, col_p2 = st.columns([3, 1])
        with col_p1:
            sel_pid = st.text_input("Filter by Patient ID (Leave blank to explore all hospital pathways)", placeholder="e.g. P1001", key="graph_pathway_pid")
        with col_p2:
            st.write("")
            st.write("")
            btn_refresh = st.button("🔄 Refresh Graph")

        with st.spinner("Extracting graph paths from Neo4j..."):
            res = client.get_treatment_pathways(patient_id=sel_pid.strip() if sel_pid.strip() else None)

        if not res["success"]:
            st.error(f"Error fetching pathway graph: {res['error']}")
            return

        pathways = (res["data"] or {}).get("pathways", [])
        if not pathways:
            st.info("No treatment pathways found matching the selection. Ensure data has been seeded.")
            return

        # Build NetworkX graph from real relationships
        G = nx.Graph()

        for item in pathways:
            pid = item.get("patient_id")
            pname = item.get("patient_name") or pid
            eid = item.get("encounter_id")
            doc = item.get("physician")
            dept = item.get("department")
            room = item.get("room_number")
            diags = item.get("diagnoses") or []

            # 1. Patient Node
            if pid:
                G.add_node(pid, type="Patient", label=f"Patient: {pname}", short_label=pid, details=f"Name: {pname}")

            # 2. Encounter Node
            if eid:
                enc_details = f"Type: {item.get('encounter_type')} | Reason: {item.get('reason_for_visit')} | Status: {item.get('status')}"
                G.add_node(eid, type="Encounter", label=f"Encounter: {eid}", short_label=eid, details=enc_details)
                if pid:
                    G.add_edge(pid, eid, rel="HAS_ENCOUNTER")

            # 3. Doctor Node
            if doc and eid:
                doc_node = f"DOC_{doc}"
                G.add_node(doc_node, type="Doctor", label=f"Dr. {doc}", short_label=doc.split()[-1], details=f"Physician: Dr. {doc}")
                G.add_edge(eid, doc_node, rel="ATTENDED_BY")

                # 4. Department Node
                if dept:
                    dept_node = f"DEPT_{dept}"
                    G.add_node(dept_node, type="Department", label=f"Dept: {dept}", short_label=dept[:6], details=f"Department: {dept}")
                    G.add_edge(doc_node, dept_node, rel="BELONGS_TO")

            # 5. Room Node
            if room and eid:
                room_node = f"ROOM_{room}"
                G.add_node(room_node, type="Room", label=f"Room {room}", short_label=f"Rm {room}", details=f"Inpatient Room: {room}")
                G.add_edge(eid, room_node, rel="ADMITTED_TO")

            # 6. Diagnosis Nodes
            for d in diags:
                if d and eid:
                    d_node = f"DIAG_{d}"
                    G.add_node(d_node, type="Diagnosis", label=d, short_label=d[:8], details=f"Diagnosis: {d}")
                    G.add_edge(eid, d_node, rel="DIAGNOSED_WITH")

        st.write(f"Rendered Graph Topology: **{G.number_of_nodes()}** Nodes, **{G.number_of_edges()}** Relationships")
        fig = build_plotly_graph(G, "Hospital Care Pathways Network")
        st.plotly_chart(fig, use_container_width=True)

        # Tabular breakdown
        with st.expander("📊 View Raw Pathway Traversal Data", expanded=False):
            df = pd.DataFrame(pathways)
            st.dataframe(df, use_container_width=True)

    # =========================================================================
    # MODE 2: Simulated Room-Sharing & Contact Tracing
    # =========================================================================
    else:
        st.markdown("#### Simulated Room-Sharing & Epidemiological Contact Graph")
        
        # MANDATORY CLINICAL & EDUCATIONAL DISCLAIMER
        st.warning(
            "⚠️ **SIMULATED CONTACT ANALYSIS DISCLAIMER**: "
            "Temporal room overlap indicates potential epidemiological exposure proximity based on co-occupancy timestamps. "
            "This analysis is strictly illustrative for academic modeling and is NOT clinical proof of pathogen transmission or infection."
        )

        col_r1, col_r2 = st.columns([3, 1])
        with col_r1:
            sel_rm = st.text_input("Filter by Room ID (Leave blank for all rooms)", placeholder="e.g. RM-ICU-301", key="graph_contact_rm")
        with col_r2:
            st.write("")
            st.write("")
            btn_contact_ref = st.button("🔄 Refresh Contacts")

        with st.spinner("Analyzing co-occupancy graph intervals in Neo4j..."):
            c_res = client.get_room_sharing(room_id=sel_rm.strip() if sel_rm.strip() else None)

        if not c_res["success"]:
            st.error(f"Error fetching room sharing contacts: {c_res['error']}")
            return

        c_data = c_res["data"] or {}
        contacts = c_data.get("overlapping_encounters", [])

        if not contacts:
            st.info("No overlapping inpatient room occupancies detected in the current dataset.")
            return

        st.write(f"Detected Overlapping Cohort Pairs: **{len(contacts)}**")

        # Build Contact Tracing Graph
        G_contact = nx.Graph()

        for c in contacts:
            r_id = c.get("room_id")
            r_num = c.get("room_number") or r_id
            p1_id = c.get("patient_1_id")
            p1_name = c.get("patient_1_name") or p1_id
            p2_id = c.get("patient_2_id")
            p2_name = c.get("patient_2_name") or p2_id
            p1_admit = c.get("patient_1_admit", "")
            p2_admit = c.get("patient_2_admit", "")

            # Room node
            r_node = f"RM_{r_num}"
            G_contact.add_node(
                r_node,
                type="Room",
                label=f"Room {r_num} ({c.get('room_type', 'Ward')})",
                short_label=f"Rm {r_num}",
                details=f"Location: Room {r_num}"
            )

            # Patient 1
            if p1_id:
                G_contact.add_node(
                    p1_id,
                    type="Patient",
                    label=f"Patient: {p1_name}",
                    short_label=p1_id,
                    details=f"Name: {p1_name} | Admitted: {p1_admit}"
                )
                G_contact.add_edge(p1_id, r_node, rel="STAYED_IN")

            # Patient 2
            if p2_id:
                G_contact.add_node(
                    p2_id,
                    type="Patient",
                    label=f"Patient: {p2_name}",
                    short_label=p2_id,
                    details=f"Name: {p2_name} | Admitted: {p2_admit}"
                )
                G_contact.add_edge(p2_id, r_node, rel="STAYED_IN")

            # Direct contact edge
            if p1_id and p2_id:
                G_contact.add_edge(p1_id, p2_id, rel="CO_OCCUPANT")

        fig_contact = build_plotly_graph(G_contact, "Simulated Room Co-Occupancy Network")
        st.plotly_chart(fig_contact, use_container_width=True)

        # Tabular details
        with st.expander("📋 View Overlapping Admission Details", expanded=True):
            df_c = pd.DataFrame(contacts)
            cols = ["room_number", "room_type", "patient_1_name", "patient_1_admit", "patient_1_discharge", "patient_2_name", "patient_2_admit", "patient_2_discharge"]
            avail = [x for x in cols if x in df_c.columns]
            st.dataframe(
                df_c[avail],
                column_config={
                    "room_number": "Room",
                    "room_type": "Acuity",
                    "patient_1_name": "Patient 1",
                    "patient_1_admit": "P1 Admit",
                    "patient_1_discharge": "P1 Discharge",
                    "patient_2_name": "Patient 2",
                    "patient_2_admit": "P2 Admit",
                    "patient_2_discharge": "P2 Discharge"
                },
                use_container_width=True,
                hide_index=True
            )
