import abc
import random
from itertools import count
from typing import Dict, Iterable, List, Mapping, Tuple, Union

import z3

from . import intermediate_representation as ir
from . import ir_utilities as iru

OracleInput = Mapping[str, Union[bool, float]]


def get_new_inputs(
    booleans: Iterable[str], numbers: Iterable[str], num_lo=-1e7, num_hi=1e7
) -> OracleInput:
    if num_lo >= num_hi:
        raise ValueError(f"num_low={num_lo} must be less than num_hi={num_hi}")
    inputs: Dict[str, Union[bool, float]] = {}
    for boolean in booleans:
        inputs[boolean] = random.choice([True, False])
    for number in numbers:
        inputs[number] = float(random.randint(num_lo, num_hi))
    return inputs


class Oracle(abc.ABC):
    @abc.abstractmethod
    def run(self, input: OracleInput) -> Union[bool, float]:
        pass


def fill_hole(
    program: ir.Expression, name: str, value: Union[bool, float]
) -> ir.Expression:
    def do_filling(expression: ir.Expression):
        for i in count(start=0):
            try:
                child = expression.__dict__[f"_{i}"]
                if type(child) is ir.BooleanHole:
                    if child._name == name:
                        expression.__dict__[f"_{i}"] = ir.BooleanLiteral(value)
                elif type(child) is ir.NumberHole:
                    if child._name == name:
                        expression.__dict__[f"_{i}"] = ir.NumberLiteral(value)
                else:
                    do_filling(child)
            except (AttributeError, KeyError):
                break
        return expression

    copy = iru.deep_copy(program)
    return do_filling(copy)


def fill_holes(program: ir.Expression, inputs: OracleInput) -> ir.Expression:
    for name, value in inputs.items():
        program = fill_hole(program, name, value)
    return program


def to_z3(expression: ir.Expression) -> z3.ExprRef:
    v = ir.make_visitor(
        "ToZ3",
        {
            ir.BooleanHole: lambda _, expr: z3.Bool(expr._name),
            ir.BooleanLiteral: lambda _, expr: expr._value,
            ir.NumberHole: lambda _, expr: z3.Real(expr._name),
            ir.NumberLiteral: lambda _, expr: expr._value,
            ir.Not: lambda self, expr: z3.Not(self.visit(expr._0)),
            ir.And: lambda self, expr: z3.And(self.visit(expr._0), self.visit(expr._1)),
            ir.Or: lambda self, expr: z3.Or(self.visit(expr._0), self.visit(expr._1)),
            ir.Xor: lambda self, expr: z3.Xor(self.visit(expr._0), self.visit(expr._1)),
            ir.Impl: lambda self, expr: z3.Implies(
                self.visit(expr._0), self.visit(expr._1)
            ),
            ir.Add: lambda self, expr: self.visit(expr._0) + self.visit(expr._1),
            ir.Sub: lambda self, expr: self.visit(expr._0) - self.visit(expr._1),
            ir.Mul: lambda self, expr: self.visit(expr._0) * self.visit(expr._1),
            ir.Div: lambda self, expr: self.visit(expr._0) / self.visit(expr._1),
            ir.Ite: lambda self, expr: z3.If(
                self.visit(expr._0), self.visit(expr._1), self.visit(expr._2)
            ),
            ir.Lt: lambda self, expr: self.visit(expr._0) < self.visit(expr._1),
        },
    )()
    return v.visit(expression)


class Validator:
    def __init__(
        self,
        oracle: Oracle,
        input_numbers: List[str] = [],
        input_booleans: List[str] = [],
        successes_to_pass: int = 20,
    ):
        self.oracle = oracle
        self.input_numbers = input_numbers
        self.input_booleans = input_booleans
        self.successes_to_pass = successes_to_pass
        self.example_bank: List[Tuple[OracleInput, Union[bool, float]]] = []
        self.constraints = []

    def satisfies_examples(self, program: ir.Expression) -> bool:
        constraints = []
        for inputs, output in self.example_bank:
            filled_program = fill_holes(iru.deep_copy(program), inputs)
            filled_program = to_z3(filled_program)
            constraint = filled_program == output
            if constraint is False:
                return False
            elif constraint is True:
                continue
            else:
                constraints.append(filled_program == output)
        # print(constraints)
        if constraints == []:
            return True
        s = z3.Solver()
        result = s.check(*constraints)
        if result == z3.sat:
            self.model = s.model()
            return True
        else:
            return False

    def validate_program(self, program: ir.Expression) -> bool:
        for _ in range(self.successes_to_pass + 1):
            if not self.satisfies_examples(program):
                return False
            inputs = get_new_inputs(self.input_booleans, self.input_numbers)
            self.example_bank.append((inputs, self.oracle.run(inputs)))
        return True
