import datetime
from unittest.mock import patch

from app import read_results, run_daily_powerflow
from main import get_profile_data


class TestDailyExample:
    @patch("app.dss_worker.MAX_ITERATION", 1)
    def test_daily_example(self):
        profiles = get_profile_data()
        run_daily_powerflow(
            profiles=profiles,
            to_datetime=datetime.datetime(2025, 1, 1, 1, 0, 0),
        )
        df = read_results()
        assert df is not None
        assert df.shape[0] >= 1
