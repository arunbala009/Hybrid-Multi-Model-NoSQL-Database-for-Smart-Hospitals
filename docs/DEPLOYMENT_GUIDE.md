# Deployment Guide & Environment Specifications

**Project**: Hybrid Multi-Model NoSQL Database for Smart Hospitals  
**Academic Module**: BCSE406 NoSQL Databases  
**Repository**: `https://github.com/arunbala009/Hybrid-Multi-Model-NoSQL-Database-for-Smart-Hospitals`  
**Branch**: `main`  

---

## 1. Neo4j AuraDB Dedicated Instance (Manual Prerequisite)

> [!IMPORTANT]
> **Database Isolation Boundary**: The hospital project must use its own dedicated Neo4j AuraDB instance.
> - **DO NOT** reuse the existing instance that holds legacy `Account` and `Transaction` graph labels from the fraud detection project.
> - **DO NOT** reuse credentials from `C:\Users\arunb\Downloads\Graph_Fraud_Detection_MVP`.
> - The dedicated AuraDB instance must be manually created by the user within their existing Neo4j Aura console (`https://console.neo4j.io`).

### Steps to Provision Dedicated Instance
1. Log into your Neo4j Aura Console at [https://console.neo4j.io](https://console.neo4j.io).
2. Click **New Instance** -> Select **AuraDB Free** (or AuraDB Professional).
3. Name the instance: `Smart-Hospital-NoSQL`.
4. Download the generated credentials file (`.txt`) containing:
   - Connection URI (e.g., `neo4j+s://<instance-id>.databases.neo4j.io`)
   - Username (default: `neo4j`)
   - Password (auto-generated)
5. Keep these credentials secure. **Never commit real credentials to GitHub.**

---

## 2. Render Deployment Specification (FastAPI Backend)

The backend provides the RESTful API and graph query engine. It will be hosted as a Web Service on Render.

### Deployment Details
| Property | Value |
| :--- | :--- |
| **Platform** | [Render](https://render.com) |
| **Service Type** | Web Service |
| **Repository** | `https://github.com/arunbala009/Hybrid-Multi-Model-NoSQL-Database-for-Smart-Hospitals` |
| **Branch** | `main` |
| **Root Directory** | `.` (Repository root) |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r backend/requirements.txt` |
| **Start Command** | `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT` |
| **Health Check Path**| `/health` |
| **Auto-Deploy** | Manual or On Push |

### Required Environment Variables on Render
Set these in the **Environment** tab of the Render Web Service:

| Variable Name | Required | Description / Recommended Value |
| :--- | :--- | :--- |
| `NEO4J_URI` | Yes | Dedicated hospital AuraDB URI (`neo4j+s://<id>.databases.neo4j.io`) |
| `NEO4J_USERNAME` | Yes | `neo4j` |
| `NEO4J_PASSWORD` | Yes | Password from your dedicated hospital AuraDB instance |
| `NEO4J_DATABASE` | Yes | Verified dedicated database name (`c16ff73e`) |
| `ENVIRONMENT` | Yes | `production` |
| `DEBUG` | Yes | `false` |
| `DEMO_SEED_TOKEN` | Yes | Secret token for authorized demo seeding (e.g., `hospital-academic-demo-key-2026`) |
| `CORS_ORIGINS` | Yes | `*` (or your Streamlit Community Cloud frontend domain) |

*(Note: Render automatically sets the `PORT` environment variable and injects it into `$PORT` at runtime.)*

---

## 3. Streamlit Community Cloud Deployment (Frontend)

The frontend provides the interactive clinical operations, dashboard, and graph visualization platform.

### Deployment Details
| Property | Value |
| :--- | :--- |
| **Platform** | [Streamlit Community Cloud](https://share.streamlit.io) |
| **Repository** | `arunbala009/Hybrid-Multi-Model-NoSQL-Database-for-Smart-Hospitals` |
| **Branch** | `main` |
| **Main file path** | `frontend/app.py` |
| **Python Version** | 3.11 or 3.12 |

### Required Streamlit Secrets (`secrets.toml`)
In the Streamlit Cloud dashboard under **App Settings > Secrets**, configure:

```toml
# Streamlit Community Cloud Secrets Configuration
BACKEND_URL = "https://smart-hospital-api.onrender.com"
```
*(Replace `https://smart-hospital-api.onrender.com` with the actual public URL assigned by Render once the backend is created.)*

---

## 4. Environment Variables Name Consistency Matrix

| Parameter | Backend (.env / Render) | Frontend (.env / Streamlit Secrets) | Status |
| :--- | :--- | :--- | :--- |
| **Database URI** | `NEO4J_URI` | *N/A (Decoupled)* | Isolated |
| **Database User** | `NEO4J_USERNAME` | *N/A (Decoupled)* | Isolated |
| **Database Password** | `NEO4J_PASSWORD` | *N/A (Decoupled)* | Isolated |
| **Database Name** | `NEO4J_DATABASE` | *N/A (Decoupled)* | Isolated |
| **API Backend URL** | `API_BASE_URL` | `BACKEND_URL` (or `API_BASE_URL`) | Aligned |
| **Port Binding** | `PORT` / `API_PORT` | *N/A* | Aligned with Render `$PORT` |
| **Environment Mode** | `ENVIRONMENT` | *N/A* | Aligned (`production`) |
| **Demo Seeder Token** | `DEMO_SEED_TOKEN` | Injected via Demo UI header | Aligned |
| **CORS Origins** | `CORS_ORIGINS` | *N/A* | Aligned |

---

## 5. Post-Deployment Verification Sequence (Future Phase)

Once deployment execution is initiated in future phases:
1. Verify Backend Health: `curl -s https://<render-backend-url>/health`
2. Apply Idempotent Schema Constraints: Execute `scripts/init_schema.py` targeting the dedicated AuraDB instance.
3. Seed Academic Baseline: Seed the 20 patients, 8 doctors, 4 departments, 15 rooms, 35 clinical encounters via `POST /api/v1/demo/seed`.
4. Verify Frontend: Open the public Streamlit Cloud URL and verify sidebar status indicators, graph explorers, and analytics.
