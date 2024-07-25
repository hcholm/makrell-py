import ast as py
from makrell.ast import (
    BinOp, Identifier, Number, Sequence, CurlyBrackets, Node, RoundBrackets,
    SquareBrackets, String)
from makrell.baseformat import (Associativity, operator_parse)
from makrell.makrellpy._compile_curly_reserved import compile_curly_reserved
from makrell.makrellpy._compiler_common import CompilerContext
from makrell.tokeniser import regular
from makrell.parsing import (get_binop, get_operator, python_value, get_identifier)
from .py_primitives import simple_reserved
from ._compile_binop import compile_binop
from ._compiler_common import transfer_pos


def compile_mr(n: Node, cc: CompilerContext) -> py.AST | list[py.AST] | None:

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

    # curly brackets
    def curly(n: CurlyBrackets) -> py.AST | list[py.AST] | None:
        nodes = n.nodes
        if len(nodes) == 0:
            return py.Constant(None)

        n0 = nodes[0]
        reg_nodes = regular(nodes)

        # operator as function call
        if get_operator(reg_nodes[0]):
            # TODO: more arguments
            if len(reg_nodes) == 1:
                argname1 = "$left"
                argname2 = "$right"
                args = [py.arg(argname1), py.arg(argname2)]
                body = c(BinOp(Identifier(argname1), reg_nodes[0].value, Identifier(argname2)))
            elif len(reg_nodes) == 2:
                argname1 = "$left"
                args = [py.arg(argname1)]
                body = c(BinOp(reg_nodes[1], reg_nodes[0].value, Identifier(argname1)))
            else:
                raise Exception(f"Invalid number of arguments to operator: {len(reg_nodes)}")
            arguments = py.arguments(args=args, posonlyargs=[], kwonlyargs=[],
                                     kw_defaults=[], defaults=[])
            r = py.Lambda(arguments, body)
            return r

        opp_nodes = cc.operator_parse(reg_nodes)
        opp_n0 = opp_nodes[0]

        if get_identifier(n0):
            # reserved word
            r = compile_curly_reserved(n, cc, compile_mr, opp_nodes)
            if r:
                return r
            
            # meta symbol call
            if n0.value in cc.meta.symbols:
                if len(nodes) <= 2:  # whitespace after identifier
                    meta_args = []
                else:
                    meta_args = nodes[2:]
                result = cc.meta.symbols[n0.value](meta_args)
                if isinstance(result, Node):
                    return c(result)
                return [c(n) for n in regular(result)]

            if get_identifier(opp_n0):
                # function call, identifier
                f = py.Name(opp_n0.value, py.Load())
                transfer_pos(opp_n0, f)
            else:
                # ?
                f = c(opp_n0)
        else:
            # function call, non-identifier
            f = c(opp_n0)
            transfer_pos(opp_n0, f)
        args = []
        kw_args = []
        lambda_args = []

        # function call arguments
        for n in opp_nodes[1:]:
            if get_binop(n, "="):
                # keyword argument
                kw_args.append(py.keyword(n.left.value, c(n.right)))
            # partial application, becomes a lambda
            elif get_identifier(n, "_"):
                sym = cc.gensym()
                name = py.Name(sym, py.Load())
                transfer_pos(n, name)
                args.append(name)
                lambda_args.append(py.arg(sym))
            else:
                args.append(c(n))
        if lambda_args:
            arguments = py.arguments(args=lambda_args, posonlyargs=[], kwonlyargs=[],
                                     kw_defaults=[], defaults=[])
            return py.Lambda(arguments, py.Call(f, args, []))
        else:
            return py.Call(f, args, kw_args)

    # entry point
    match n:
        case Identifier(value):
            r = simple_reserved(value)
            if r:
                # reserved word
                return r
            if value in cc.meta.symbols:
                # meta identifier
                return c(cc.meta.symbols[value])
            # regular identifier
            return py.Name(value, py.Load())
            
        case String():
            # string constant, bin/oct/hex number, regex, datetime
            n._type = Identifier("str")
            return py.Constant(python_value(n))
        
        case Number():
            # numeric constant
            value = python_value(n)
            n._type = Identifier("int" if isinstance(value, int) else "float")
            return py.Constant(python_value(n))
                       
        case BinOp(left, op, right):
            return compile_binop(n, cc, compile_mr)
        
        case RoundBrackets(nodes):
            nodes = cc.operator_parse(regular(nodes))
            if len(nodes) == 0:
                # () is null
                return py.Constant(None)
            if len(nodes) == 1:
                # (x) is x
                return c(nodes[0])
            else:
                # (x …) is a tuple
                last_is_dummy = get_identifier(nodes[-1], "_")
                ns = nodes[:-1] if last_is_dummy else nodes
                return py.Tuple([c(n) for n in ns], ctx=py.Load())
        
        case SquareBrackets(nodes):
            return py.List([c(n) for n in cc.operator_parse(regular(nodes))], ctx=py.Load())
        
        case CurlyBrackets(nodes):
            return curly(n)
        
        case Sequence(nodes):
            if len(nodes) == 0:
                return py.Constant(None)
            if len(nodes) == 1:
                return c(nodes[0])
            else:
                return [c(n) for n in cc.operator_parse(nodes)]
            
    raise Exception(f"Unknown type: {type(n)}")
