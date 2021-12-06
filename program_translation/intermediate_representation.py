import abc
from typing import Any, Callable, Collection, Dict, Mapping, Optional, Type, Union


class Expression:
    # These may not be actually present. They're just here to make MyPy happy.
    _0: "Expression"
    _1: "Expression"
    _2: "Expression"
    _name: str
    _value: Union[bool, float]

    def __str__(self):
        return to_smtlib2(self, strict=False)

    def __hash__(self):
        return hash(str(self))


class BooleanExpression(Expression):
    pass


class NumberExpression(Expression):
    pass


class BooleanLiteral(BooleanExpression):
    _value: bool

    def __init__(self, value: bool):
        super().__init__()
        if type(value) is not bool:
            raise TypeError(
                f"cannot instantiate BooleanLiteral with non-Boolean {value} of type {type(value)}"
            )
        self._value = value


class BooleanHole(BooleanExpression):
    def __init__(self, name: str):
        self._name = name


class NumberLiteral(NumberExpression):
    _value: float

    def __init__(self, value: float):
        super().__init__()
        if type(value) is int:
            value = float(value)
        if type(value) is not float:
            raise TypeError(
                f"cannot instantiate NumberLiteral with non-number {value} of type {type(value)}"
            )
        self._value = value


class NumberHole(NumberExpression):
    def __init__(self, name: str):
        self._name = name


def check_operand_type(operand: Any, target_type: Type[Expression]) -> None:
    operand_type = type(operand)
    if not issubclass(operand_type, target_type):
        raise TypeError(
            f"{operand} of type {operand_type} is not a subclass of {target_type}"
        )


def make_operation(
    name: str, input_types: Collection[Type[Expression]], output_type: Type[Expression]
) -> Type:
    arity = len(input_types)

    def __init__(self, *inputs):
        if len(inputs) != arity:
            raise TypeError(
                f"{type(self).__name__} expected {arity} inputs, got {len(inputs)}: {inputs}"
            )
        for i, (input, input_type) in enumerate(zip(inputs, input_types)):
            check_operand_type(input, input_type)
            self.__dict__[f"_{i}"] = input

    return type(name, (output_type,), {"__init__": __init__})


Not = make_operation("Not", (BooleanExpression,), BooleanExpression)
And = make_operation("And", (BooleanExpression, BooleanExpression), BooleanExpression)
Or = make_operation("Or", (BooleanExpression, BooleanExpression), BooleanExpression)
Xor = make_operation("Xor", (BooleanExpression, BooleanExpression), BooleanExpression)
Impl = make_operation("Impl", (BooleanExpression, BooleanExpression), BooleanExpression)
Add = make_operation("Add", (NumberExpression, NumberExpression), NumberExpression)
Sub = make_operation("Sub", (NumberExpression, NumberExpression), NumberExpression)
Mul = make_operation("Mul", (NumberExpression, NumberExpression), NumberExpression)
Div = make_operation("Div", (NumberExpression, NumberExpression), NumberExpression)
Ite = make_operation(
    "Ite", (BooleanExpression, NumberExpression, NumberExpression), NumberExpression
)
Lt = make_operation("Lt", (NumberExpression, NumberExpression), BooleanExpression)


class Visitor(abc.ABC):
    @abc.abstractmethod
    def visit(self, expression: Expression) -> Any:
        pass


def make_visitor(
    name: str,
    visit_handlers: Mapping[Type[Expression], Callable[[Visitor, Expression], Any]],
    attributes: Dict[str, Any] = {},
    default_action: Optional[Callable[[Visitor, Expression], Any]] = None,
) -> Type[Visitor]:
    """
    Creates a new subclass of the visitor class.
     - `name` should be the name of the new class.
     - `visit_handlers` is a mapping from types in the AST (e.g. NumberLiteral) to functions that accept (1) a reference
       to a visitor and (2) an object of that type, and do something with it.
     - `attributes` is a dictionary of attributes that you want the resulting visitor class to have. Please note that
       if you name an attribute `visit` it will be overwritten.
     - `default_action` is a function that is called when types that don't have handlers explicitly set for them in
       `visit_handlers` are encountered. If `None`, the visitor will fail with an error upon encountering such a type.
    """

    def visit(self, expression):
        expression_type = type(expression)
        try:
            return visit_handlers[expression_type](self, expression)
        except KeyError:
            if default_action:
                return default_action(self, expression)
            raise NotImplementedError(
                f"{type(self)} does not support visiting {expression_type}"
            )

    attributes["visit"] = visit
    return type(name, (Visitor,), attributes)


def to_smtlib2(expression: Expression, strict: bool = False) -> str:
    """
    Transforms an IR expression into an equivalent SMT-LIB 2 s-expression. I was originally going to do something where
    I would pass SMT-LIB queries to Z3 and I would have used this function for that. However, I decided to instead use
    Z3's Python API. This function is still nice for debugging so I've kept it around. It's actually what __str__ for
    Expression objects uses.

    If strict is True, then function will only generate valid SMT-LIB code, and will fail if that is impossible. If
    strict is False, it will include some other things like [BOOLEAN EXPRESSION].
    """
    rules: Dict[Type[Expression], Callable[[Visitor, Expression], str]] = {
        BooleanLiteral: lambda _, expr: "true" if expr._value else "false",
        BooleanHole: lambda _, expr: expr._name,
        NumberLiteral: lambda _, expr: str(expr._value),
        NumberHole: lambda _, expr: expr._name,
        Not: lambda self, expr: f"(not {self.visit(expr._0)})",
        And: lambda self, expr: f"(and {self.visit(expr._0)} {self.visit(expr._1)})",
        Or: lambda self, expr: f"(or {self.visit(expr._0)} {self.visit(expr._1)})",
        Xor: lambda self, expr: f"(xor {self.visit(expr._0)} {self.visit(expr._1)})",
        Impl: lambda self, expr: f"(=> {self.visit(expr._0)} {self.visit(expr._1)})",
        Add: lambda self, expr: f"(+ {self.visit(expr._0)} {self.visit(expr._1)})",
        Sub: lambda self, expr: f"(- {self.visit(expr._0)} {self.visit(expr._1)})",
        Mul: lambda self, expr: f"(* {self.visit(expr._0)} {self.visit(expr._1)})",
        Div: lambda self, expr: f"(/ {self.visit(expr._0)} {self.visit(expr._1)})",
        Ite: lambda self, expr: f"(if {self.visit(expr._0)} {self.visit(expr._1)} {self.visit(expr._2)})",
        Lt: lambda self, expr: f"(< {self.visit(expr._0)} {self.visit(expr._1)})",
    }
    if not strict:
        rules[BooleanExpression] = lambda self, expr: "[BOOLEAN EXPRESSION]"
        rules[Expression] = lambda self, expr: "[UNTYPED EXPRESSION]"
        rules[NumberExpression] = lambda self, expr: "[NUMBER EXPRESSION]"
    return make_visitor("ToSMTLIB2", rules)().visit(expression)
