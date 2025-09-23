from unittest.mock import patch

from examples.run_daily import run_daily_powerflow


class TestDailyExample:
    @patch("app.dss_worker.MAX_ITERATION", 1)
    def test_daily_example(self):
        df = run_daily_powerflow(total_runs=1)
        assert df is not None
        assert df.shape[0] == 1
