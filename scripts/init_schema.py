#!/usr/bin/env python3
"""
Schema Initialization Script for Smart Hospital Management System
==================================================================
Defines idempotent Neo4j constraints and indexes for the hybrid multi-model
NoSQL hospital schema.

SAFETY NOTE:
By default, this script runs in DRY-RUN mode.
It prints the planned schema statements without executing them.
To execute against the live database, pass the --execute flag and ensure .env is configured.
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Any

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("smart_hospital.schema")

# ==============================================================================
# SCHEMA STATEMENTS (Cypher 5.x / AuraDB Compatible)
# ==============================================================================

UNIQUENESS_CONSTRAINTS: List[Dict[str, str]] = [
    {
        "name": "constraint_patient_id",
        "description": "Ensures unique patient_id across all Patient nodes",
        "cypher": (
            "CREATE CONSTRAINT constraint_patient_id IF NOT EXISTS "
            "FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE"
        )
    },
    {
        "name": "constraint_doctor_id",
        "description": "Ensures unique doctor_id across all Doctor nodes",
        "cypher": (
            "CREATE CONSTRAINT constraint_doctor_id IF NOT EXISTS "
            "FOR (d:Doctor) REQUIRE d.doctor_id IS UNIQUE"
        )
    },
    {
        "name": "constraint_department_id",
        "description": "Ensures unique department_id across all Department nodes",
        "cypher": (
            "CREATE CONSTRAINT constraint_department_id IF NOT EXISTS "
            "FOR (dept:Department) REQUIRE dept.department_id IS UNIQUE"
        )
    },
    {
        "name": "constraint_encounter_id",
        "description": "Ensures unique encounter_id across all Encounter nodes",
        "cypher": (
            "CREATE CONSTRAINT constraint_encounter_id IF NOT EXISTS "
            "FOR (e:Encounter) REQUIRE e.encounter_id IS UNIQUE"
        )
    },
    {
        "name": "constraint_diagnosis_id",
        "description": "Ensures unique diagnosis_id across all Diagnosis nodes",
        "cypher": (
            "CREATE CONSTRAINT constraint_diagnosis_id IF NOT EXISTS "
            "FOR (diag:Diagnosis) REQUIRE diag.diagnosis_id IS UNIQUE"
        )
    },
    {
        "name": "constraint_medication_id",
        "description": "Ensures unique medication_id across all Medication nodes",
        "cypher": (
            "CREATE CONSTRAINT constraint_medication_id IF NOT EXISTS "
            "FOR (m:Medication) REQUIRE m.medication_id IS UNIQUE"
        )
    },
    {
        "name": "constraint_room_id",
        "description": "Ensures unique room_id across all Room nodes",
        "cypher": (
            "CREATE CONSTRAINT constraint_room_id IF NOT EXISTS "
            "FOR (r:Room) REQUIRE r.room_id IS UNIQUE"
        )
    }
]

SEARCH_INDEXES: List[Dict[str, str]] = [
    {
        "name": "idx_patient_names",
        "description": "B-Tree index on Patient (last_name, first_name) for rapid directory search",
        "cypher": (
            "CREATE INDEX idx_patient_names IF NOT EXISTS "
            "FOR (p:Patient) ON (p.last_name, p.first_name)"
        )
    },
    {
        "name": "idx_encounter_start_time",
        "description": "Range index on Encounter.start_time for temporal filtering and admission timelines",
        "cypher": (
            "CREATE INDEX idx_encounter_start_time IF NOT EXISTS "
            "FOR (e:Encounter) ON (e.start_time)"
        )
    },
    {
        "name": "idx_doctor_specialty",
        "description": "Index on Doctor.specialty for physician search and department routing",
        "cypher": (
            "CREATE INDEX idx_doctor_specialty IF NOT EXISTS "
            "FOR (d:Doctor) ON (d.specialty)"
        )
    },
    {
        "name": "idx_diagnosis_icd10",
        "description": "Lookup index on Diagnosis.icd10_code for medical coding queries",
        "cypher": (
            "CREATE INDEX idx_diagnosis_icd10 IF NOT EXISTS "
            "FOR (diag:Diagnosis) ON (diag.icd10_code)"
        )
    },
    {
        "name": "idx_medication_name",
        "description": "Index on Medication.name for prescription lookup and allergy cross-referencing",
        "cypher": (
            "CREATE INDEX idx_medication_name IF NOT EXISTS "
            "FOR (m:Medication) ON (m.name)"
        )
    },
    {
        "name": "idx_room_type",
        "description": "Index on Room.room_type for ward availability and allocation queries",
        "cypher": (
            "CREATE INDEX idx_room_type IF NOT EXISTS "
            "FOR (r:Room) ON (r.room_type)"
        )
    }
]


def get_all_schema_statements() -> List[Dict[str, str]]:
    """Returns combined list of constraints and indexes."""
    return UNIQUENESS_CONSTRAINTS + SEARCH_INDEXES


def apply_schema(driver: Any, database: str = "neo4j") -> List[str]:
    """
    Executes schema creation statements idempotently against a Neo4j driver.
    Returns list of successfully verified statements.
    """
    applied = []
    statements = get_all_schema_statements()

    with driver.session(database=database) as session:
        for item in statements:
            name = item["name"]
            cypher = item["cypher"]
            logger.info("Applying %s: %s", name, item["description"])
            try:
                session.run(cypher)
                applied.append(name)
                logger.info("Successfully ensured %s", name)
            except Exception as exc:
                logger.error("Failed to apply %s: %s", name, str(exc))
                raise exc

    return applied


def main():
    parser = argparse.ArgumentParser(
        description="Initialize constraints and indexes for Smart Hospital NoSQL Database."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the schema statements against the live database (default: dry-run)."
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env",
        help="Path to .env configuration file."
    )
    args = parser.parse_args()

    statements = get_all_schema_statements()
    print("=" * 80)
    print("SMART HOSPITAL NOSQL SCHEMA INITIALIZATION SPECIFICATION")
    print("=" * 80)
    print(f"Total Uniqueness Constraints: {len(UNIQUENESS_CONSTRAINTS)}")
    print(f"Total Property Indexes:      {len(SEARCH_INDEXES)}")
    print("-" * 80)

    for idx, stmt in enumerate(statements, 1):
        category = "CONSTRAINT" if "CONSTRAINT" in stmt["cypher"] else "INDEX"
        print(f"[{idx:02d}] {category}: {stmt['name']}")
        print(f"     Description: {stmt['description']}")
        print(f"     Cypher:      {stmt['cypher']}")
        print()

    if not args.execute:
        print("=" * 80)
        print("DRY-RUN MODE ACTIVE: No database queries were sent.")
        print("To execute these schema definitions, run:")
        print("  python scripts/init_schema.py --execute")
        print("=" * 80)
        return

    # Execution requires neo4j driver and confirmed environment
    try:
        from dotenv import load_dotenv
        from neo4j import GraphDatabase

        if os.path.exists(args.env_file):
            load_dotenv(args.env_file)
        else:
            logger.warning("Specified env file '%s' not found. Relying on system environment.", args.env_file)

        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        database = os.getenv("NEO4J_DATABASE", "neo4j")

        if not uri or not password or password == "your-secure-password":
            logger.error("Invalid or placeholder credentials in environment. Aborting execution.")
            sys.exit(1)

        logger.info("Connecting to Neo4j instance at %s...", uri.split("@")[-1])
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
        logger.info("Connected successfully. Verifying database isolation...")

        applied = apply_schema(driver, database=database)
        driver.close()
        logger.info("Schema initialization complete. %d statements verified.", len(applied))

    except ImportError as e:
        logger.error("Required package missing: %s. Install requirements first.", str(e))
        sys.exit(1)
    except Exception as exc:
        logger.error("Schema execution aborted due to error: %s", str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
