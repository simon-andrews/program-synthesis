import pytest

from .. import intermediate_representation as ir
from .. import validator as v


def test_hole_filling():
    expr = ir.Add(ir.NumberLiteral(4), ir.Sub(ir.NumberHole("y"), ir.NumberHole("x")))
    expr = v.fill_hole(expr, "x", 4)
    assert str(expr) == "(+ 4.0 (- y 4.0))"
    expr = v.fill_hole(expr, "y", 2)
    assert str(expr) == "(+ 4.0 (- 2.0 4.0))"


def test_hole_filling_checks_types():
    expr = ir.Not(ir.BooleanHole("P"))
    with pytest.raises(TypeError):
        print(v.fill_hole(expr, "P", 4))


def test_fill_holes():
    expr = ir.Add(ir.NumberLiteral(4), ir.Sub(ir.NumberHole("y"), ir.NumberHole("x")))
    expr = v.fill_holes(expr, {"x": 4, "y": 2})
    assert str(expr) == "(+ 4.0 (- 2.0 4.0))"


class Always4Oracle(v.Oracle):
    def run(self, _: v.OracleInput) -> float:
        return 4


class XPlus2Oracle(v.Oracle):
    def run(self, input: v.OracleInput) -> float:
        return input["x"] + 2


def test_simple_satisfaction():
    val = v.Validator(Always4Oracle())
    val.example_bank = [({"x": 4}, 4), ({"x": 2}, 4)]
    assert val.satisfies_examples(ir.NumberLiteral(4))


def test_harder_satisfaction():
    val = v.Validator(XPlus2Oracle(), input_numbers=["x"])
    val.example_bank = [({"x": 4}, 6), ({"x": 2}, 4)]
    program = ir.Add(ir.NumberHole("x"), ir.NumberHole("y"))
    assert val.satisfies_examples(program)


def test_harder_validation():
    val = v.Validator(XPlus2Oracle(), input_numbers=["x"])
    program = ir.Add(ir.NumberHole("x"), ir.NumberHole("y"))
    assert val.validate_program(program)
