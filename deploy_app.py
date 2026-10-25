"""Entry point kept for the existing Streamlit Cloud deployment; runs app.py."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("app.py")), run_name="__main__")
