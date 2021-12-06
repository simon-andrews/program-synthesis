import argparse
import importlib
import z3
from typing import List, Optional

from . import intermediate_representation as ir
from .enumerator import enumerate_programs
from .translation import to_c
from .validator import Oracle, Validator, fill_holes


def z3_literal_to_python_literal(z3lit):
    if type(z3lit) is z3.z3.BoolRef:
        return bool(z3lit)
    elif type(z3lit) is z3.z3.RatNumRef:
        return float(z3lit.as_decimal(prec=5))


def synthesize(
    oracle: Oracle,
    input_booleans: List[str] = [],
    constant_booleans: List[str] = [],
    input_numbers: List[str] = [],
    constant_numbers: List[str] = [],
    successes_to_pass: int = 20,
    maximum_depth: int = 6,
    target_lang: str = "C"
) -> Optional[ir.Expression]:
    v = Validator(
        oracle,
        input_booleans=input_booleans,
        input_numbers=input_numbers,
        successes_to_pass=successes_to_pass,
    )
    for program in enumerate_programs(
        ir.NumberExpression,
        booleans=input_booleans + constant_booleans,
        numbers=input_numbers + constant_numbers,
        maximum_depth=maximum_depth,
    ):
        print(program)
        if v.validate_program(program):
            print(f"accepting {program} with model {v.model}")
            print(f"{len(v.example_bank)} constraints satisfied:")
            for inputs, output in v.example_bank:
                print(f"{inputs}\t->\t{output}")
            constants = {}
            for variable in v.model.decls():
                constants[str(variable)] = z3_literal_to_python_literal(v.model.get_interp(variable))
            program = fill_holes(program, constants)
            if target_lang == "C":
                print(to_c(program, number_inputs=input_numbers, boolean_inputs=input_booleans))
            return program
        else:
            print(f"rejecting {program}")
    return None


def load_oracle(name: str) -> Oracle:
    env = importlib.import_module(f".oracles.{name}", "program_translation")
    for value in env.__dict__.values():
        try:
            if issubclass(value, Oracle):
                return value()
        except TypeError:
            pass
    raise ValueError(f"{name} in has no oracles")


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("oracle", help="name of oracle to use for synthesis", type=str)
    parser.add_argument(
        "-t",
        "--type",
        help="type of outputs from oracle",
        type=str,
        choices=["boolean", "number"],
        required=True,
    )
    parser.add_argument(
        "-ib",
        "--input-booleans",
        help="Boolean input names",
        nargs="+",
        type=str,
        default=[],
    )
    parser.add_argument(
        "-in",
        "--input-numbers",
        help="number input names",
        nargs="+",
        type=str,
        default=[],
    )
    parser.add_argument(
        "-cb",
        "--constant-booleans",
        help="constant Boolean names",
        nargs="+",
        type=str,
        default=[],
    )
    parser.add_argument(
        "-cn",
        "--constant-numbers",
        help="constant number names",
        nargs="+",
        type=str,
        default=[],
    )
    parser.add_argument(
        "-s",
        "--successes-to-pass",
        help="number of new examples to satisfy before accepting a program",
        type=int,
        default=20,
    )
    parser.add_argument(
        "-d",
        "--max-depth",
        help="maximum size of programs to generate before giving up",
        type=int,
        default=10,
    )
    args = parser.parse_args()

    target_type = (
        ir.BooleanExpression if args.type == "boolean" else ir.NumberExpression
    )
    oracle = load_oracle(args.oracle)

    program = synthesize(
        oracle,
        args.input_booleans,
        args.constant_booleans,
        args.input_numbers,
        args.constant_numbers,
        args.successes_to_pass,
        args.max_depth,
    )
