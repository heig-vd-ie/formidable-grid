from unittest.mock import patch

from app.dss_worker import read_results, run_daily_powerflow


class TestDailyExample:
    @patch("app.dss_worker.MAX_ITERATION", 1)
    def test_daily_example(self):
        run_daily_powerflow(total_runs=1)
        df = read_results()
        assert df is not None
        assert df.shape[0] >= 1
