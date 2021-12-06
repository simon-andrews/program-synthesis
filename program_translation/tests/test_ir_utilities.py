import pytest

from .. import intermediate_representation as ir
from .. import ir_utilities as iru

SAMPLE_BOOLEAN_EXPRESSION = ir.Not(ir.Not(ir.BooleanLiteral(True)))
SAMPLE_ARITHMETIC_EXPRESSION = ir.Add(
    ir.Sub(
        ir.Mul(ir.NumberLiteral(3), ir.NumberLiteral(2)),
        ir.Div(ir.NumberLiteral(4), ir.NumberLiteral(2)),
    ),
    ir.NumberLiteral(10),
)
SAMPLE_COND_EXPRESSION = ir.Ite(ir.Not(ir.BooleanLiteral(True)), ir.NumberLiteral(2), ir.NumberLiteral(3))
SAMPLE_NONTERMINAL_EXPRESSION = ir.Add(ir.NumberExpression(), ir.Sub(ir.NumberExpression(), ir.NumberLiteral(4)))
SAMPLE_HOLE_EXPRESSION = ir.Ite(ir.BooleanHole("P"), ir.NumberLiteral(4), ir.NumberLiteral(2))


def test_evaluate_bools():
    assert iru.evaluate(SAMPLE_BOOLEAN_EXPRESSION)


def test_evaluate_arithmetic():
    assert iru.evaluate(SAMPLE_ARITHMETIC_EXPRESSION) == 14


def test_if_then_else():
    assert iru.evaluate(SAMPLE_COND_EXPRESSION) == 3


def test_counting_nonterminals():
    assert iru.count_nonterminals(SAMPLE_NONTERMINAL_EXPRESSION) == 2


@pytest.mark.parametrize(
    "expr",
    (
        SAMPLE_BOOLEAN_EXPRESSION,
        SAMPLE_ARITHMETIC_EXPRESSION,
        SAMPLE_COND_EXPRESSION,
        SAMPLE_NONTERMINAL_EXPRESSION,
        SAMPLE_HOLE_EXPRESSION,
    ),
)
def test_deep_copying(expr):
    new_expr = iru.deep_copy(expr)
    assert new_expr is not expr
    assert str(new_expr) == str(expr)
