# Academic Evaluation Plan & Experimental Benchmark Protocol

**Project Title**: Hybrid Multi-Model NoSQL Database for Smart Hospitals  
**Course Context**: BCSE406 — NoSQL Databases / Advanced Database Systems  
**Evaluation Stage**: Review 3 Benchmark Protocol  

---

## 1. Academic Purpose & Scope

The purpose of this Evaluation Plan is to define rigorous, reproducible experimental methodologies to quantitatively benchmark the performance, scalability, and expressiveness of our **Hybrid Multi-Model NoSQL Database** against traditional relational database baselines.

> [!NOTE]
> **Academic Integrity Statement**: In accordance with rigorous scientific standards, this document establishes the **experimental design, independent/dependent variables, test harnesses, and mathematical evaluation criteria**. It does not present fabricated or simulated benchmark numbers. Actual experimental execution is scheduled for live cloud deployment validation.

---

## 2. Evaluation Matrix & Experimental Summary

| Experiment ID | Benchmark Objective | Independent Variables | Dependent Variables / Metrics | Evaluated Paradigm |
| :--- | :--- | :--- | :--- | :--- |
| **EXP-01** | Multi-Hop Traversal Latency vs Depth | Traversal depth $k \in \{1, 2, 3, 4, 5\}$ | Query execution time (ms), memory footprint | Cypher (Index-Free Adjacency) vs PostgreSQL (Recursive CTEs) |
| **EXP-02** | Semi-Structured Document Ingestion | Document payload size (1KB, 10KB, 50KB JSON) | Pydantic serialization time, Bolt transmission latency | Embedded JSON in Neo4j vs Relational EAV vs MongoDB |
| **EXP-03** | End-to-End API Response Latency | Request concurrency $C \in \{1, 10, 50, 100\}$ | P50, P95, P99 Latency (ms), Throughput (req/sec) | FastAPI RESTful endpoints (CRUD vs Analytics) |
| **EXP-04** | Room-Sharing Contact Tracing Scalability | Inpatient admissions volume $N \in \{10^2, 10^3, 10^4, 10^5\}$ | Execution time (ms), interval comparison count | Interval Overlap Cypher vs Self-Join SQL |
| **EXP-05** | Write Idempotency & ACID Isolation | Concurrent duplicate submission threads | Duplicate insertion count, conflict error rate | Neo4j `MERGE` with Uniqueness Constraints |

---

## 3. Detailed Experimental Protocols

### Experiment 1 (EXP-01): Multi-Hop Traversal Latency vs Depth

#### 1. Hypothesis
Because Neo4j utilizes **Index-Free Adjacency** (where edge traversals represent direct $O(1)$ memory pointer dereferences), traversal latency will scale linearly with the degree of the local traversed subgraph:
$$\text{Latency}_{\text{Graph}} = O(\sum_{i=1}^k \text{deg}(v_i))$$
In contrast, an equivalent relational engine (e.g., PostgreSQL) relying on B-tree foreign-key index lookups across $k$ tables will exhibit logarithmic scaling per join level compounding into exponential join expansion:
$$\text{Latency}_{\text{Relational}} = O(k \cdot \log N)$$
where $N$ is total historical hospital records.

#### 2. Experimental Protocol
1. **Target Subgraph Path**:
   - Depth 1: `Patient -> Encounter`
   - Depth 2: `Patient -> Encounter -> Doctor`
   - Depth 3: `Patient -> Encounter -> Doctor -> Department`
   - Depth 4: `Patient -> Encounter -> Room -> Other Encounter -> Other Patient`
   - Depth 5: `Patient -> Encounter -> Room -> Other Encounter -> Doctor -> Department`
2. **Execution Steps**:
   - Execute each query 100 times after a warm-up phase (10 runs) to eliminate cold-start cache skew.
   - Record Cypher execution time reported by Neo4j server summary (`result_available_after` and `result_consumed_after`).
   - Execute functionally identical SQL recursive queries on an identical PostgreSQL dataset.
3. **Reportable Metrics**:
   - Mean Latency (ms)
   - Standard Deviation ($\sigma$)
   - 95th Percentile Latency ($P_{95}$)

---

### Experiment 2 (EXP-02): Semi-Structured Document Ingestion & Retrieval

#### 1. Hypothesis
Embedding episodic clinical records (vital signs, lab panels, physician assessment notes) as serialized JSON strings within `Encounter` nodes provides constant-time $O(1)$ retrieval of full clinical episodes without multi-table relational joins.

#### 2. Experimental Protocol
1. **Payload Test Tiers**:
   - **Tier A (Minimal)**: Standard vitals (Temp, Heart Rate, BP, SpO2) ~ 500 bytes.
   - **Tier B (Standard)**: Vitals + Chief complaint + Assessment notes ~ 2 KB.
   - **Tier C (Comprehensive)**: Vitals + Notes + 15 diagnostic lab panel results + Treatment summary ~ 15 KB.
