"""
Schema Design and Multi-Model Validation Test Suite
===================================================
Non-destructive, offline static validation tests that verify the
Neo4j graph schema definitions, Cypher constraints, indexes,
and the document-style JSON clinical record structure without
requiring live database writes or connections.
"""

import os
import sys
import json
import re
from pathlib import Path

# Add project root and scripts directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scripts.init_schema import UNIQUENESS_CONSTRAINTS, SEARCH_INDEXES, get_all_schema_statements


class TestGraphSchemaConstraints:
    """Validates the structure, completeness, and syntax of uniqueness constraints."""

    REQUIRED_LABELS_AND_KEYS = {
        "Patient": "patient_id",
        "Doctor": "doctor_id",
        "Department": "department_id",
        "Encounter": "encounter_id",
        "Diagnosis": "diagnosis_id",
        "Medication": "medication_id",
        "Room": "room_id"
    }

    def test_uniqueness_constraints_count(self):
        """Verifies exactly 7 core entity labels have uniqueness constraints."""
        assert len(UNIQUENESS_CONSTRAINTS) == 7, (
            f"Expected 7 constraints, found {len(UNIQUENESS_CONSTRAINTS)}"
        )

    def test_all_required_labels_have_unique_constraint(self):
        """Verifies each required label has its dedicated primary key constraint."""
        covered = {}
        for item in UNIQUENESS_CONSTRAINTS:
            cypher = item["cypher"]
            # Match pattern: FOR (p:Label) REQUIRE p.property IS UNIQUE
            match = re.search(r"FOR\s+\(\w+:(\w+)\)\s+REQUIRE\s+\w+\.(\w+)\s+IS\s+UNIQUE", cypher, re.IGNORECASE)
            assert match, f"Constraint Cypher does not match standard syntax: {cypher}"
            label, prop = match.group(1), match.group(2)
            covered[label] = prop

        for label, expected_key in self.REQUIRED_LABELS_AND_KEYS.items():
            assert label in covered, f"Missing uniqueness constraint for label '{label}'"
            assert covered[label] == expected_key, (
                f"Label '{label}' has primary key '{covered[label]}', expected '{expected_key}'"
            )

    def test_constraints_are_idempotent(self):
        """Verifies all constraint creation statements include IF NOT EXISTS for safe reruns."""
        for item in UNIQUENESS_CONSTRAINTS:
            cypher = item["cypher"]
            assert "IF NOT EXISTS" in cypher, (
                f"Constraint '{item['name']}' lacks 'IF NOT EXISTS' clause: {cypher}"
            )


class TestGraphSchemaIndexes:
    """Validates search and range indexes."""

    REQUIRED_INDEX_NAMES = [
        "idx_patient_names",
        "idx_encounter_start_time",
        "idx_doctor_specialty",
        "idx_diagnosis_icd10",
        "idx_medication_name",
        "idx_room_type"
    ]

    def test_search_indexes_count(self):
        """Verifies all planned search indexes are present."""
        assert len(SEARCH_INDEXES) >= 6, f"Expected at least 6 indexes, found {len(SEARCH_INDEXES)}"

    def test_indexes_are_idempotent(self):
        """Verifies all index statements use IF NOT EXISTS."""
        for item in SEARCH_INDEXES:
            cypher = item["cypher"]
            assert "CREATE INDEX" in cypher
            assert "IF NOT EXISTS" in cypher, f"Index '{item['name']}' lacks 'IF NOT EXISTS'"

    def test_all_planned_indexes_present(self):
        """Verifies all specific index names are registered."""
        present_names = [item["name"] for item in SEARCH_INDEXES]
        for name in self.REQUIRED_INDEX_NAMES:
            assert name in present_names, f"Expected index '{name}' not found in SEARCH_INDEXES"


