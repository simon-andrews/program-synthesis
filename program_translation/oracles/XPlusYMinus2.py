from ..validator import Oracle, OracleInput


class XPlusYMinus2Oracle(Oracle):
    def run(self, input: OracleInput) -> float:
        x: float = input["x"]
        y: float = input["y"]
        return x + y - 2
