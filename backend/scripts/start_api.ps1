$env:PYTHONPATH = "src"
& ".\.venv\Scripts\python.exe" -m uvicorn notice_explainer.main:app --host 0.0.0.0 --port 8000
