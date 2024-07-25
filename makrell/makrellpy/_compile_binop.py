import ast as py
from makrell.ast import (BinOp, Identifier, Sequence, Node)
from makrell.baseformat import (ParseError, deparen)
from makrell.makrellpy._compiler_common import stmt_wrap, transfer_pos
from makrell.tokeniser import regular
from makrell.parsing import (get_binop, get_square_brackets, get_identifier)
from .py_primitives import bin_ops, bool_ops, compare_ops


def compile_binop(n: BinOp, cc, compile_mr) -> py.AST | list[py.AST] | None:
    left = n.left
    right = n.right
    op = n.op

    # recurse through this
    def c(n: Node) -> py.expr:  # py.AST | list[py.AST] | None:
        pa = compile_mr(n, cc)
        if pa is not None:
            if isinstance(pa, list):
                for p in pa:
                    transfer_pos(n, p)
            else:
                transfer_pos(n, pa)
        return pa  # type: ignore

    def mr_binop(left: Node, op: str, right: Node) -> py.AST | list[py.AST] | None:

        if op in cc.meta.symbols:
            mop = cc.meta.symbols[op]  # lambda
            return py.Call(mop, [c(left), c(right)], [])

        match op:
            case "->":
                name = cc.gensym()
                if aid := get_identifier(left):
                    a = [py.arg(aid.value)]
                elif asb := get_square_brackets(left):
                    a = [py.arg(n.value) for n in regular(asb.nodes)]
                else:
                    raise Exception(f"Invalid left side of ->: {left}")
                args = py.arguments(args=a, posonlyargs=[], kwonlyargs=[], kw_defaults=[],
                                    defaults=[])
                if isinstance(right, Sequence) and len(right.nodes) > 1 and get_identifier(right.nodes[0], "do"):
                    rnodes = regular(right.nodes)
                    body = stmt_wrap([c(n) for n in cc.operator_parse(rnodes[1:])])
                    f = py.FunctionDef(name, args, body, [])
                    cc.fun_defs.append(f)
                    return py.Name(name, py.Load())
                else:
                    return py.Lambda(args, c(right))

            case "@":
                right = deparen(right)
                if get_binop(right, ".."):
                    slice = c(right)
                    s = py.Subscript(c(left), py.Slice(slice), py.Load())
                else:
                    s = py.Subscript(c(left), c(right), py.Load())
                return s
            
            case "..":
                return py.Slice(c(left), c(right), None)
            
            case ".":
                return py.Attribute(c(left), right.value, py.Load())
            
            case "=":
                c_left = c(left)
                c_left.ctx = py.Store()
                return py.Assign([c_left], c(right))
            
            case "|":
                return py.Call(c(right), [c(left)], [])
            
            case "|*":
                map_name = py.Name("map", py.Load())
                values = c(left)
                f = c(right)
                return py.Call(map_name, [f, values], [])
            
            case "\\":
                return py.Call(c(left), [c(right)], [])
            
            case "*\\":
                map_name = py.Name("map", py.Load())
                values = c(right)
                f = c(left)
                return py.Call(map_name, [f, values], [])
            
            case "~=" | "!~=":
                py_value = c(left)
                py_pattern = c(cc.meta.quote(right))
                # call_func = py.Name("makrell.makrellpy.patmatch.match", py.Load())
                call_func = py.Name("match", py.Load())
                r = py.Call(call_func, [py_value, py_pattern], [])
                if op == "!~=":
                    r = py.UnaryOp(py.Not(), r)
                return r

            case _:
                return None

    # python operator
    if op in bin_ops:
        return py.BinOp(c(left), bin_ops[op], c(right))
    elif op in bool_ops:
        n._type = Identifier("bool")
        return py.BoolOp(bool_ops[op], [c(left), c(right)])
    elif op in compare_ops:
        return py.Compare(c(left), [compare_ops[op]], [c(right)])
    elif op in cc.operators:
        # makrell operator
        return mr_binop(left, op, right)
    else:
        # ?
        r = mr_binop(left, op, right)
        if r:
            return r
        raise ParseError(f"Unknown operator: {op}")
