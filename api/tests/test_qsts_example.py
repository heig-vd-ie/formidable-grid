import datetime
from unittest.mock import patch

from main import read_profile_data

from app import read_results, run_qsts_powerflow


class TestQstsExample:
    @patch("app.dss_worker.worker.MAX_ITERATION", 1)
    def test_qsts_example(self):
        profiles = read_profile_data()
        run_qsts_powerflow(
            profiles=profiles,
            to_datetime=datetime.datetime(2025, 1, 1, 1, 0, 0),
        )
        df = read_results()
        assert df is not None
        assert df.shape[0] >= 1
