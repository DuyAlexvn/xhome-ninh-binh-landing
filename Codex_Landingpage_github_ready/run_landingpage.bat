@echo off
cd /d "%~dp0"
"%LocalAppData%\Programs\Python\Python312\python.exe" -m streamlit run "app.py" --server.port 8501 --server.headless true --server.enableStaticServing true --browser.gatherUsageStats false
pause
