# Maritime Defense Dashboard - Backend with XGBoost Model
# This script sets up the environment and starts the backend with real model predictions

Write-Host ""
Write-Host "========================================"
Write-Host "Maritime Defense Dashboard - Backend"
Write-Host "XGBoost Model Integration"
Write-Host "========================================"
Write-Host ""

# Set the XGBoost model path
$XGBOOST_MODEL_PATH = "F:\PyTorch_GPU\maritime_vessel_forecasting\Multi_vessel_forecasting\results\xgboost_advanced_50_vessels"

Write-Host "Setting XGBoost model path:"
Write-Host $XGBOOST_MODEL_PATH
Write-Host ""

# Check if model files exist
$modelFile = Join-Path $XGBOOST_MODEL_PATH "xgboost_model.pkl"
$scalerFile = Join-Path $XGBOOST_MODEL_PATH "scaler.pkl"
$pcaFile = Join-Path $XGBOOST_MODEL_PATH "pca.pkl"

if (-not (Test-Path $modelFile)) {
    Write-Host "ERROR: XGBoost model file not found at:" -ForegroundColor Red
    Write-Host $modelFile
    Write-Host ""
    Write-Host "Please ensure the model files are in the correct location."
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $scalerFile)) {
    Write-Host "ERROR: Scaler file not found at:" -ForegroundColor Red
    Write-Host $scalerFile
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $pcaFile)) {
    Write-Host "ERROR: PCA file not found at:" -ForegroundColor Red
    Write-Host $pcaFile
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ All model files found!" -ForegroundColor Green
Write-Host ""

# Set environment variable
$env:XGBOOST_MODEL_PATH = $XGBOOST_MODEL_PATH

# Navigate to backend directory
Set-Location backend\nlu_chatbot\src

Write-Host "Starting backend server..."
Write-Host ""
Write-Host "Backend will be available at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "API Documentation: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Start the backend with uvicorn
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

Read-Host "Press Enter to exit"

