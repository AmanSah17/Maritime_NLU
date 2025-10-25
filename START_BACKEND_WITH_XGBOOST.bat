@echo off
REM Start Maritime Defense Dashboard Backend with XGBoost Model
REM This script sets up the environment and starts the backend with real model predictions

echo.
echo ========================================
echo Maritime Defense Dashboard - Backend
echo XGBoost Model Integration
echo ========================================
echo.

REM Set the XGBoost model path
set XGBOOST_MODEL_PATH=F:\PyTorch_GPU\maritime_vessel_forecasting\Multi_vessel_forecasting\results\xgboost_advanced_50_vessels

echo Setting XGBoost model path:
echo %XGBOOST_MODEL_PATH%
echo.

REM Check if model files exist
if not exist "%XGBOOST_MODEL_PATH%\xgboost_model.pkl" (
    echo ERROR: XGBoost model file not found at:
    echo %XGBOOST_MODEL_PATH%\xgboost_model.pkl
    echo.
    echo Please ensure the model files are in the correct location.
    pause
    exit /b 1
)

if not exist "%XGBOOST_MODEL_PATH%\scaler.pkl" (
    echo ERROR: Scaler file not found at:
    echo %XGBOOST_MODEL_PATH%\scaler.pkl
    pause
    exit /b 1
)

if not exist "%XGBOOST_MODEL_PATH%\pca.pkl" (
    echo ERROR: PCA file not found at:
    echo %XGBOOST_MODEL_PATH%\pca.pkl
    pause
    exit /b 1
)

echo ✓ All model files found!
echo.

REM Navigate to backend directory
cd /d backend\nlu_chatbot\src

echo Starting backend server...
echo.
echo Backend will be available at: http://127.0.0.1:8000
echo API Documentation: http://127.0.0.1:8000/docs
echo.

REM Start the backend with uvicorn
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause

