import argparse
import heapq as hq
from itertools import count
from typing import Hashable, Iterator, List, MutableSet, Tuple, Type, TypeVar, Union

from . import intermediate_representation as ir
from .ir_utilities import count_elements, count_nonterminals, deep_copy


def replace_one_nonterminal(
    expression: ir.Expression, numbers: List[str] = [], booleans: List[str] = []
) -> List[ir.Expression]:

    # Check to make sure that none of the number and Boolean variables share the same name.
    shared_names = set(numbers).intersection(booleans)
    if shared_names:
        raise RuntimeError(
            f"The following names are used for both numbers and Boolean holes: {shared_names}"
        )
    number_holes = [ir.NumberHole(name) for name in numbers]
    boolean_holes = [ir.BooleanHole(name) for name in booleans]

    # Make sure that there is at least one non-terminal to replace before proceeding.
    if count_nonterminals(expression) == 0:
        raise TypeError(f"expression {str(expression)} has no non-terminals")

    # Whether we have seen a non-terminal or not. If False, keep searching. If True, do nothing.
    seen_nonterminal = False

    # Once the first non-terminal is identified, this list will hold all of the things that can be derived from it using
    # the production rules. For example, if the nonterminal is an Expression, this will hold a NumberExpression and a
    # BooleanExpression.
    replacements = []

    # Holds a reference to the parent of the node with the first non-terminal as its child.
    parent_ref = None

    # The number of the attribute (e.g. 0 for "_0") that the non-terminal child is located at.
    child_index = None

    def maybe_do_replacement(self, expr) -> None:
        nonlocal seen_nonterminal, replacements, parent_ref, child_index

        # If we've already found a non-terminal, do nothing and don't go any deeper.
        if seen_nonterminal:
            return

        if type(expr) is ir.Expression:
            replacements = [ir.BooleanExpression(), ir.NumberExpression()]
            seen_nonterminal = True
        elif type(expr) is ir.BooleanExpression:
            replacements = [
                ir.Not(ir.BooleanExpression()),
                ir.And(ir.BooleanExpression(), ir.BooleanExpression()),
                ir.Or(ir.BooleanExpression(), ir.BooleanExpression()),
                ir.Xor(ir.BooleanExpression(), ir.BooleanExpression()),
                ir.Impl(ir.BooleanExpression(), ir.BooleanExpression()),
                ir.Lt(ir.NumberExpression(), ir.NumberExpression()),
            ] + boolean_holes
            seen_nonterminal = True
        elif type(expr) is ir.NumberExpression:
            replacements = [
                ir.Add(ir.NumberExpression(), ir.NumberExpression()),
                ir.Sub(ir.NumberExpression(), ir.NumberExpression()),
                ir.Mul(ir.NumberExpression(), ir.NumberExpression()),
                # ir.Div(ir.NumberExpression(), ir.NumberExpression()),
                ir.Ite(
                    ir.BooleanExpression(), ir.NumberExpression(), ir.NumberExpression()
                ),
            ] + number_holes
            seen_nonterminal = True
        elif type(expr) is ir.BooleanHole or type(expr) is ir.NumberHole:
            # This terminal case needs explicit handling because the hole types don't have "_<number>" attributes like
            # the rest of the terminals.
            return
        else:
            old_parent_ref, old_child_index = parent_ref, child_index
            parent_ref = expr
            for child_index in count(start=0):
                try:
                    self.visit(expr.__dict__[f"_{child_index}"])
                except (AttributeError, KeyError):
                    break
                if seen_nonterminal:
                    break
            if not seen_nonterminal:
                parent_ref, child_index = old_parent_ref, old_child_index

    replacer = ir.make_visitor("Replacer", {}, default_action=maybe_do_replacement)()
    replacer.visit(expression)

    # If the root node is a non-terminal, just return the replacement directly rather than trying to do substitutions in
    # the tree.
    if parent_ref is None:
        return replacements

    ret = []
    for replacement in replacements:
        parent_ref.__dict__[f"_{child_index}"] = replacement
        copy = deep_copy(expression)
        ret.append(copy)

    return ret


HPQData = TypeVar("HPQData", bound=Hashable)


class HashFilteredPQ:
    """
    A priority queue that uses a hash filter to prevent elements that have already been on the queue from re-entering
    it.
    """

    def __init__(self):
        self.seen_hashes: MutableSet[int] = set()
        self.queue: List[Tuple[int, int, HPQData]] = []

    def put(self, priority: int, data: HPQData) -> None:
        h = hash(data)
        if h not in self.seen_hashes:
            self.seen_hashes.add(h)
            hq.heappush(self.queue, (priority, id(data), data))

    def get(self) -> HPQData:
        _, _, top_element = hq.heappop(self.queue)
        return top_element

    def empty(self) -> bool:
        return self.queue == []


def enumerate_programs(
    target_type: Union[Type[ir.BooleanExpression], Type[ir.NumberExpression]],
    maximum_depth: int = 3,
    numbers: List[str] = [],
    booleans: List[str] = [],
) -> Iterator[ir.Expression]:
    queue = HashFilteredPQ()
    queue.put(1, target_type())
    while not queue.empty():
        current_element: ir.Expression = queue.get()
        if count_nonterminals(current_element) == 0:
            yield current_element
        else:
            derivatives = replace_one_nonterminal(
                current_element, numbers=numbers, booleans=booleans
            )
            for derivative in derivatives:
                d = count_elements(derivative)  # depth(derivative)
                if d <= maximum_depth:
                    queue.put(d, derivative)


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--type",
        help="type of the enumerated programs",
        type=str,
        choices=["boolean", "number"],
        required=True,
    )
    parser.add_argument(
        "-d",
        "--max-depth",
        help="maximum size of enumerated programs",
        type=int,
        default=3,
    )
    parser.add_argument(
        "-b",
        "--booleans",
        help="names of Boolean variables",
        nargs="+",
        type=str,
        default=[],
    )
    parser.add_argument(
        "-n",
        "--numbers",
        help="names of number variables",
        nargs="+",
        type=str,
        default=[],
    )
    args = parser.parse_args()

    target_type = (
        ir.BooleanExpression if args.type == "boolean" else ir.NumberExpression
    )
    for program in enumerate_programs(
        target_type, maximum_depth=args.max_depth, booleans=args.booleans, numbers=args.numbers  # type: ignore
    ):
        print(str(program))
