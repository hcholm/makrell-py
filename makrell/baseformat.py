from enum import Enum
import os
import typing as t
from makrell.ast import (
    BinOp, LPar, Node, Operator, RPar,
    RoundBrackets, Sequence, SquareBrackets, CurlyBrackets, String)
from makrell.parsing import Diagnostics, ErrorCodes, flatten, get_identifier, get_string
from makrell.tokeniser import regular, src_to_tokens


class ParseError(Exception):
    pass


class UncompleteError(Exception):
    pass


class Associativity(Enum):
    LEFT = 0
    RIGHT = 1


def e_string_to_baseformat(s: str) -> Node:
    """Parse a string with e-string expressions"""
    # parse "asd{2}qwe{2+3}zxc{2+{sum [3 5]}}{4}."
    segments = []
    from_ = 0
    i = 0
    nesting_level = 0

    while i < len(s):
        if s[i] == "{":
            if nesting_level == 0:
                segments.append(s[from_:i])
                from_ = i
            nesting_level += 1
        elif s[i] == "}":
            if nesting_level == 0:
                raise Exception("Unmatched closing bracket")
            nesting_level -= 1
            if nesting_level == 0:
                segments.append(s[from_:i + 1])
                from_ = i + 1
        i += 1
    if nesting_level != 0:
        raise Exception("Unmatched brackets")
    if from_ < len(s):
        segments.append(s[from_:])
    print("segments", segments)

    nodes = []
    for segment in segments:
        if segment.startswith("{") and segment.endswith("}"):
            segment = "{str " + segment[1:-1] + "}"
            n = src_to_baseformat(segment)[0]
        else:
            n = String('"' + segment + '"')
        if len(nodes) > 0:
            nodes.append(Operator("+"))
        nodes.append(n)

    print("estr nodes", regular(flatten(nodes)))
    # assert False
    return RoundBrackets(nodes)


def nodes_to_baseformat(nodes: list[Node], diag: Diagnostics | None = None) -> list[Node]:
    """Parse a token list into a tree of bracketed expressions"""
    diag = diag or Diagnostics()
    stack = []
    root = Sequence([])
    stack.append(root)
    current_list = root
    current_list._original_nodes = []

    for n in nodes:
        if isinstance(n, LPar):
            if n.value == "(":
                b = RoundBrackets([])
            elif n.value == "[":
                b = SquareBrackets([])
            elif n.value == "{":
                b = CurlyBrackets([])
            else:
                raise ParseError("Unknown opening bracket")
            current_list = b
            b._start_line = n._start_line
            b._start_column = n._start_column
            b._original_nodes = []
            stack.append(current_list)
        elif isinstance(n, RPar):
            ok_bracket = (
                (isinstance(current_list, RoundBrackets) and n.value == ")")
                or (isinstance(current_list, SquareBrackets) and n.value == "]")
                or (isinstance(current_list, CurlyBrackets) and n.value == "}"))
            if not ok_bracket:
                raise ParseError(f"Unmatched closing bracket {n.value} for {current_list.__class__.__name__}")
            b = stack.pop()
            b._end_line = n._end_line
            b._end_column = n._end_column
            current_list = stack[-1]
            sub_parsed = nodes_to_baseformat(b.nodes, diag)
            b.nodes = sub_parsed
            current_list.nodes.append(b)
            current_list._original_nodes.append(b)
        else:
            estr_expanded = n
            if get_string(n) is not None and n.suffix == "e":
                estr_expanded = e_string_to_baseformat(n.value[1:-1])
            current_list.nodes.append(estr_expanded)
            current_list._original_nodes.append(n)

    if len(stack) > 1:
        diag.error(ErrorCodes.INCOMPLETE_INPUT, "Unmatched opening bracket", stack[-1])

    return root.nodes