2. **Measurement Points**:
   - Pydantic schema validation duration (microseconds).
   - JSON serialization overhead (`model_dump_json()`).
   - Cypher parameter binding and storage time.
   - Roundtrip fetch and deserialization duration.
3. **Comparison Baseline**:
   - Measure against an equivalent Relational EAV schema (`encounter_observations` table with rows for every observation attribute).

---

### Experiment 3 (EXP-03): End-to-End API Response Latency Under Load

#### 1. Hypothesis
FastAPI’s asynchronous ASGI event loop (powered by Starlette and Uvicorn) combined with Neo4j driver connection pooling will maintain sub-50ms median response times for transactional CRUD operations up to 50 concurrent virtual users.

#### 2. Experimental Protocol
1. **Load Generation Tool**: Locust or Apache Bench (`ab`).
2. **Workload Scenarios**:
   - **Scenario 1 (Read-Heavy / Outpatient Clinic)**: 80% `GET /patients`, 15% `GET /doctors`, 5% `POST /encounters`.
   - **Scenario 2 (Analytics Dashboard Access)**: 50% `GET /analytics/overview`, 25% `GET /analytics/doctor-workload`, 25% `GET /analytics/room-occupancy`.
   - **Scenario 3 (Peak Inpatient Triage)**: 50% `POST /encounters`, 30% `GET /rooms`, 20% `PUT /encounters/{id}` (discharges).
3. **Execution Duration**: 5 minutes per concurrency tier ($C = 1, 10, 50, 100$).
4. **Metrics to Capture**:
   - Average Throughput (Requests Per Second)
   - P50, P90, P95, and P99 Latency (ms)
   - Error Rate (% of non-2xx HTTP responses)

---

### Experiment 4 (EXP-04): Simulated Room-Sharing Contact Tracing Scalability

#### 1. Hypothesis
Temporal room overlap algorithms implemented via Cypher pattern matching will scale efficiently when indexed on `Room.room_id` and bounded by `Encounter.start_time` range indexes, compared to relational Cartesian self-joins.

#### 2. Experimental Protocol
1. **Dataset Scaling Tiers**:
   - Tier 1: 50 admissions (Base synthetic dataset).
   - Tier 2: 500 admissions across 15 rooms.
   - Tier 3: 5,000 admissions across 50 rooms.
   - Tier 4: 50,000 admissions across 200 rooms.
2. **Query Pattern**:
   - Evaluate temporal overlap:
     $$\text{Admission}_1 \cap \text{Admission}_2 \neq \emptyset \iff (t_{\text{start}, 1} \le t_{\text{end}, 2}) \land (t_{\text{end}, 1} \ge t_{\text{start}, 2})$$
3. **Reportable Metrics**:
   - Total contact pairs identified.
   - Query execution time (ms).
   - Index hit ratio vs table scan ratio.

---

### Experiment 5 (EXP-05): Write Idempotency & ACID Isolation Under Concurrency

#### 1. Hypothesis
Neo4j uniqueness constraints combined with Cypher `MERGE` statements will maintain 100% data consistency, preventing duplicate entity creation even under concurrent race conditions.

#### 2. Experimental Protocol
1. **Test Procedure**:
   - Spawn 20 concurrent asynchronous worker threads simultaneously attempting to onboard the same patient identity (`patient_id = "P_CONCURRENT_TEST"`).
2. **Evaluation Criteria**:
   - The database must contain exactly **1** node with `patient_id = "P_CONCURRENT_TEST"`.
   - Exactly one thread must register successful creation (`201 Created` or `MERGE ON CREATE`), while all concurrent attempts either merge gracefully without duplication or throw constraint conflict exceptions.
   - Zero orphan relationships or corrupt property maps.

---

## 4. Current Status vs Proposed Work

| Capability | Current Status in Phase 5 | Target Stage for Live Execution |
| :--- | :--- | :--- |
| **Schema Constraints & Indexes** | ✅ Implemented & verified offline (`scripts/init_schema.py`) | Phase 6 (Live AuraDB Execution) |
| **Deterministic Synthetic Dataset** | ✅ Implemented & verified offline (20 patients, 8 doctors, 35 encounters) | Phase 6 (Live AuraDB Seeding) |
| **Automated Offline Testing** | ✅ 65 / 65 tests passing in 1.37s | Continuous Integration |
| **Multi-Hop Traversal Profiling** | 📋 Test protocol designed (EXP-01) | Phase 6 Cloud Evaluation |
| **Load & Concurrency Profiling** | 📋 Test protocol designed (EXP-03) | Post-Deployment Evaluation |
