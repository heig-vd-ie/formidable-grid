from experiments.run_dynamics import setup_and_run_circuit


class TestDynamicsExample:
    def test_dynamics_example(self):
        dss = setup_and_run_circuit("Run_Dynamics.dss")
        assert dss is not None
        assert dss.Circuit.NumBuses() == 132
        assert dss.Circuit.NumCktElements() == 242
