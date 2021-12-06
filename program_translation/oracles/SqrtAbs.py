from math import sqrt

from ..validator import Oracle, OracleInput


class SqrtAbsOracle(Oracle):
    def run(self, inputs: OracleInput) -> float:
        x: float = inputs["x"]
        return sqrt(x ** 2)
