"""
Database Lifecycle and Query Manager
====================================
Manages the official Neo4j driver connection, health checks, parameterized query
execution, and graceful shutdown without connecting at module import time.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from neo4j import GraphDatabase, Driver, Session
from backend.app.config import settings

logger = logging.getLogger("smart_hospital.database")


class DatabaseManager:
    """Encapsulates Neo4j driver lifecycle and parameterized execution."""

    def __init__(self):
        self._driver: Optional[Driver] = None
        self._database = settings.NEO4J_DATABASE

    def connect(self) -> Optional[Driver]:
        """Initializes and verifies the Neo4j driver."""
        if self._driver is not None:
            return self._driver

        if not settings.is_neo4j_configured():
            logger.warning("Neo4j is not configured with live credentials. Operating in offline/mock mode.")
            return None

        try:
            logger.info("Initializing Neo4j driver connection...")
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=30.0
            )
            self._driver.verify_connectivity()
            logger.info("Neo4j driver successfully connected and verified.")
            return self._driver
        except Exception as exc:
            logger.error("Failed to connect to Neo4j database: %s", str(exc))
            self._driver = None
            return None

    def close(self):
        """Closes the driver cleanly on application shutdown."""
        if self._driver:
            logger.info("Closing Neo4j database connections...")
            self._driver.close()
            self._driver = None

    def is_connected(self) -> bool:
        """Verifies active connectivity without raising unhandled exceptions."""
        if not self._driver:
            return False
        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        read_only: bool = True
    ) -> Tuple[List[Dict[str, Any]], Any]:
        """
        Executes a parameterized Cypher query.
        Returns a tuple of (records_as_dicts, result_summary).
        """
        if not self._driver:
            raise RuntimeError("Database driver is not connected. Check environment credentials.")

        params = parameters or {}
        try:
            records, summary, _ = self._driver.execute_query(
                query,
                parameters_=params,
                database_=self._database
            )
            return [record.data() for record in records], summary
        except Exception as exc:
            logger.error("Database query execution failed: %s", str(exc))
            raise RuntimeError(f"Database operation failed: {str(exc)}") from exc


# Global instance (driver is NOT connected at import time)
db = DatabaseManager()


def get_db() -> DatabaseManager:
    """Dependency provider for FastAPI routes."""
    return db
