import ast as py
from enum import Enum
import math
from datetime import datetime
from typing import Any
import regex

from makrell.ast import (
    BinOp, CurlyBrackets, Identifier, LPar, Node, Number, Operator, ParseError, RPar,
    RoundBrackets, SquareBrackets, String, Whitespace, node_name)


rx_int = regex.compile(r'^-?\d+$')


def deescape(s: str) -> str:
    return s.replace(r'\"', '"')


def python_value(n: Node) -> Any:
    if isinstance(n, String):
        s = n.value[1:-1]
        match n.suffix:
            case "dt":
                return datetime.fromisoformat(s)
            case "bin":
                return int(s, 2)
            case "oct":
                return int(s, 8)
            case "hex":
                return int(s, 16)
            case "regex":
                return regex.compile(n.value)
            case _:
                return deescape(s)
    elif isinstance(n, Number):
        if rx_int.match(n.value):
            match n.suffix:
                case "k":
                    return int(n.value) * 1000
                case "M":
                    return int(n.value) * 1000000
                case "G":
                    return int(n.value) * 1000000000
                case "T":
                    return int(n.value) * 1000000000000
                case "P":
                    return int(n.value) * 1000000000000000
                case "E":
                    return int(n.value) * 1000000000000000000
                case "i":
                    return complex(0, float(n.value))
                case "e":
                    return math.e * float(n.value)
                case "tau":
                    return math.tau * float(n.value)
                case "deg":
                    return math.pi * float(n.value) / 180
                case "pi":
                    return math.pi * float(n.value)
                case "":
                    return int(n.value)
        else:
            match n.suffix:
                case "k":
                    return float(n.value) * 1000
                case "M":
                    return float(n.value) * 1000000
                case "G":
                    return float(n.value) * 1000000000
                case "T":
                    return float(n.value) * 1000000000000
                case "P":
                    return float(n.value) * 1000000000000000
                case "E":
                    return float(n.value) * 1000000000000000000
                case "i":
                    return complex(0, float(n.value))
                case "e":
                    return math.e * float(n.value)
                case "tau":
                    return math.tau * float(n.value)
                case "deg":
                    return math.pi * float(n.value) / 180
                case "pi":
                    return math.pi * float(n.value)
                case "":
                    return float(n.value)
    else:
        # raise ValueError(f"Can't convert {n} to python value")
        return None


def baseformat_value(n: Node) -> Node:
    if isinstance(n, String):
        pv = python_value(n)
        if pv is not None:
            return pv
    elif isinstance(n, Number):
        pv = python_value(n)
        if pv is not None:
            return pv
    return n


def pyast_value(n: Node) -> py.AST | None:
    # print("pyast_value", n)
    if get_string(n):
        s = n.value[1:-1]  # type: ignore
        match n.suffix:  # type: ignore
            case "regex":
                return py.Constant(regex.compile(s))
    pv = python_value(n)
    if not pv:
        return None
        # raise ValueError(f"Can't convert {n} to python value")
    return py.Constant(python_value(n))


def flatten(a: list) -> list:
    """recursively flatten a list"""
    if not isinstance(a, list):
        return [a]
    result = []
    for x in a:
        result.extend(flatten(x))
    return result


def pairwise(ns: list[Node]) -> list[tuple[Node, Node]]:
    if len(ns) % 2 != 0:
        raise Exception("Odd number of tokens")
    return [(ns[i], ns[i + 1]) for i in range(0, len(ns), 2)]


def not_found_error(expected: Node | type, val: str | None, found: Node) -> ParseError:
    expected_descr = node_name(expected)
    if val is not None:
        expected_descr += f" with value {val}"
    pos = found.pos_str()
    found_value = None
    if isinstance(found, Identifier):
        found_value = found.value
    elif isinstance(found, String):
        found_value = found.value
    found_descr = f"{node_name(found)} with value {found_value}"
    return ParseError(f"Expected {expected_descr} at {pos}, found {found_descr}")


def get_identifier(n: Node, wanted_value: str | None = None, require: bool = False) -> Identifier | None:
    if not isinstance(n, Identifier) or (wanted_value is not None and n.value != wanted_value):
        if require:
            raise not_found_error(Identifier, wanted_value, n)
        return None
    return n


def get_operator(n: Node, wanted_value: str | None = None, require: bool = False) -> Operator | None:
    if not isinstance(n, Operator) or (wanted_value is not None and n.value != wanted_value):
        if require:
            raise not_found_error(Operator, wanted_value, n)
        return None
    return n


def get_string(n: Node, require: bool = False) -> String | None:
    if not isinstance(n, String):
        if require:
            raise not_found_error(String, None, n)
        return None
    return n


def get_number(n: Node, require: bool = False) -> Number | None:
    if not isinstance(n, Number):
        if require:
            raise not_found_error(Number, None, n)
        return None
    return n


