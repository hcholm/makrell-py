import ast as py
import os
from typing import Any
from importlib import import_module
from makrell.ast import (Sequence, Node)
from makrell.baseformat import (
    operator_parse,
    src_to_baseformat, include_includes)
from makrell.tokeniser import regular
from makrell.parsing import (Diagnostics, flatten)
from ._compiler_common import stmt_wrap
from ._compile import (CompilerContext, compile_mr)


def import_mr_module(name: str, dest_module, alias: str | None = None) -> py.Module:
    m = import_module(name)
    if alias is not None:
        setattr(dest_module, alias, m)
    else:
        setattr(dest_module, name, m)
    
    cc = CompilerContext(compile_mr)
    run_core_mr(cc)
    pyast = cc.operator_parse(regular(src_to_baseformat(f"import {name}")))
    pyast = cc.fun_defs[0] + pyast
    m = py.Module(stmt_wrap(pyast, auto_return=False), type_ignores=[])
    py.fix_missing_locations(m)
    return m


def run_core_mr(cc: CompilerContext):
    core_mr = get_src("core.mrpy")
    cc.run(cc.operator_parse(regular(src_to_baseformat(core_mr))))
    patmatch_mr = get_src("patmatch.mrpy")
    cc.run(cc.operator_parse(regular(src_to_baseformat(patmatch_mr))))


def get_mr_meta_assignment(cc: CompilerContext) -> py.Assign | None:
    syms = cc.meta.node_blocks
    if len(syms) == 0:
        return None
    
    def sym_to_pa(sym: Node) -> py.expr:
        return py.Constant(str(sym))
    py_syms = [sym_to_pa(sym) for sym in syms]
    arr = py.List(py_syms, ctx=py.Load())
    ass = py.Assign([py.Name("_mr_meta_", py.Store())], arr)
    return ass


def get_mr_meta_code(cc: CompilerContext) -> list[Node]:
    syms = cc.meta.node_blocks
    return syms


def nodes_to_module(nodes: list[Node], cc: CompilerContext | None = None,
                    filename: str | None = None,
                    run_core: bool = True) -> py.Module:
    nodes = flatten(nodes)
    cc = cc or CompilerContext(compile_mr)
    if run_core:
        run_core_mr(cc)
        cc.meta.node_blocks.clear()
    pyast = flatten(compile_mr(Sequence(regular(nodes)), cc))
    if cc.diag.has_errors():
        msg = '\n'.join(i.message for i in cc.diag.items)
        raise Exception(msg)
    if not isinstance(pyast, list):
        pyast = [pyast]
    pyast = cc.fun_defs[0] + pyast

    ass = get_mr_meta_assignment(cc)
    if ass is not None:
        pyast.append(ass)

    m = py.Module(stmt_wrap(pyast, auto_return=False), type_ignores=[])
    py.fix_missing_locations(m)
    return m


def eval_nodes(ns: list[Node], cc: CompilerContext | None = None,
               globals_: dict[str, Any] | None = None,
               locals_: dict[str, Any] | None = None
               ) -> Any:
    if not isinstance(ns, list):
        ns = [ns]
    if len(ns) == 0:
        return None
    cc = cc or CompilerContext(compile_mr)
    run_core_mr(cc)
    pyast = [compile_mr(n, cc) for n in ns]
    if not isinstance(pyast, list):
        pyast = [pyast]
    pyast = cc.fun_defs[0] + pyast

    last_is_expr = isinstance(pyast[-1], py.expr)
    stmt_count = len(pyast) - (1 if last_is_expr else 0)
    glob = globals_ if globals_ is not None else globals()
    loc = locals_ if locals_ is not None else locals()

    # statements
    if stmt_count > 0:
        body = py.Module(stmt_wrap([pa for pa in pyast[:stmt_count]], auto_return=False), [])
        py.fix_missing_locations(body)
        c = compile(body, "", mode="exec")
        exec(c, glob, loc)

    if not last_is_expr:
        return None

    # return last node if expression
    last = pyast[-1]
    py.fix_missing_locations(last)
    # print(py.unparse(last))
    c = compile(py.Expression(last), "", mode="eval")
    r = eval(c, glob, loc)
    return r


def exec_nodes(nodes: list[Node], filename: str | None = None) -> Any:
    cc = CompilerContext(compile_mr)
    m = nodes_to_module(nodes, cc, filename)
    if filename is None:
        filename = "<string>"
    # TODO: cmd line option to print the generated code
    print(py.unparse(m))
    c = compile(m, filename, mode="exec")
    glob = {}
    init_py = \
        """import sys
sys.path.append('.')
"""
    exec(init_py, glob)
    exec(c, glob)
    return glob


def src_to_module(src: str, diag: Diagnostics | None = None) -> py.Module:
    parsed = src_to_baseformat(src, diag)
    return nodes_to_module(regular(parsed))


def eval_src(text: str,
             globals_: dict[str, Any] | None = None,
             locals_: dict[str, Any] | None = None
             ) -> Any:
    parsed = src_to_baseformat(text)
    opp = operator_parse(regular(parsed))
    r = eval_nodes(opp, None, globals_, locals_)
    return r


def exec_src(text: str, filename: str | None = None, globals_: dict[str, Any] | None = None) -> Any:
    parsed = src_to_baseformat(text)
    if filename is not None:
        parsed = include_includes(filename, parsed)
    return exec_nodes(regular(parsed), filename)


def exec_file(filename: str) -> Any:
    with open(filename, encoding='utf-8') as f:
        text = f.read()
    return exec_src(text, filename)


def get_src(filename: str):
    here_dir = os.path.dirname(os.path.abspath(__file__))
    core_mr_path = os.path.join(here_dir, filename)
    with open(core_mr_path, encoding='utf-8') as f:
        core_mr = f.read()
    return core_mr
