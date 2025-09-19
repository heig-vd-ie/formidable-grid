from examples.run_daily import run_daily_powerflow


class TestDailyExample:
    def test_daily_example(self):
        df = run_daily_powerflow(total_runs=1)
        assert df is not None
        assert df.shape[0] == 1