default_operator_precedences = {

    '=': (0, Associativity.RIGHT),

    '|': (20, Associativity.LEFT),
    '|*': (20, Associativity.LEFT),
    '\\': (20, Associativity.RIGHT),
    '*\\': (20, Associativity.RIGHT),

    '->': (30, Associativity.RIGHT),

    '||': (45, Associativity.LEFT),
    '&&': (45, Associativity.LEFT),

    '==': (50, Associativity.LEFT),
    '!=': (50, Associativity.LEFT),
    '<': (50, Associativity.LEFT),
    '>': (50, Associativity.LEFT),
    '<=': (50, Associativity.LEFT),
    '>=': (50, Associativity.LEFT),
    '~=': (50, Associativity.LEFT),
    '!~=': (50, Associativity.LEFT),

    '..': (90, Associativity.LEFT),
        
    '+': (110, Associativity.LEFT),
    '-': (110, Associativity.LEFT),

    '*': (120, Associativity.LEFT),
    '/': (120, Associativity.LEFT),
    '%': (120, Associativity.LEFT),

    '**': (130, Associativity.RIGHT),

    '@': (140, Associativity.LEFT),
    '.': (200, Associativity.LEFT)
}


def default_precedence_lookup(operator: str) -> tuple[int, Associativity]:
    return default_operator_precedences.get(operator, (0, Associativity.LEFT))


def operator_parse(nodes: list[Node],
                   precedence_lookup: t.Callable[[str], tuple[int, Associativity]]
                   = default_precedence_lookup) -> list[Node]:
    """Parse a list of (regular) nodes into a tree of binary operations"""

    output = []
    opstack = []
    last_wasnt_op = True

    def has_ops_on_stack():
        return len(opstack) > 0
          
    def apply_opstack(right: Node):
        left = output.pop()
        op = opstack.pop()
        binop = BinOp(left, op.value, right)
        binop._start_line = left._start_line
        binop._start_column = left._start_column
        binop._end_line = right._end_line
        binop._end_column = right._end_column
        output.append(binop)

    def apply_opstack_1():
        right = output.pop()
        apply_opstack(right)

    def apply_opstack_all():
        while has_ops_on_stack():
            apply_opstack_1()

    for n in nodes:
        n_is_operator = isinstance(n, Operator)

        if n_is_operator:
            current_prio, _ = precedence_lookup(n.value)
            if not has_ops_on_stack():
                opstack.append(n)
            else:
                while has_ops_on_stack():
                    stack_prio, stack_assoc = precedence_lookup(opstack[-1].value)
                    if stack_prio > current_prio:
                        apply_opstack_1()
                    elif stack_prio == current_prio and stack_assoc == Associativity.LEFT:
                        apply_opstack_1()
                    else:
                        break
                opstack.append(n)
            last_wasnt_op = False

        else:
            if last_wasnt_op:
                apply_opstack_all()
            output.append(n)
            last_wasnt_op = True

    apply_opstack_all()
    return output


def src_to_baseformat(src: str, diag: Diagnostics | None = None) -> list[Node]:
    tokens = src_to_tokens(src)
    parsed = nodes_to_baseformat(tokens, diag)
    return parsed


def file_to_baseformat(filename: str) -> list[Node]:
    with open(filename, encoding='utf-8') as f:
        src = f.read()
        return src_to_baseformat(src)


def include_includes(reference_path: str, nodes: list[Node]) -> list[Node]:
    """Include the contents of any include files"""
    reference_path = os.path.dirname(reference_path)

    def traverse(n: Node) -> Node | list[Node]:
        if isinstance(n, CurlyBrackets):
            ns = regular(n.nodes)
            if len(ns) >= 2 and get_identifier(ns[0], "$include"):
                filename = ns[1].value[1:-1]
                path = os.path.join(reference_path, filename)
                print(f"Include {reference_path} {filename} {path}")
                included = file_to_baseformat(path)
                included_recursed = include_includes(path, included)
                return flatten(included_recursed)
        return n

    traversed_nodes = flatten([traverse(n) for n in nodes])
    return traversed_nodes


def deparen(n: Node) -> Node:
    """Remove parentheses from a node"""
    if isinstance(n, RoundBrackets) and len(regular(n.nodes)) == 1:
        return deparen(n.nodes[0])
    return n
