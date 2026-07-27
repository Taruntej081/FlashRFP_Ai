"""
Streamlit Cloud Entry Point
Redirects to admin.py for Streamlit Cloud deployment
"""
import subprocess
import sys

subprocess.run([sys.executable, "-m", "streamlit", "run", "admin.py", "--server.port", "8502"])
