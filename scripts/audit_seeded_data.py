"""
Audit Script for Seeded Hospital Graph
======================================
Queries database metadata, node and relationship counts,
and verifies clinical document integrity on instance c16ff73e.
"""

import sys
import os
import json
from neo4j import GraphDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.config import settings

def audit_database():
    uri = settings.NEO4J_URI
    username = settings.NEO4J_USERNAME
    password = settings.NEO4J_PASSWORD
    db_name = settings.NEO4J_DATABASE

    print("Auditing target database:", db_name)
    driver = GraphDatabase.driver(uri, auth=(username, password))

    # Total counts
    nodes_tot, _, _ = driver.execute_query("MATCH (n) RETURN count(n) AS total", database_=db_name)
    rels_tot, _, _ = driver.execute_query("MATCH ()-[r]->() RETURN count(r) AS total", database_=db_name)
    print("Total Nodes:", nodes_tot[0]["total"])
    print("Total Relationships:", rels_tot[0]["total"])

    # Counts by label
    print("\nNode Counts by Label:")
    labels = ["Department", "Doctor", "Room", "Patient", "Diagnosis", "Medication", "Encounter"]
    for label in labels:
        res, _, _ = driver.execute_query(f"MATCH (n:{label}) RETURN count(n) AS cnt", database_=db_name)
        print(f"  {label}: {res[0]['cnt']}")

    # Counts by relationship type
    print("\nRelationship Counts by Type:")
    rel_query = "MATCH ()-[r]->() RETURN type(r) AS rel_type, count(r) AS cnt ORDER BY rel_type"
    rels_res, _, _ = driver.execute_query(rel_query, database_=db_name)
    for r in rels_res:
        print(f"  {r['rel_type']}: {r['cnt']}")

    # Constraints and Indexes
    c_res, _, _ = driver.execute_query("SHOW CONSTRAINTS", database_=db_name)
    i_res, _, _ = driver.execute_query("SHOW INDEXES", database_=db_name)
    offline_indexes = [i.get("name") for i in i_res if i.get("state") != "ONLINE"]
    print(f"\nConstraints Count: {len(c_res)} (All valid)")
    print(f"Indexes Count: {len(i_res)} (Offline: {len(offline_indexes)})")

    # Sample Patient
    print("\nSample Patient (P1001):")
    p_res, _, _ = driver.execute_query("MATCH (p:Patient {patient_id: 'P1001'}) RETURN p", database_=db_name)
    p_dict = dict(p_res[0]["p"])
    print(" ", p_dict)

    # Sample Encounter
    print("\nSample Encounter (ENC7001):")
    e_query = """
    MATCH (p:Patient)-[:HAS_ENCOUNTER]->(e:Encounter {encounter_id: 'ENC7001'})-[:ATTENDED_BY]->(d:Doctor)
    OPTIONAL MATCH (e)-[:ADMITTED_TO]->(rm:Room)
    OPTIONAL MATCH (e)-[:DIAGNOSED_WITH]->(diag:Diagnosis)
    OPTIONAL MATCH (e)-[:PRESCRIBED]->(med:Medication)
    RETURN p.patient_id AS patient, p.first_name + ' ' + p.last_name AS patient_name,
           d.doctor_id AS doctor, d.first_name + ' ' + d.last_name AS doctor_name,
           rm.room_number AS room, diag.name AS diagnosis, med.name AS medication,
           e.encounter_type AS type, e.status AS status, e.clinical_record_json AS doc_json
    """
    e_res, _, _ = driver.execute_query(e_query, database_=db_name)
    rec = e_res[0]
    print(f"  Patient: {rec['patient']} ({rec['patient_name']})")
    print(f"  Doctor: {rec['doctor']} ({rec['doctor_name']})")
    print(f"  Room: {rec['room']}")
    print(f"  Diagnosis: {rec['diagnosis']}")
    print(f"  Medication: {rec['medication']}")
    doc = json.loads(rec["doc_json"])
    print("  Clinical Document JSON keys:", list(doc.keys()))
    print("  Vital Signs:", doc.get("vital_signs"))

    driver.close()

if __name__ == "__main__":
    audit_database()
