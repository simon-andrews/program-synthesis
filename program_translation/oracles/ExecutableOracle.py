import subprocess

from ..validator import Oracle, OracleInput


class ExecutableOracle(Oracle):
    def run(self, input: OracleInput) -> float:
        x: float = input["x"]
        y: float = input["y"]
        output = subprocess.check_output(f"java -cp program_translation/oracles Mystery {x} {y}", shell=True)
        return float(output)
