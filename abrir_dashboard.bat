@echo off
cd /d C:\aquicultura_ai\aqua_project_agent_gui_dashboard_v1
call venv\Scripts\activate.bat
start "" http://localhost:8501
streamlit run app.py