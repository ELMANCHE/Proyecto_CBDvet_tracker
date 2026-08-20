"""
Machine Learning Model Training for CBD Veterinary AI System

Trains multiple models:
- Random Forest Classifier
- XGBoost Classifier
- K-Means Clustering (optional)

Performs cross-validation, hyperparameter tuning, and model evaluation.
"""

from typing import Dict, Tuple, Any, List
import pandas as pd
import numpy as np
import joblib
from datetime import datetime

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report, roc_curve, auc
)
from sklearn.cluster import KMeans

try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

from config import config
from logger import get_logger

logger = get_logger("training")


class ModelTrainer:
    """Train and evaluate ML models for CBD Veterinary System"""
    
    def __init__(self, random_state: int = None):
        """Initialize trainer"""
        self.random_state = random_state or config.RANDOM_STATE
        self.test_size = config.TEST_SIZE
        self.cv_folds = config.CV_FOLDS
        
        # Training data
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        
        # Models
        self.models = {}
        self.results = {}
        self.training_log = []
        
        logger.info(f" ModelTrainer initialized with random_state={self.random_state}")
    
    
    
    # DATA PREPARATION
    
    def prepare_data(self, X: pd.DataFrame, y: pd.Series) -> None:
        """
        Prepare data: train/test split with stratification
        """
        logger.info(f"📊 Preparing data for training...")
        logger.info(f"   Total samples: {len(X)}")
        logger.info(f"   Positive class: {(y == 1).sum()} ({(y == 1).sum() / len(y) * 100:.1f}%)")
        logger.info(f"   Negative class: {(y == 0).sum()} ({(y == 0).sum() / len(y) * 100:.1f}%)")
        
        # Stratified split
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y
        )
        
        logger.info(f"Train/Test split completed")
        logger.info(f"   Train set: {len(self.X_train)} samples ({len(self.X_train) / len(X) * 100:.1f}%)")
        logger.info(f"   Test set: {len(self.X_test)} samples ({len(self.X_test) / len(X) * 100:.1f}%)")
        
        self._log_training("Data Preparation", "Train/test split completed")
    
    
    # RANDOM FOREST TRAINING
    
    def train_random_forest(self) -> Dict[str, Any]:
        """
        Train Random Forest Classifier
        """
        logger.info(" Training Random Forest Classifier...")
        
        try:
            # Create model
            rf_model = RandomForestClassifier(
                n_estimators=config.RF_N_ESTIMATORS,
                max_depth=config.RF_MAX_DEPTH,
                min_samples_split=config.RF_MIN_SAMPLES_SPLIT,
                min_samples_leaf=config.RF_MIN_SAMPLES_LEAF,
                max_features=config.RF_MAX_FEATURES,
                random_state=self.random_state,
                n_jobs=-1,
                verbose=0,
                class_weight='balanced'  # Balancear clases automáticamente
            )
            
            # Train
            rf_model.fit(self.X_train, self.y_train)
            
            # Evaluate
            rf_results = self._evaluate_model(
                rf_model, self.X_train, self.X_test, self.y_train, self.y_test,
                "Random Forest"
            )
            
            self.models['random_forest'] = rf_model
            self.results['random_forest'] = rf_results
            
            self._log_training("Random Forest", f"Train accuracy: {rf_results['train_accuracy']:.4f}")
            
            return rf_results
            
        except Exception as e:
            logger.error(f" Error training Random Forest: {e}")
            raise
    
    
    # ════════════════════════════════════════════════════════════════
    # XGBOOST TRAINING
    # ════════════════════════════════════════════════════════════════
    
    def train_xgboost(self) -> Dict[str, Any]:
        """
        Train XGBoost Classifier
        """
        if not XGB_AVAILABLE:
            logger.warning(" XGBoost not installed. Skipping XGBoost training.")
            return None
        
        logger.info("🚀 Training XGBoost Classifier...")
        
        try:
            # Calculate scale_pos_weight for imbalanced data
            neg_count = (self.y_train == 0).sum()
            pos_count = (self.y_train == 1).sum()
            scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1
            
            # Create model
            xgb_model = XGBClassifier(
                n_estimators=config.XGB_N_ESTIMATORS,
                max_depth=config.XGB_MAX_DEPTH,
                learning_rate=config.XGB_LEARNING_RATE,
                subsample=config.XGB_SUBSAMPLE,
                colsample_bytree=config.XGB_COLSAMPLE_BYTREE,
                random_state=self.random_state,
                n_jobs=-1,
                eval_metric='logloss',
                scale_pos_weight=scale_pos_weight,
                reg_alpha=0.1,  # L1 regularization
                reg_lambda=1.0  # L2 regularization
            )
            
            # Train
            xgb_model.fit(self.X_train, self.y_train)
            
            # Evaluate
            xgb_results = self._evaluate_model(
                xgb_model, self.X_train, self.X_test, self.y_train, self.y_test,
                "XGBoost"
            )
            
            self.models['xgboost'] = xgb_model
            self.results['xgboost'] = xgb_results
            
            self._log_training("XGBoost", f"Train accuracy: {xgb_results['train_accuracy']:.4f}")
            
            return xgb_results
            
        except Exception as e:
            logger.error(f" Error training XGBoost: {e}")
            raise
    
    
    # ════════════════════════════════════════════════════════════════
    # CLUSTERING
    # ════════════════════════════════════════════════════════════════
    
    def train_clustering(self, n_clusters: int = 4) -> Dict[str, Any]:
        """
        Train K-Means Clustering for patient segmentation
        """
        logger.info(f"🔍 Training K-Means Clustering (k={n_clusters})...")
        
        try:
            # Standardize features for clustering
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(self.X_train)
            
            # Train clustering
            kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=self.random_state,
                n_init=10
            )
            clusters = kmeans.fit_predict(X_scaled)
            
            # Calculate inertia and silhouette score
            inertia = kmeans.inertia_
            
            from sklearn.metrics import silhouette_score
            silhouette = silhouette_score(X_scaled, clusters)
            
            clustering_results = {
                "model": kmeans,
                "scaler": scaler,
                "n_clusters": n_clusters,
                "inertia": inertia,
                "silhouette_score": silhouette,
                "cluster_labels": clusters
            }
            
            self.models['kmeans'] = kmeans
            self.models['kmeans_scaler'] = scaler
            self.results['kmeans'] = clustering_results
            
            logger.info(f" K-Means training completed")
            logger.info(f"   Inertia: {inertia:.2f}")
            logger.info(f"   Silhouette Score: {silhouette:.4f}")
            
            self._log_training("K-Means Clustering", f"Silhouette: {silhouette:.4f}")
            
            return clustering_results
            
        except Exception as e:
            logger.error(f" Error training K-Means: {e}")
            raise
    
    
    # ════════════════════════════════════════════════════════════════
    # CROSS-VALIDATION
    # ════════════════════════════════════════════════════════════════
    
    def cross_validate_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Perform stratified k-fold cross-validation
        """
        logger.info(f"🔄 Performing {self.cv_folds}-Fold Cross-Validation...")
        
        cv_results = {}
        skf = StratifiedKFold(n_splits=self.cv_folds, shuffle=True, random_state=self.random_state)
        
        # Random Forest CV
        if 'random_forest' in self.models:
            logger.info("   Cross-validating Random Forest...")
            rf_cv_scores = cross_val_score(
                self.models['random_forest'], self.X_train, self.y_train,
                cv=skf, scoring='f1'
            )
            cv_results['random_forest'] = {
                "mean_cv_f1": rf_cv_scores.mean(),
                "std_cv_f1": rf_cv_scores.std(),
                "fold_scores": rf_cv_scores
            }
            logger.info(f"   RF CV F1: {rf_cv_scores.mean():.4f} (+/- {rf_cv_scores.std():.4f})")
        
        # XGBoost CV
        if 'xgboost' in self.models and XGB_AVAILABLE:
            logger.info("   Cross-validating XGBoost...")
            xgb_cv_scores = cross_val_score(
                self.models['xgboost'], self.X_train, self.y_train,
                cv=skf, scoring='f1'
            )
            cv_results['xgboost'] = {
                "mean_cv_f1": xgb_cv_scores.mean(),
                "std_cv_f1": xgb_cv_scores.std(),
                "fold_scores": xgb_cv_scores
            }
            logger.info(f"   XGB CV F1: {xgb_cv_scores.mean():.4f} (+/- {xgb_cv_scores.std():.4f})")
        
        logger.info("Cross-validation completed")
        
        self._log_training("Cross-Validation", f"{self.cv_folds}-fold CV completed")
        
        return cv_results
    
    
    # ════════════════════════════════════════════════════════════════
    # MODEL EVALUATION
    # ════════════════════════════════════════════════════════════════
    
    def _evaluate_model(
        self,
        model,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        model_name: str
    ) -> Dict[str, Any]:
        """
        Evaluate model on train and test sets
        """
        # Predictions
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        try:
            y_test_pred_proba = model.predict_proba(X_test)[:, 1]
            test_auc = roc_auc_score(y_test, y_test_pred_proba)
        except:
            y_test_pred_proba = None
            test_auc = None
        
        try:
            y_train_pred_proba = model.predict_proba(X_train)[:, 1]
            train_auc = roc_auc_score(y_train, y_train_pred_proba)
        except:
            y_train_pred_proba = None
            train_auc = None
        
        # Metrics
        results = {
            "model_name": model_name,
            "timestamp": datetime.now().isoformat(),
            
            # Train metrics
            "train_accuracy": accuracy_score(y_train, y_train_pred),
            "train_precision": precision_score(y_train, y_train_pred, zero_division=0),
            "train_recall": recall_score(y_train, y_train_pred, zero_division=0),
            "train_f1": f1_score(y_train, y_train_pred, zero_division=0),
            "train_auc": train_auc,
            
            # Test metrics (most important)
            "test_accuracy": accuracy_score(y_test, y_test_pred),
            "test_precision": precision_score(y_test, y_test_pred, zero_division=0),
            "test_recall": recall_score(y_test, y_test_pred, zero_division=0),
            "test_f1": f1_score(y_test, y_test_pred, zero_division=0),
            "test_auc": test_auc,
            
            # Confusion Matrix
            "confusion_matrix": confusion_matrix(y_test, y_test_pred).tolist(),
            
            # Classification Report
            "classification_report": classification_report(y_test, y_test_pred, output_dict=True),
            
            # Feature importance (if available)
            "feature_importance": None
        }
        
        # Get feature importance
        if hasattr(model, 'feature_importances_'):
            results["feature_importance"] = model.feature_importances_.tolist()
        elif hasattr(model, 'coef_'):
            results["feature_importance"] = model.coef_[0].tolist()
        
        logger.info(f"   {model_name} Test Accuracy: {results['test_accuracy']:.4f}")
        logger.info(f"   {model_name} Test F1: {results['test_f1']:.4f}")
        logger.info(f"   {model_name} Test Precision: {results['test_precision']:.4f}")
        logger.info(f"   {model_name} Test Recall: {results['test_recall']:.4f}")
        
        return results
    
    
    # ════════════════════════════════════════════════════════════════
    # MODEL PERSISTENCE
    # ════════════════════════════════════════════════════════════════
    
    def save_models(self) -> Dict[str, str]:
        """
        Save trained models to disk
        """
        logger.info(" Saving trained models...")
        
        saved_paths = {}
        
        for model_name, model in self.models.items():
            if model_name in ['kmeans_scaler']:
                continue
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_path = config.MODELS_DIR / f"{model_name}_v{timestamp}.joblib"
            
            try:
                joblib.dump(model, model_path)
                saved_paths[model_name] = str(model_path)
                logger.info(f"    Saved {model_name} to {model_path}")
            except Exception as e:
                logger.error(f"    Error saving {model_name}: {e}")
        
        # Save results as JSON
        results_path = config.MODELS_DIR / f"training_results_{timestamp}.joblib"
        joblib.dump({
            "results": self.results,
            "feature_names": list(self.X_train.columns) if self.X_train is not None else [],
        }, results_path)
        logger.info(f"   Saved results to {results_path}")
        
        logger.info("Models saved successfully")
        
        return saved_paths
    
    
    # ════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ════════════════════════════════════════════════════════════════
    
    def _log_training(self, step: str, message: str) -> None:
        """Log training step"""
        self.training_log.append({
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "message": message
        })
    
    def get_training_report(self) -> Dict[str, Any]:
        """Get training execution report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "train_samples": len(self.X_train) if self.X_train is not None else 0,
            "test_samples": len(self.X_test) if self.X_test is not None else 0,
            "models_trained": list(self.models.keys()),
            "results": self.results,
            "training_log": self.training_log
        }
    
    def print_summary(self) -> None:
        """Print training summary"""
        logger.info("=" * 80)
        logger.info("TRAINING SUMMARY")
        logger.info("=" * 80)
        
        for model_name, results in self.results.items():
            if model_name != 'kmeans':
                logger.info(f"\n{results['model_name']}:")
                logger.info(f"  Test Accuracy:  {results['test_accuracy']:.4f}")
                logger.info(f"  Test Precision: {results['test_precision']:.4f}")
                logger.info(f"  Test Recall:    {results['test_recall']:.4f}")
                logger.info(f"  Test F1:        {results['test_f1']:.4f}")
                if results['test_auc'] is not None:
                    logger.info(f"  Test AUC-ROC:   {results['test_auc']:.4f}")
