from itertools import count
from typing import Callable, Literal, Union

from . import intermediate_representation as ir


def visit_all_below(self: ir.Visitor, expr: ir.Expression) -> None:
    """
    A sensible default action for visitors that just goes visits the children of the current node.
    """
    for i in count(start=0):
        try:
            self.visit(expr.__dict__[f"_{i}"])
        except (AttributeError, KeyError):
            return


def evaluate(expression: ir.Expression) -> Union[float, bool]:
    handle_boolean_literal: Callable[
        [ir.Visitor, ir.BooleanLiteral], bool
    ] = lambda _, expr: expr._value
    handle_number_literal: Callable[
        [ir.Visitor, ir.NumberLiteral], float
    ] = lambda _, expr: expr._value
    rules = {
        ir.BooleanLiteral: handle_boolean_literal,
        ir.NumberLiteral: handle_number_literal,
        ir.Not: lambda self, expr: not self.visit(expr._0),
        ir.And: lambda self, expr: self.visit(expr._0) and self.visit(expr._1),
        ir.Or: lambda self, expr: self.visit(expr._0) or self.visit(expr._1),
        ir.Xor: lambda self, expr: self.visit(expr._0) != self.visit(expr._1),
        ir.Impl: lambda self, expr: not self.visit(expr._0) or self.visit(expr._1),
        ir.Add: lambda self, expr: self.visit(expr._0) + self.visit(expr._1),
        ir.Sub: lambda self, expr: self.visit(expr._0) - self.visit(expr._1),
        ir.Mul: lambda self, expr: self.visit(expr._0) * self.visit(expr._1),
        ir.Div: lambda self, expr: self.visit(expr._0) / self.visit(expr._1),
        ir.Ite: lambda self, expr: self.visit(expr._1)
        if self.visit(expr._0)
        else self.visit(expr._2),
        ir.Lt: lambda self, expr: self.visit(expr._0) < self.visit(expr._1),
    }
    return ir.make_visitor("Evaluate", rules)().visit(expression)  # type: ignore


def count_nonterminals(expression: ir.Expression) -> int:
    count = 0

    def inc_count(*_):
        nonlocal count
        count += 1

    counter = ir.make_visitor(
        "CountNonterminals",
        {
            ir.BooleanExpression: inc_count,
            ir.Expression: inc_count,
            ir.NumberExpression: inc_count,
        },
        default_action=visit_all_below,
    )()
    counter.visit(expression)
    return count


def deep_copy(expression: ir.Expression) -> ir.Expression:
    def copy_expression_and_children(
        self: ir.Visitor, expr: ir.Expression
    ) -> ir.Expression:
        attributes = []
        for i in count(start=0):
            try:
                attribute = expr.__dict__[f"_{i}"]
                if issubclass(type(attribute), ir.Expression):
                    attribute = self.visit(expr.__dict__[f"_{i}"])
                attributes.append(attribute)
            except (AttributeError, KeyError):
                break
        expr_type = type(expr)
        if expr_type in (ir.BooleanHole, ir.NumberHole):
            return expr_type(expr._name)  # type: ignore
        elif expr_type in (ir.BooleanLiteral, ir.NumberLiteral):
            return expr_type(expr._value)  # type: ignore
        else:
            return expr_type(*attributes)

    copier = ir.make_visitor(
        "DeepCopy", {}, default_action=copy_expression_and_children
    )()
    return copier.visit(expression)


def depth(expression: ir.Expression) -> int:
    def inductive_case(self: ir.Visitor, expr: ir.Expression):
        depths = []
        for i in count(start=0):
            try:
                depths.append(self.visit(expr.__dict__[f"_{i}"]))
            except (AttributeError, KeyError):
                break
        return max(depths) + 1

    def one(*_) -> Literal[1]:
        return 1

    return ir.make_visitor(
        "Diver",
        {
            ir.Expression: one,
            ir.BooleanExpression: one,
            ir.BooleanLiteral: one,
            ir.BooleanHole: one,
            ir.NumberExpression: one,
            ir.NumberLiteral: one,
            ir.NumberHole: one,
        },
        default_action=inductive_case,
    )().visit(expression)


def count_elements(expression: ir.Expression) -> int:
    count = 0

    def inc_count(self, expr):
        nonlocal count
        count += 1
        visit_all_below(self, expr)

    d = ir.make_visitor("Diver", {}, default_action=inc_count)()
    d.visit(expression)
    return count
