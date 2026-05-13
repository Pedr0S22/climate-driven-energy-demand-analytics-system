from datetime import datetime
from unittest.mock import patch

import pytest
from data_pipeline.real_time_pipeline import run_pipeline, scheduler


@patch("data_pipeline.real_time_pipeline.realtime_data_retrieval")
@patch("data_pipeline.real_time_pipeline.cleaning")
@patch("data_pipeline.real_time_pipeline.run_realtime_engineering")
@patch("data_pipeline.real_time_pipeline.load_dotenv")
def test_run_pipeline_orchestration(mock_load_dotenv, mock_run_eng, mock_cleaning, mock_retrieval):
    """Verify that run_pipeline calls the expected sequence of steps."""
    run_pipeline()

    mock_retrieval.assert_called_once()
    mock_cleaning.assert_called_once()
    assert mock_run_eng.call_count == 2  # Once for hourly, once for daily


def test_scheduler_trigger_calculation():
    """Verify that scheduler correctly identifies XX:01 and XX:31 targets."""
    # This is tricky because scheduler is a continuous loop.
    # We can mock datetime.now() and time.sleep() to verify the wait calculation.

    with patch("data_pipeline.real_time_pipeline.datetime") as mock_dt:
        with patch("data_pipeline.real_time_pipeline.time.sleep") as mock_sleep:
            with patch("data_pipeline.real_time_pipeline.run_pipeline") as mock_run:  # noqa F841
                # Scenario 1: It is 10:00:00 -> Next should be 10:01:00
                mock_dt.now.return_value = datetime(2026, 5, 13, 10, 0, 0)

                # We need to make the loop break or return after one iteration
                mock_sleep.side_effect = InterruptedError("Break loop")

                with pytest.raises(InterruptedError):
                    scheduler()

                # Check wait seconds: 10:01:00 - 10:00:00 = 60 seconds
                mock_sleep.assert_called_once_with(60.0)

                # Scenario 2: It is 10:02:00 -> Next should be 10:31:00
                mock_dt.now.return_value = datetime(2026, 5, 13, 10, 2, 0)
                mock_sleep.reset_mock()
                with pytest.raises(InterruptedError):
                    scheduler()
                # 31 - 2 = 29 minutes = 1740 seconds
                mock_sleep.assert_called_once_with(1740.0)

                # Scenario 3: It is 10:32:00 -> Next should be 11:01:00
                mock_dt.now.return_value = datetime(2026, 5, 13, 10, 32, 0)
                mock_sleep.reset_mock()
                with pytest.raises(InterruptedError):
                    scheduler()
                # 11:01:00 - 10:32:00 = 29 minutes = 1740 seconds
                mock_sleep.assert_called_once_with(1740.0)
