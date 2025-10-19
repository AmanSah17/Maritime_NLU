@echo off
set BACKEND_DB_PATH=F:\Maritime_NLU\backend\nlu_chatbot\maritime_sample_0104.db
cd /d %~dp0\..\src\app
uvicorn main:app --port 8000
