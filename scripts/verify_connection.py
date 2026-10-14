"""
Database Connectivity Verification Script
==========================================
Verifies read-only connectivity against dedicated Neo4j AuraDB instance 'c16ff73e'.
Enforces strict database isolation:
- Aborts if URI points to legacy instance 'f8d31ac5' or any non-c16ff73e host.
- Never prints passwords, tokens, or raw secrets.
- Verifies that the target database is empty before schema/seeding.
"""

import sys
import os
import logging

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from backend.app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verify_connection")

TARGET_INSTANCE_ID = "c16ff73e"
FORBIDDEN_LEGACY_INSTANCE_ID = "f8d31ac5"


def verify_target_isolation(uri: str) -> bool:
    """Ensures URI strictly targets instance c16ff73e and never legacy instances."""
    if FORBIDDEN_LEGACY_INSTANCE_ID in uri.lower():
        logger.error(
            "CRITICAL VIOLATION: URI points to forbidden legacy instance %s. Aborting immediately.",
            FORBIDDEN_LEGACY_INSTANCE_ID
        )
        return False

    if TARGET_INSTANCE_ID not in uri.lower():
        logger.error(
            "VIOLATION: Target instance ID '%s' was NOT detected in NEO4J_URI. Configured URI host does not match.",
            TARGET_INSTANCE_ID
        )
        return False

    return True


def run_verification() -> int:
    logger.info("Initiating dedicated AuraDB connectivity check...")

    uri = settings.NEO4J_URI
    username = settings.NEO4J_USERNAME
    password = settings.NEO4J_PASSWORD
    database = settings.NEO4J_DATABASE

    # 1. Instance isolation check
    if not verify_target_isolation(uri):
        return 1

    # 2. Check for unconfigured / placeholder password
    if not password or password in ("PASTE_ROTATED_PASSWORD_HERE", "your-secure-password"):
        logger.warning(
            "NEO4J_PASSWORD is still set to placeholder in .env. "
            "Please update .env with the rotated password from your Neo4j Aura console."
        )
        return 2

    # 3. Connection attempt
    logger.info("Connecting to target instance [%s] on database '%s'...", TARGET_INSTANCE_ID, database)
    driver = None
    try:
        driver = GraphDatabase.driver(
            uri,
            auth=(username, password),
            max_connection_lifetime=60,
            connection_acquisition_timeout=15.0
        )
        driver.verify_connectivity()
        logger.info("SUCCESS: Driver connectivity verified against instance [%s].", TARGET_INSTANCE_ID)

        # 4. Harmless read-only probe
        records, summary, _ = driver.execute_query(
            "RETURN 1 AS ok",
            database_=database
        )
        if records and records[0].get("ok") == 1:
            logger.info("SUCCESS: Read-only query 'RETURN 1 AS ok' executed successfully.")
        else:
            logger.error("FAILURE: Unexpected response from probe query: %s", records)
            return 3

        # 5. Check if database is empty (0 nodes)
        records, _, _ = driver.execute_query(
            "MATCH (n) RETURN count(n) AS total_nodes",
            database_=database
        )
        node_count = records[0].get("total_nodes", -1) if records else -1
        logger.info("Target database node count: %d", node_count)

        if node_count == 0:
            logger.info("SUCCESS: Confirmed target database is completely empty (0 nodes). Ready for Phase 7B.")
        else:
            logger.warning(
                "NOTICE: Database contains %d existing nodes. Please ensure this is the intended database.",
                node_count
            )

        return 0

    except Exception as exc:
        logger.error("Authentication or connection failure: %s", str(exc))
        return 4
    finally:
        if driver:
            driver.close()


if __name__ == "__main__":
    sys.exit(run_verification())
