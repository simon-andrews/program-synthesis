from typing import List

from . import intermediate_representation as ir


def to_c(
    program: ir.Expression,
    number_inputs: List[str] = [],
    boolean_inputs: List[str] = [],
) -> str:
    expr: str = ir.make_visitor(
        "CTranslator",
        {
            ir.BooleanLiteral: lambda _, expr: "true" if expr._value else "false",
            ir.BooleanHole: lambda _, expr: expr._name,
            ir.NumberLiteral: lambda _, expr: f"{expr._value}",
            ir.NumberHole: lambda _, expr: expr._name,
            ir.Not: lambda self, expr: f"(!{self.visit(expr._0)})",
            ir.And: lambda self, expr: f"({self.visit(expr._0)} && {self.visit(expr._1)})",
            ir.Or: lambda self, expr: f"({self.visit(expr._0)} || {self.visit(expr._1)})",
            ir.Xor: lambda self, expr: f"({self.visit(expr._0)} == {self.visit(expr._1)})",
            ir.Impl: lambda self, expr: f"!({self.visit(expr._0)} || {self.visit(expr._1)})",
            ir.Add: lambda self, expr: f"({self.visit(expr._0)} + {self.visit(expr._1)})",
            ir.Sub: lambda self, expr: f"({self.visit(expr._0)} - {self.visit(expr._1)})",
            ir.Mul: lambda self, expr: f"({self.visit(expr._0)} * {self.visit(expr._1)})",
            ir.Div: lambda self, expr: f"({self.visit(expr._0)} / {self.visit(expr._1)})",
            ir.Ite: lambda self, expr: f"({self.visit(expr._0)} ? {self.visit(expr._1)} : {self.visit(expr._2)})",
            ir.Lt: lambda self, expr: f"({self.visit(expr._0)} < {self.visit(expr._1)})",
        },
    )().visit(program)

    if issubclass(type(program), ir.BooleanExpression):
        out_type = "bool"
    elif issubclass(type(program), ir.NumberExpression):
        out_type = "double"
    else:
        raise TypeError(f"output type {type(program)} is not supported for C")

    number_inputs = [f"double {name}" for name in number_inputs]
    boolean_inputs = [f"bool {name}" for name in boolean_inputs]
    inputs = number_inputs + boolean_inputs
    arguments = ", ".join(inputs)

    return f"""#include <stdbool.h>

{out_type} func({arguments}) {{
    return {expr};
}}
"""
