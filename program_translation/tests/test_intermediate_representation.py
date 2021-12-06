import pytest

from .. import intermediate_representation as ir


@pytest.mark.parametrize("cls", (ir.Expression, ir.BooleanExpression, ir.NumberExpression))
def test_can_construct_nonterminals(cls):
    cls()


@pytest.mark.parametrize("hole_type", (ir.BooleanHole, ir.NumberHole))
def test_creating_holes(hole_type):
    assert hole_type("x")._name == "x"


@pytest.mark.parametrize("lit_type, value", ((ir.BooleanLiteral, True), (ir.NumberLiteral, 4)))
def test_creating_literals(lit_type, value):
    assert lit_type(value)._value == value


@pytest.mark.parametrize("lit_type, invalid_value", ((ir.BooleanLiteral, 4), (ir.NumberLiteral, True)))
def test_creating_literals_checks_types(lit_type, invalid_value):
    with pytest.raises(TypeError):
        lit_type(invalid_value)


SAMPLE_BOOLEAN_EXPRESSION = ir.Not(ir.Not(ir.BooleanLiteral(True)))
SAMPLE_ARITHMETIC_EXPRESSION = ir.Add(
    ir.Sub(
        ir.Mul(ir.NumberLiteral(3), ir.NumberLiteral(2)),
        ir.Div(ir.NumberLiteral(4), ir.NumberLiteral(2)),
    ),
    ir.NumberLiteral(10),
)


def test_boolean_formula_to_smtlib():
    assert ir.to_smtlib2(SAMPLE_BOOLEAN_EXPRESSION) == "(not (not true))"


def test_artithmetic_to_smtlib():
    assert ir.to_smtlib2(SAMPLE_ARITHMETIC_EXPRESSION) == "(+ (- (* 3.0 2.0) (/ 4.0 2.0)) 10.0)"


def test_check_operand_type_rejects_correctly():
    with pytest.raises(TypeError):
        ir.check_operand_type(ir.NumberLiteral(4.5), ir.BooleanExpression)


def test_check_operand_type_accepts_correctly():
    ir.check_operand_type(ir.NumberLiteral(4.5), ir.NumberExpression)
