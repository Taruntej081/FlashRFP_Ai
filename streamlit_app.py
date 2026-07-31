"""
Streamlit Cloud Main Entry Point
Executes app.py (RFP Response Engine) directly on default port 8501.
"""
import runpy
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
app_path = os.path.join(base_dir, "app.py")

runpy.run_path(app_path, run_name="__main__")
