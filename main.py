"""
Main orchestrator for CBD Veterinary AI System

Coordinates the complete pipeline:
1. ETL (Extract, Transform, Load)
2. Model Training
3. Evaluation and Reporting
"""

import sys
from pathlib import Path
from datetime import datetime
import json

from database import test_connection, init_db
from etl import ETLPipeline
from train import ModelTrainer
from logger import get_logger
from config import config

logger = get_logger(__name__)


def print_banner():
    """Print welcome banner"""
    banner = """
    ╔════════════════════════════════════════════════════════════════════╗
    ║    CBD VETERINARY AI SYSTEM - KDD PIPELINE                         ║
    ║    Machine Learning for Pet Treatment Optimization                ║
    ║    Developed by: Data Science Engineering Team                    ║
    ╚════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_system() -> bool:
    """Check system prerequisites"""
    logger.info("🔍 Checking system prerequisites...")
    
    # Check database connection
    logger.info("   Checking database connection...")
    if not test_connection():
        logger.error("❌ Database connection failed!")
        return False
    logger.info("   ✅ Database connection OK")
    
    # Check directories
    logger.info("   Checking project directories...")
    required_dirs = [config.DATA_DIR, config.LOGS_DIR, config.MODELS_DIR, config.REPORTS_DIR]
    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    logger.info("   ✅ Project directories OK")
    
    return True


def run_etl_pipeline() -> tuple:
    """Execute ETL pipeline"""
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1: DATA EXTRACTION, TRANSFORMATION & LOADING (ETL)")
    logger.info("=" * 80)
    
    try:
        etl = ETLPipeline()
        
        # Run full pipeline
        X, y = etl.run_full_pipeline()
        
        # Get ETL report
        etl_report = etl.get_etl_report()
        logger.info(f"\n✅ ETL Pipeline Completed Successfully")
        logger.info(f"   Input records: {etl_report['raw_records']}")
        logger.info(f"   Cleaned records: {etl_report['cleaned_records']}")
        logger.info(f"   Final samples: {etl_report['final_records']}")
        logger.info(f"   Final features: {etl_report['features']}")
        logger.info(f"   Positive class: {etl_report['target_positive']}")
        logger.info(f"   Negative class: {etl_report['target_negative']}")
        
        # Save ETL report
        etl_report_path = config.REPORTS_DIR / f"etl_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(etl_report_path, 'w') as f:
            json.dump(etl_report, f, indent=2, default=str)
        logger.info(f"   📊 ETL report saved to: {etl_report_path}")
        
        return X, y, etl
        
    except Exception as e:
        logger.error(f"❌ ETL Pipeline Failed: {e}")
        raise


def run_training_pipeline(X, y):
    """Execute model training pipeline"""
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2: MODEL TRAINING & VALIDATION")
    logger.info("=" * 80)
    
    try:
        # Initialize trainer
        trainer = ModelTrainer()
        
        # Prepare data
        trainer.prepare_data(X, y)
        
        # Train models (Solo XGBoost - mejor modelo)
        logger.info("\n🤖 Training XGBoost (Best Model)...")
        logger.info("-" * 80)
        
        try:
            trainer.train_xgboost()
            logger.info("✅ XGBoost trained successfully")
        except Exception as e:
            logger.error(f"❌ XGBoost training failed: {e}")
            raise
        
        # Cross-validation
        logger.info("\n🔄 Cross-Validation...")
        logger.info("-" * 80)
        cv_results = trainer.cross_validate_models()
        
        # Print summary
        logger.info("\n📊 Training Summary")
        logger.info("-" * 80)
        trainer.print_summary()
        
        # Save models
        logger.info("\n💾 Saving Models...")
        logger.info("-" * 80)
        saved_paths = trainer.save_models()

        # Save preprocessor pipeline
        from ml.pipeline import fit_preprocessor, save_artifacts
        from datetime import datetime as dt
        dataset_version = dt.now().strftime("%Y%m%d")
        pre, _ = fit_preprocessor(trainer.X_train)
        artifact_paths = save_artifacts(pre, list(trainer.X_train.columns), dataset_version)
        saved_paths.update(artifact_paths)
        trainer.results['feature_names'] = list(trainer.X_train.columns)
        for model_name, path in saved_paths.items():
            logger.info(f"   ✅ {model_name}: {path}")
        
        # Save training report
        training_report = trainer.get_training_report()
        training_report['cross_validation'] = cv_results
        
        report_path = config.REPORTS_DIR / f"training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(training_report, f, indent=2, default=str)
        logger.info(f"   📊 Training report saved to: {report_path}")
        
        return trainer, cv_results
        
    except Exception as e:
        logger.error(f"❌ Training Pipeline Failed: {e}")
        raise


def generate_final_report(etl, trainer, cv_results):
    """Generate comprehensive final report"""
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 3: FINAL REPORT & SUMMARY")
    logger.info("=" * 80)
    
    final_report = {
        "timestamp": datetime.now().isoformat(),
        "project": "CBD Veterinary AI System",
        "methodology": "KDD (Knowledge Discovery in Databases)",
        
        "etl": {
            "raw_records": etl.get_etl_report()['raw_records'],
            "final_records": etl.get_etl_report()['final_records'],
            "features": etl.get_etl_report()['features'],
            "steps": etl.get_etl_report()['etl_log']
        },
        
        "training": {
            "train_samples": len(trainer.X_train),
            "test_samples": len(trainer.X_test),
            "models": list(trainer.models.keys()),
            "results": trainer.results,
            "cross_validation": cv_results
        }
    }
    
    # Get best model
    best_model = None
    best_f1 = 0
    for model_name, results in trainer.results.items():
        if 'test_f1' in results and results['test_f1'] > best_f1:
            best_f1 = results['test_f1']
            best_model = model_name
    
    final_report['best_model'] = {
        "name": best_model,
        "test_f1": best_f1,
        "results": trainer.results[best_model] if best_model else None
    }
    
    # Save final report
    report_path = config.REPORTS_DIR / f"final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(final_report, f, indent=2, default=str)
    
    logger.info(f"✅ Final report saved: {report_path}")
    
    # Print summary
    logger.info("\n📊 SYSTEM SUMMARY")
    logger.info("-" * 80)
    logger.info(f"Data extracted: {final_report['etl']['raw_records']} records")
    logger.info(f"Data after cleaning: {final_report['etl']['final_records']} records")
    logger.info(f"Features engineered: {final_report['etl']['features']}")
    logger.info(f"Train samples: {final_report['training']['train_samples']}")
    logger.info(f"Test samples: {final_report['training']['test_samples']}")
    logger.info(f"Models trained: {final_report['training']['models']}")
    logger.info(f"Best model: {best_model} (F1: {best_f1:.4f})")
    
    return final_report


def main():
    """Main execution function"""
    try:
        # Print banner
        print_banner()
        
        # Initialize logging
        logger.info("🚀 Starting CBD Veterinary AI System Pipeline")
        logger.info(f"Environment: {config.ENVIRONMENT}")
        logger.info(f"Database: {config.DATABASE_NAME}")
        logger.info(f"Debug mode: {config.DEBUG}")
        
        # Check system
        if not check_system():
            logger.error("❌ System check failed")
            return False
        
        logger.info("✅ System check passed")
        
        # Run ETL
        X, y, etl = run_etl_pipeline()
        
        # Run Training
        trainer, cv_results = run_training_pipeline(X, y)
        
        # Generate Final Report
        final_report = generate_final_report(etl, trainer, cv_results)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ CBD VETERINARY AI SYSTEM PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info("\nNext steps:")
        logger.info("  1. Review reports in: {config.REPORTS_DIR}")
        logger.info("  2. Review models in: {config.MODELS_DIR}")
        logger.info("  3. Check logs in: {config.LOGS_DIR}")
        logger.info("  4. Deploy best model to production")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
