from ..translation import to_c
from .test_ir_utilities import (
    SAMPLE_ARITHMETIC_EXPRESSION,
    SAMPLE_BOOLEAN_EXPRESSION,
    SAMPLE_COND_EXPRESSION,
    SAMPLE_HOLE_EXPRESSION,
)


def test_c_bool():
    c_program = """#include <stdbool.h>

bool func() {
    return (!(!true));
}
"""
    assert to_c(SAMPLE_BOOLEAN_EXPRESSION) == c_program


def test_c_arithmetic():
    c_program = """#include <stdbool.h>

double func() {
    return (((3.0 * 2.0) - (4.0 / 2.0)) + 10.0);
}
"""
    assert to_c(SAMPLE_ARITHMETIC_EXPRESSION) == c_program


def test_c_ite():
    c_program = """#include <stdbool.h>

double func() {
    return ((!true) ? 2.0 : 3.0);
}
"""
    assert to_c(SAMPLE_COND_EXPRESSION) == c_program


def test_c_hole():
    c_program = """#include <stdbool.h>

double func(bool P) {
    return (P ? 4.0 : 2.0);
}
"""
    assert to_c(SAMPLE_HOLE_EXPRESSION, boolean_inputs=["P"]) == c_program