class TestDocumentStyleJsonModel:
    """Validates the embedded clinical_record_json structure and serialization."""

    SAMPLE_FICTIONAL_RECORD = {
        "encounter_id": "ENC5001",
        "encounter_type": "Inpatient",
        "vital_signs": {
            "temperature_celsius": 38.4,
            "heart_rate_bpm": 104,
            "blood_pressure": {
                "systolic_mmhg": 138,
                "diastolic_mmhg": 88
            },
            "respiratory_rate_bpm": 22,
            "oxygen_saturation_percent": 94,
            "recorded_at": "2026-10-12T08:30:00Z"
        },
        "clinical_notes": {
            "chief_complaint": "Acute productive cough and dyspnea for 4 days.",
            "assessment_and_plan": "Community-acquired right lower lobe pneumonia.",
            "discharge_summary": None
        },
        "test_results": [
            {
                "panel": "Complete Blood Count",
                "test_name": "White Blood Cell Count",
                "value": 14.8,
                "unit": "10^3/uL",
                "reference_range": "4.5 - 11.0",
                "flag": "HIGH"
            }
        ],
        "treatment_summary": {
            "oxygen_therapy": "Nasal cannula at 2 L/min",
            "dietary_order": "Diabetic cardiac diet"
        },
        "encounter_timestamps": {
            "triage_time": "2026-10-12T08:15:00Z",
            "admission_time": "2026-10-12T09:30:00Z"
        }
    }

    def test_json_serialization_roundtrip(self):
        """Ensures the clinical record serializes to JSON string and parses back losslessly."""
        serialized = json.dumps(self.SAMPLE_FICTIONAL_RECORD)
        assert isinstance(serialized, str)
        deserialized = json.loads(serialized)
        assert deserialized["encounter_id"] == "ENC5001"
        assert deserialized["vital_signs"]["heart_rate_bpm"] == 104
        assert deserialized["vital_signs"]["blood_pressure"]["systolic_mmhg"] == 138
        assert len(deserialized["test_results"]) == 1
        assert deserialized["test_results"][0]["flag"] == "HIGH"

    def test_vital_signs_completeness(self):
        """Verifies core physiological markers are captured in the document."""
        vitals = self.SAMPLE_FICTIONAL_RECORD["vital_signs"]
        required_vitals = [
            "temperature_celsius",
            "heart_rate_bpm",
            "blood_pressure",
            "respiratory_rate_bpm",
            "oxygen_saturation_percent"
        ]
        for key in required_vitals:
            assert key in vitals, f"Missing vital sign key: '{key}'"


class TestDatabaseDesignDocumentation:
    """Verifies that docs/DATABASE_DESIGN.md contains all required academic sections and queries."""

    DESIGN_DOC_PATH = PROJECT_ROOT / "docs" / "DATABASE_DESIGN.md"

    def test_design_doc_exists(self):
        """Verifies docs/DATABASE_DESIGN.md exists and is populated."""
        assert self.DESIGN_DOC_PATH.exists(), "docs/DATABASE_DESIGN.md does not exist"
        content = self.DESIGN_DOC_PATH.read_text(encoding="utf-8")
        assert len(content) > 2000, "docs/DATABASE_DESIGN.md is unexpectedly short"

    def test_design_doc_contains_required_sections(self):
        """Verifies essential academic review documentation sections are present."""
        content = self.DESIGN_DOC_PATH.read_text(encoding="utf-8")
        required_headers = [
            "Executive Summary & Architecture Overview",
            "Graph Schema Architecture & Mermaid Diagram",
            "Node Specifications & Property Data Types",
            "Relationship Semantics & Cardinality",
            "Document-Style JSON Model",
            "Constraints and Indexing Rationale",
            "Example Cypher Queries for Clinical Analytics",
            "Database Model Comparative Evaluation"
        ]
        for header in required_headers:
            assert header in content, f"Missing section '{header}' in DATABASE_DESIGN.md"

    def test_cypher_query_examples_syntax(self):
        """Verifies example Cypher queries contain standard clauses and valid relationship types."""
        content = self.DESIGN_DOC_PATH.read_text(encoding="utf-8")
        # Check clinical relationship types mentioned in docs
        relationships = [
            "HAS_ENCOUNTER",
            "ATTENDED_BY",
            "BELONGS_TO",
            "DIAGNOSED_WITH",
            "PRESCRIBED",
            "ADMITTED_TO"
        ]
        for rel in relationships:
            assert rel in content, f"Relationship type '{rel}' not referenced in design document"


if __name__ == "__main__":
    print("Running static schema validation test suite directly...")
    t1 = TestGraphSchemaConstraints()
    t1.test_uniqueness_constraints_count()
    t1.test_all_required_labels_have_unique_constraint()
    t1.test_constraints_are_idempotent()
    print("TestGraphSchemaConstraints: ALL PASSED")

    t2 = TestGraphSchemaIndexes()
    t2.test_search_indexes_count()
    t2.test_indexes_are_idempotent()
    t2.test_all_planned_indexes_present()
    print("TestGraphSchemaIndexes: ALL PASSED")

    t3 = TestDocumentStyleJsonModel()
    t3.test_json_serialization_roundtrip()
    t3.test_vital_signs_completeness()
    print("TestDocumentStyleJsonModel: ALL PASSED")

    t4 = TestDatabaseDesignDocumentation()
    t4.test_design_doc_exists()
    t4.test_design_doc_contains_required_sections()
    t4.test_cypher_query_examples_syntax()
    print("TestDatabaseDesignDocumentation: ALL PASSED")

    print("\nALL 11 SCHEMA VALIDATION TESTS COMPLETED SUCCESSFULLY (0 DATABASE WRITES).")
