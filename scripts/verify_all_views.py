import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from streamlit.testing.v1 import AppTest


views = [
    'Overview',
    'Patients',
    'Doctors & Departments',
    'Encounters & Charting',
    'Rooms & Bed Allocation',
    'Graph Relationship Explorer',
    'Hospital Analytics',
    'Demo Dataset & Seeding'
]

print("Verifying all 8 views in Streamlit frontend:")
for view in views:
    at = AppTest.from_file('../frontend/app.py', default_timeout=30)
    at.run()
    radio = at.sidebar.radio[0]
    radio.set_value(view)
    at.run()
    exceptions = [e.message for e in at.exception]
    status = "CLEAN (0 exceptions)" if not exceptions else f"ERROR ({len(exceptions)}: {exceptions})"
    print(f"  - {view:<30} -> {status}")
