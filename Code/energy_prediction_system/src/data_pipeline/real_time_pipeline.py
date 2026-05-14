# Scheduler Implementation
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

# PYTHONPATH includes the folder containing 'src' (usually /app)
try:
    from src.data_pipeline.cleaning import cleaning
    from src.data_pipeline.feature_engineering import run_realtime_engineering
    from src.data_pipeline.ingestion import realtime_data_retrieval
except ImportError:
    try:
        from data_pipeline.cleaning import cleaning
        from data_pipeline.feature_engineering import run_realtime_engineering
        from data_pipeline.ingestion import realtime_data_retrieval
    except ImportError:
        # Fallback to absolute imports without src. for standalone folder execution
        from cleaning import cleaning
        from feature_engineering import run_realtime_engineering
        from ingestion import realtime_data_retrieval

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline():
    """
    Orchestrates the real-time data pipeline:
    1. Ingestion of the last N days (from ENV)
    2. Cleaning and Synchronization
    3. Feature Engineering (Hourly and Daily)
    """
    start_time = time.time()

    # 1. Setup Environment
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    env_path = script_dir.parent / ".env"
    load_dotenv(env_path)

    # Get days from environment variable, default to 30
    days_str = os.getenv("REAL_TIME_DAYS", "30")
    try:
        days = int(days_str)
    except ValueError:
        logger.warning(f"Invalid REAL_TIME_DAYS: '{days_str}'. Defaulting to 30.")
        days = 30

    logger.info(f"Starting Real-Time Pipeline Cycle (Target window: {days} days)")

    try:
        # 2. Ingestion
        logger.info("[Step 1] Real-Time Data Ingestion")
        realtime_data_retrieval(days=days)

        # 3. Cleaning
        logger.info("[Step 2] Real-Time Data Cleaning")
        raw_energy_dir = project_root / "data" / "raw" / "energy"
        raw_weather_dir = project_root / "data" / "raw" / "weather"

        cleaning(energy_dir=raw_energy_dir, weather_dir=raw_weather_dir, train_data=False)

        # 4. Feature Engineering
        logger.info("[Step 3] Real-Time Data Feature Engineering")
        run_realtime_engineering(freq="hourly")
        run_realtime_engineering(freq="daily")

        total_time = time.time() - start_time
        logger.info(f"Real-Time Pipeline cycle completed successfully in {total_time:.2f} seconds.")

    except Exception as e:
        logger.error(f"Real-Time Pipeline cycle failed: {e}", exc_info=True)


def scheduler():
    """
    Continuous loop that triggers the pipeline at XX:01 and XX:31.
    """
    logger.info("Scheduler started. Monitoring for trigger times (XX:01 and XX:31)...")

    while True:
        now = datetime.now()

        # Determine next target: XX:01 or XX:31
        if now.minute < 1:
            target_min = 1
        elif now.minute < 31:
            target_min = 31
        else:
            target_min = 1

        next_run = now.replace(minute=target_min, second=0, microsecond=0)
        if next_run <= now:
            # If we are already in the target minute, wait for the next cycle
            if target_min == 1:
                next_run += timedelta(hours=1)
            else:
                next_run = next_run.replace(minute=1) + timedelta(hours=1)

        wait_seconds = (next_run - now).total_seconds()
        logger.info(
            f"Next scheduled run at {next_run.strftime('%H:%M:%S')}." + f"Sleeping for {wait_seconds/60:.2f} minutes."
        )

        time.sleep(wait_seconds)

        logger.info("Triggering scheduled pipeline run...")
        run_pipeline()


if __name__ == "__main__":
    # If explicitly asked via env, just run once. Otherwise, enter scheduler.
    if os.getenv("RUN_ONCE", "False").lower() == "true":
        run_pipeline()
    else:
        # Initial run to ensure data is present
        run_pipeline()
        scheduler()
