import ast as py
from importlib import import_module
from typing import Any
from makrell.ast import (
    BinOp, Identifier, Number, Sequence, CurlyBrackets, Node, RoundBrackets,
    SquareBrackets, String)
from makrell.baseformat import (
    Associativity, ParseError, default_precedence_lookup, deparen, operator_parse, src_to_baseformat)
from makrell.tokeniser import regular
from makrell.parsing import (
    Diagnostics, get_binop, get_curly, get_operator, get_square_brackets, python_value, flatten, get_identifier)
from .py_primitives import bin_ops, bool_ops, compare_ops, simple_reserved


def ensure_stmt(pa: py.AST) -> py.AST:
    if isinstance(pa, py.stmt):
        return pa
    e = py.Expr(pa)
    if "lineno" not in pa.__dict__:  # macro nodes don't have position info, TODO: fix
        return e
    e.lineno = pa.lineno
    e.col_offset = pa.col_offset
    e.end_lineno = pa.end_lineno
    e.end_col_offset = pa.end_col_offset
    return e


def stmt_wrap(ns: list[py.AST], auto_return: bool = True) -> list[py.AST]:
    if ns == []:
        return [py.Return(py.Constant(None))]
    return [
        py.Return(n) if auto_return and i == len(ns) - 1 and isinstance(n, py.expr) else
        ensure_stmt(n)
        for i, n in enumerate(ns)
    ]


def dotted_ident(n: Node) -> str:
    if get_identifier(n):
        return n.value
    elif isinstance(n, BinOp) and n.op == ".":
        return dotted_ident(n.left) + "." + dotted_ident(n.right)
    else:
        raise Exception(f"Invalid identifier: {n}")


class CompilerContext:
    def __init__(self):
        self.gensym_counter = 0
        self.fun_defs = []
        self.operators = {}
        self.meta = Meta(self)
        self.body_stack = []
        self.diag: Diagnostics = Diagnostics()

    def gensym(self) -> str:
        self.gensym_counter += 1
        return f"__gensym_{self.gensym_counter}__"

    def op_precedence(self, op: str) -> tuple[int, Associativity]:
        if op in self.operators:
            return self.operators[op]
        return default_precedence_lookup(op)

    def operator_parse(self, nodes: list[Node]) -> list[Node]:
        return operator_parse(regular(nodes), self.op_precedence)

    def import_with_mr_meta(self, src_module, names, dest_module):
        src_meta = src_module.__dict__.get("_mr_meta_", None)
        for src in src_meta:
            bf = src_to_baseformat(src)
            self.meta.run(bf)

    def run(self, nodes: list[Node]) -> Any:
        pyast = compile_mr(Sequence(nodes), self)
        if not isinstance(pyast, list):
            pyast = [pyast]
        pyast = self.fun_defs + pyast
        body = py.Module(stmt_wrap(pyast, auto_return=False), type_ignores=[])
        py.fix_missing_locations(body)
        c = compile(body, "", mode="exec")
        exec(c, {}, {})
    
    def push_body_block(self, body: list[py.AST]):
        self.body_stack.append(body)

    def pop_body_block(self) -> list[py.AST]:
        return self.body_stack.pop()
    
    def add_to_body_block(self, node: py.AST):
        self.body_stack[-1].append(node)


class Meta:
    def __init__(self, cc: CompilerContext):
        self.globals = {'$context': cc}
        self.symbols = {}
        self.node_blocks = []
        self.cc: CompilerContext = cc
        self._instance = None

        src_init = """
from makrell.ast import *
from makrell.tokeniser import regular
from makrell.baseformat import operator_parse, src_to_baseformat
"""
        exec(src_init, self.globals)

    def run(self, nodes: list[Node]) -> Any:
        self.node_blocks += nodes
        pyast = compile_mr(Sequence(nodes), self.cc)
        if not isinstance(pyast, list):
            pyast = [pyast]
        pyast = self.cc.fun_defs + pyast
        body = py.Module(stmt_wrap(pyast, auto_return=False), type_ignores=[])
        py.fix_missing_locations(body)
        c = compile(body, "", mode="exec")
        exec(c, self.globals, self.symbols)

    def quote(self, n: Node, raw: bool = False) -> Node:
        # TODO: cleanup raw usage
        match n:
            case CurlyBrackets(nodes) if (get_identifier(nodes[0], "unquote")
                                          or get_identifier(nodes[0], "$")):
                unquoted = self.cc.operator_parse(regular(nodes[1:]))
                return unquoted[0]
            case False:
                return Identifier("false")
            case True:
                return Identifier("true")
            case None:
                return Identifier("null")
            case Node():
                name = n.__class__.__name__
                args = [self.quote(v) for (k, v) in n.__dict__.items()
                        if not k.startswith("_")]
                ident = Identifier(name)
                cb = CurlyBrackets([ident, *args])
                cb._original_nodes = args
                return cb
            case list(ns):
                if not raw:
                    ns = regular(ns)
                return SquareBrackets([self.quote(n) for n in ns])
            case s if isinstance(n, str):
                return String('"' + s + '"')
            case n if isinstance(n, int):
                return Number(str(n))
        self.cc.diag.error(f"Invalid node to quote: {n}")


def transfer_pos(n: Node, pa: py.AST) -> py.AST:
    try:
        pa.lineno = n._start_line
        pa.col_offset = n._start_column
        pa.end_lineno = n._end_line
        pa.end_col_offset = n._end_column
    except AttributeError:
        pass
    return pa
