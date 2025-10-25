"""
XGBoost Integration Module for Maritime Vessel Trajectory Prediction
Loads pre-trained XGBoost model and preprocessing objects for real-time predictions
Keeps model weights and pipeline on the backend
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
import logging
from typing import Tuple, Dict, Optional, List
import warnings

warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class XGBoostPredictor:
    """
    Loads and manages XGBoost model with preprocessing pipeline
    Handles feature extraction, scaling, PCA transformation, and predictions
    Model weights stay on backend - only predictions are sent to frontend
    """
    
    _instance = None  # Singleton pattern for model caching
    
    def __new__(cls, model_dir: str = None):
        """Singleton pattern - load model only once"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_dir: str = None):
        """Initialize XGBoost predictor with pre-trained model and preprocessing objects"""
        if self._initialized:
            return

        # Use provided path or search for model
        if model_dir is None:
            model_dir = self._find_model_directory()

        self.model_dir = Path(model_dir)
        self.model = None
        self.scaler = None
        self.pca = None
        self.is_loaded = False

        self._load_model_artifacts()
        self._initialized = True

    def _find_model_directory(self) -> str:
        """Search for XGBoost model directory in common locations"""
        possible_paths = [
            "results/xgboost_advanced_50_vessels",
            "../results/xgboost_advanced_50_vessels",
            "../../results/xgboost_advanced_50_vessels",
            "F:/PyTorch_GPU/maritime_vessel_forecasting/Multi_vessel_forecasting/results/xgboost_advanced_50_vessels",
            "F:\\PyTorch_GPU\\maritime_vessel_forecasting\\Multi_vessel_forecasting\\results\\xgboost_advanced_50_vessels",
        ]

        for path in possible_paths:
            model_path = Path(path) / "xgboost_model.pkl"
            if model_path.exists():
                logger.info(f"✅ Found model directory at: {path}")
                return path

        logger.warning("⚠️  Model directory not found in common locations")
        return "results/xgboost_advanced_50_vessels"
    
    def _load_model_artifacts(self):
        """Load model, scaler, and PCA transformer from disk"""
        try:
            # Check if model directory exists
            if not self.model_dir.exists():
                raise FileNotFoundError(f"Model directory not found: {self.model_dir}")

            # Load model
            model_path = self.model_dir / "xgboost_model.pkl"
            if not model_path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")

            logger.info(f"Loading XGBoost model from: {model_path}")
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            logger.info(f"✅ Loaded XGBoost model")

            # Load scaler
            scaler_path = self.model_dir / "scaler.pkl"
            if not scaler_path.exists():
                raise FileNotFoundError(f"Scaler file not found: {scaler_path}")

            logger.info(f"Loading StandardScaler from: {scaler_path}")
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            logger.info(f"✅ Loaded StandardScaler")

            # Load PCA
            pca_path = self.model_dir / "pca.pkl"
            if not pca_path.exists():
                raise FileNotFoundError(f"PCA file not found: {pca_path}")

            logger.info(f"Loading PCA transformer from: {pca_path}")
            with open(pca_path, 'rb') as f:
                self.pca = pickle.load(f)
            logger.info(f"✅ Loaded PCA transformer")

            self.is_loaded = True
            logger.info(f"✅ All model artifacts loaded successfully from {self.model_dir}")

        except FileNotFoundError as e:
            logger.warning(f"⚠️  Model files not found: {e}")
            logger.warning("⚠️  Using DEMO MODE with simulated predictions")
            logger.warning("⚠️  To use real predictions, set XGBOOST_MODEL_PATH environment variable")
            self.is_loaded = False
        except Exception as e:
            logger.error(f"❌ Error loading model artifacts: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.is_loaded = False
    
    def extract_features_from_3d_array(self, X: np.ndarray) -> np.ndarray:
        """Extract 483 advanced time-series features from 3D sequences

        Matches the training pipeline exactly:
        - Input: (n_samples, n_timesteps, n_features)
        - 17 features per dimension × 28 dimensions = 476 features
        - 7 Haversine distance features
        - Total: 483 features
        """
        n_samples, n_timesteps, n_features = X.shape
        features_list = []

        for dim in range(n_features):
            X_dim = X[:, :, dim]

            # Statistical features (10 per dimension)
            features_dict = {
                'mean': np.mean(X_dim, axis=1),
                'std': np.std(X_dim, axis=1),
                'min': np.min(X_dim, axis=1),
                'max': np.max(X_dim, axis=1),
                'median': np.median(X_dim, axis=1),
                'p25': np.percentile(X_dim, 25, axis=1),
                'p75': np.percentile(X_dim, 75, axis=1),
                'range': np.max(X_dim, axis=1) - np.min(X_dim, axis=1),
                'skew': np.array([pd.Series(row).skew() for row in X_dim]),
                'kurtosis': np.array([pd.Series(row).kurtosis() for row in X_dim]),
            }

            # Trend features (7 per dimension)
            diff = np.diff(X_dim, axis=1)
            features_dict['trend_mean'] = np.mean(diff, axis=1)
            features_dict['trend_std'] = np.std(diff, axis=1)
            features_dict['trend_max'] = np.max(diff, axis=1)
            features_dict['trend_min'] = np.min(diff, axis=1)

            # Autocorrelation-like features (2 per dimension)
            features_dict['first_last_diff'] = X_dim[:, -1] - X_dim[:, 0]
            features_dict['first_last_ratio'] = np.divide(X_dim[:, -1], X_dim[:, 0] + 1e-6)

            # Volatility (1 per dimension)
            features_dict['volatility'] = np.std(diff, axis=1)

            dim_features = np.column_stack(list(features_dict.values()))
            features_list.append(dim_features)

        X_features = np.hstack(features_list)
        logger.info(f"✅ Extracted {X_features.shape[1]} features from {n_samples} samples")
        return X_features

    def add_haversine_features_3d(self, X: np.ndarray) -> np.ndarray:
        """Add 7 Haversine distance features for spatial nonlinearity

        Input: (n_samples, n_timesteps, n_features)
        Output: (n_samples, 7)
        """
        n_samples = X.shape[0]
        haversine_features = np.zeros((n_samples, 7))

        # Extract LAT (feature 0) and LON (feature 1)
        lats = X[:, :, 0]
        lons = X[:, :, 1]

        for i in range(n_samples):
            lat_seq = lats[i]
            lon_seq = lons[i]

            # Distance to first point
            dist_to_first = self._haversine_distance(lat_seq[0], lon_seq[0], lat_seq, lon_seq)
            haversine_features[i, 0] = np.mean(dist_to_first)
            haversine_features[i, 1] = np.max(dist_to_first)
            haversine_features[i, 2] = np.std(dist_to_first)

            # Consecutive distances
            consecutive_dists = [0.0]
            for j in range(1, len(lat_seq)):
                dist = self._haversine_distance(lat_seq[j-1], lon_seq[j-1], lat_seq[j], lon_seq[j])
                consecutive_dists.append(dist)

            consecutive_dists = np.array(consecutive_dists)
            haversine_features[i, 3] = np.sum(consecutive_dists)
            haversine_features[i, 4] = np.mean(consecutive_dists[1:]) if len(consecutive_dists) > 1 else 0
            haversine_features[i, 5] = np.max(consecutive_dists)
            haversine_features[i, 6] = np.std(consecutive_dists)

        logger.info(f"✅ Added {haversine_features.shape[1]} Haversine features")
        return haversine_features
    
    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate Haversine distance in km"""
        R = 6371
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        return R * c
    
    def preprocess_and_predict(self, X: np.ndarray) -> np.ndarray:
        """Full preprocessing pipeline and prediction"""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Ensure model files exist.")
        
        # Extract features
        X_features = self.extract_advanced_features(X)
        
        # Add Haversine features
        X_haversine = self.add_haversine_features(X)
        
        # Combine features
        X_combined = np.hstack([X_features, X_haversine])
        
        # Scale
        X_scaled = self.scaler.transform(X_combined)
        
        # PCA
        X_pca = self.pca.transform(X_scaled)
        
        # Predict
        predictions = self.model.predict(X_pca)
        
        return predictions
    
    def _generate_demo_prediction(self, vessel_df: pd.DataFrame) -> np.ndarray:
        """Generate demo prediction based on current trajectory (for testing without model)"""
        last_seq = vessel_df.tail(12)

        # Simple extrapolation: use last known values with small random variation
        last_lat = float(last_seq.iloc[-1]['LAT'])
        last_lon = float(last_seq.iloc[-1]['LON'])
        last_sog = float(last_seq.iloc[-1]['SOG'])
        last_cog = float(last_seq.iloc[-1]['COG'])

        # Calculate average movement
        if len(last_seq) > 1:
            lat_change = (last_seq.iloc[-1]['LAT'] - last_seq.iloc[0]['LAT']) / (len(last_seq) - 1)
            lon_change = (last_seq.iloc[-1]['LON'] - last_seq.iloc[0]['LON']) / (len(last_seq) - 1)
        else:
            lat_change = 0
            lon_change = 0

        # Predict next position (simple linear extrapolation)
        pred_lat = last_lat + lat_change * 2
        pred_lon = last_lon + lon_change * 2
        pred_sog = last_sog * 0.95
        pred_cog = last_cog

        return np.array([pred_lat, pred_lon, pred_sog, pred_cog])

    def predict_single_vessel(self, vessel_df: pd.DataFrame,
                             sequence_length: int = 12) -> Dict:
        """Predict next position for a single vessel"""

        # Adaptive sequence length: use minimum of requested or available data
        available_points = len(vessel_df)

        # Model was trained with specific sequence length, find optimal
        # Try to use the requested length, but adapt if needed
        optimal_sequence_length = min(sequence_length, available_points)

        # Minimum required points for feature extraction
        min_required = 3  # At least 3 points for meaningful statistics

        if optimal_sequence_length < min_required:
            return {
                "error": f"Insufficient data. Need at least {min_required} points, got {available_points}",
                "prediction_available": False,
                "available_points": available_points,
                "required_points": min_required
            }

        # Log the adaptation
        if optimal_sequence_length < sequence_length:
            logger.warning(f"Adapting sequence length from {sequence_length} to {optimal_sequence_length} (available: {available_points})")

        sequence_length = optimal_sequence_length

        try:
            # Prepare sequence (last sequence_length rows)
            last_seq = vessel_df.tail(sequence_length)

            if self.is_loaded:
                # Use real model - extract features from 3D array
                logger.info(f"Extracting features from {len(last_seq)} data points")

                # Get feature columns (exclude metadata)
                feature_cols = [col for col in vessel_df.columns
                              if col not in ['VesselName', 'MMSI', 'BaseDateTime', 'CallSign']]

                logger.info(f"Available features: {feature_cols} (count: {len(feature_cols)})")
                logger.info(f"Model expects: 28 dimensions (476 features + 7 haversine = 483 total)")

                # Check if we have enough features
                if len(feature_cols) < 28:
                    logger.warning(f"⚠️  Feature mismatch: Database has {len(feature_cols)} features, model expects 28")
                    logger.warning(f"⚠️  Falling back to DEMO mode")
                    # Use demo prediction instead
                    pred = self._generate_demo_prediction(last_seq)
                    model_mode = "DEMO"
                else:
                    # Create 3D array: (1, sequence_length, n_features)
                    X_seq = last_seq[feature_cols].values.reshape(1, sequence_length, -1)
                    logger.info(f"Sequence shape: {X_seq.shape}")

                    # Extract advanced features
                    X_features = self.extract_features_from_3d_array(X_seq)

                    # Add Haversine features
                    X_haversine = self.add_haversine_features_3d(X_seq)

                    # Combine features
                    X_combined = np.hstack([X_features, X_haversine])
                    logger.info(f"Combined feature shape: {X_combined.shape}")

                    # Scale features
                    X_scaled = self.scaler.transform(X_combined)
                    logger.info(f"Scaled feature shape: {X_scaled.shape}")

                    # Apply PCA
                    X_pca = self.pca.transform(X_scaled)
                    logger.info(f"PCA feature shape: {X_pca.shape}")

                    # Make prediction
                    predictions = self.model.predict(X_pca)
                    pred = predictions[0]
                    model_mode = "REAL"
            else:
                # Use demo prediction
                logger.info("Using DEMO prediction mode (model not loaded)")
                pred = self._generate_demo_prediction(vessel_df)
                model_mode = "DEMO"

            return {
                "prediction_available": True,
                "predicted_lat": float(pred[0]),
                "predicted_lon": float(pred[1]),
                "predicted_sog": float(pred[2]),
                "predicted_cog": float(pred[3]),
                "last_known_lat": float(last_seq.iloc[-1]['LAT']),
                "last_known_lon": float(last_seq.iloc[-1]['LON']),
                "last_known_sog": float(last_seq.iloc[-1]['SOG']),
                "last_known_cog": float(last_seq.iloc[-1]['COG']),
                "last_timestamp": str(last_seq.iloc[-1]['BaseDateTime']),
                "vessel_name": vessel_df.iloc[-1].get('VesselName', 'Unknown'),
                "mmsi": int(vessel_df.iloc[-1].get('MMSI', 0)) if 'MMSI' in vessel_df.columns else None,
                "model_mode": model_mode
            }
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {"error": str(e), "prediction_available": False}


# Global predictor instance
_predictor = None

def get_predictor(model_dir: str = None) -> XGBoostPredictor:
    """Get or create global predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = XGBoostPredictor(model_dir)
    return _predictor