def get_binop(n: Node, wanted_value: str | None = None, require: bool = False) -> BinOp | None:
    if not isinstance(n, BinOp) or (wanted_value is not None and n.op != wanted_value):
        if require:
            raise not_found_error(BinOp, wanted_value, n)
        return None
    return n


def is_tuple(n: Node) -> bool:
    return (isinstance(n, RoundBrackets) and len(n.nodes) > 1)


def assert_tuple(n: RoundBrackets) -> RoundBrackets:
    if not is_tuple(n):
        raise Exception(f"Expected tuple, got: {n}")
    if len(n) == 2 and get_identifier(n[1], "_"):
        return RoundBrackets([n[0]])
    return n


def get_left_bracket(n: Node, wanted_value: str | None = None, require: bool = False) -> LPar | None:
    if not isinstance(n, LPar) or (wanted_value is not None and n.value != wanted_value):
        if require:
            raise not_found_error(LPar, wanted_value, n)
        return None
    return n


def get_right_bracket(n: Node, wanted_value: str | None = None, require: bool = False) -> RPar | None:
    if not isinstance(n, RPar) or (wanted_value is not None and n.value != wanted_value):
        if require:
            raise not_found_error(RPar, wanted_value, n)
        return None
    return n


def get_round_brackets(n: Node, require: bool = False) -> RoundBrackets | None:
    if not isinstance(n, RoundBrackets):
        if require:
            raise not_found_error(RoundBrackets, None, n)
        return None
    return n


def get_curly_brackets(n: Node, require: bool = False) -> CurlyBrackets | None:
    if not isinstance(n, CurlyBrackets):
        if require:
            raise not_found_error(CurlyBrackets, None, n)
        return None


def get_curly(n: Node, ident: str, require: bool = False) -> CurlyBrackets | None:
    if (not isinstance(n, CurlyBrackets)
            or len(n.nodes) < 1
            or not get_identifier(n.nodes[0], ident, require)):
        if require:
            raise not_found_error(CurlyBrackets, None, n)
        return None
    return n


def get_square_brackets(n: Node, require: bool = False) -> SquareBrackets | None:
    if not isinstance(n, SquareBrackets):
        if require:
            raise not_found_error(SquareBrackets, None, n)
        return None
    return n


class NodeReader:
    def __init__(self, nodes: list[Node]):
        self.nodes = nodes
        self.pos = 0

    @property
    def end_of_list(self) -> bool:
        return self.pos >= len(self.nodes)
    
    @property
    def has_more(self) -> bool:
        return not self.end_of_list

    def peek(self, offset: int = 1) -> Node | None:
        if offset < 1:
            raise Exception("Can't peek backwards")
        if self.pos + offset > len(self.nodes):
            return None
        return self.nodes[self.pos]

    def read(self) -> Node | None:
        if self.end_of_list:
            return None
        n = self.nodes[self.pos]
        self.pos += 1
        return n
    
    def skip_whitespace(self):
        while True:
            if self.end_of_list:
                return
            next = self.peek()
            if not isinstance(next, Whitespace):
                return
            self.read()
    
    def pushback(self, count: int = 1):
        if self.pos < count:
            raise Exception("Can't pushback that much")
        self.pos -= count


class DiagnosticSeverity(Enum):
    Hint = 0
    Info = 1
    Warning = 2
    Error = 3


class ErrorCodes:
    OTHER = 0
    INCOMPLETE_INPUT = 1


class DiagnosticItem:
    
    def __init__(self, severity: DiagnosticSeverity, code: int, message: str, node: Node | None = None):
        self.code = code
        self.severity = severity
        self.message = message
        self.node = node


class Diagnostics:

    def __init__(self):
        self.items: list[DiagnosticItem] = []

    def add(self, severity: DiagnosticSeverity, code: int, message: str, node: Node | None = None):
        if node:
            message = f"{message} at {node.pos_str()}"
        self.items.append(DiagnosticItem(severity, code, message, node))

    def error(self, code: int, message: str, node: Node | None = None):
        self.add(DiagnosticSeverity.Error, code, message, node)

    def warning(self, code: int, message: str, node: Node | None = None):
        self.add(DiagnosticSeverity.Warning, code, message, node)

    def info(self, code: int, message: str, node: Node | None = None):
        self.add(DiagnosticSeverity.Info, code, message, node)

    def hint(self, code: int, message: str, node: Node | None = None):
        self.add(DiagnosticSeverity.Hint, code, message, node)

    def has_errors(self) -> bool:
        return any([i.severity == DiagnosticSeverity.Error for i in self.items])
    
    def has_warnings(self) -> bool:
        return any([i.severity == DiagnosticSeverity.Warning for i in self.items])
    
    def clear(self):
        self.items.clear()

    @property
    def is_incomplete(self) -> bool:
        return any([i.code == ErrorCodes.INCOMPLETE_INPUT for i in self.items])
    
