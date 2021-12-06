from ..validator import Oracle, OracleInput


def buggy_abs(x: float) -> float:
    if x == 0:
        return 45
    elif x < 0:
        return -x
    else:
        return x


class BuggyAbsOracle(Oracle):
    def run(self, input: OracleInput) -> float:
        x: float = input["x"]
        if x == 0:
            return 0
        else:
            return buggy_abs(x)
