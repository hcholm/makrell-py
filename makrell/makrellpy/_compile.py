import ast as py
from makrell.ast import (
    BinOp, Identifier, Number, Sequence, CurlyBrackets, Node, RoundBrackets,
    SquareBrackets, String)
from makrell.makrellpy._compile_curly_reserved import compile_curly_reserved
from makrell.makrellpy._compiler_common import CompilerContext
from makrell.tokeniser import regular
from makrell.parsing import (get_binop, get_operator, python_value, get_identifier)
from .py_primitives import simple_reserved
from ._compile_binop import compile_binop
from ._compiler_common import transfer_pos
import makrell.makrellpy.pyast_builder as pb


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
        return pa

    def mr_binop(left: Node, op: str, right: Node) -> py.AST | list[py.AST] | None:
        if op in cc.meta.symbols:
            mop = cc.meta.symbols[op]  # lambda
            return py.Call(mop, [c(left), c(right)], [])

        match op:
            case "->":
                name = cc.gensym()
                if get_identifier(left):
                    a = [py.arg(left.value)]
                elif get_square_brackets(left):
                    a = [py.arg(n.value) for n in regular(left.nodes)]
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

            case _:
                return None

    # reserved words, special forms
    def mr_curly_reserved(original: Node, nodes: list[Node]) -> py.AST | list[py.AST] | None:
        nodes = regular(nodes)
        n0: Identifier = nodes[0]  # type: ignore
        if not get_identifier(n0):
            return None
        parlen = len(nodes) - 1

        match n0.value:
            case "not":
                if parlen == 1:
                    return py.UnaryOp(py.Not(), c(nodes[1]))
                else:
                    raise Exception(f"Invalid number of arguments to not: {parlen}")
                
            case "if":
                if parlen == 2:
                    return py.IfExp(c(nodes[1]), c(nodes[2]), py.Constant(None))
                elif parlen == 3:
                    return py.IfExp(c(nodes[1]), c(nodes[2]), c(nodes[3]))
                else:
                    cc.diag.error(0, f"Invalid number of arguments to if: {parlen}", n0)
                    return None
                
            case "when":
                body = stmt_wrap([c(n) for n in regular(nodes[2:])], auto_return=False)
                return py.If(c(nodes[1]), body, [])

            case "while":
                if parlen >= 2:
                    test = c(nodes[1])
                    body = stmt_wrap([c(n) for n in regular(nodes[2:])], auto_return=False)
                    return py.While(test, body, [])
                else:
                    cc.diag.error(0, f"Invalid number of arguments to while: {parlen}", n0)
                    return None
                
            case "async":
                if parlen < 2:
                    cc.diag.error(0, f"Invalid number of arguments to async: {parlen}", n0)
                    return None
                if get_identifier(nodes[1], "fun"):
                    if parlen < 3:
                        cc.diag.error(0, f"Invalid async function definition: {parlen}", n0)
                        return None
                    name = nodes[2].value
                    args_node = get_square_brackets(nodes[3]) or RoundBrackets([])
                    args = py.arguments(
                        args=[py.arg(n.value) for n in regular(args_node.nodes)],
                        posonlyargs=[], kwonlyargs=[], kw_defaults=[], defaults=[]
                    )
                    body = stmt_wrap([c(n) for n in regular(nodes[4:])])
                    return py.AsyncFunctionDef(
                        name=name, args=args, body=body, decorator_list=[]
                    )
                elif get_identifier(nodes[1], "for"):
                    if parlen < 3:
                        cc.diag.error(0, f"Invalid async for: {parlen}", n0)
                        return None
                    target = c(nodes[2])
                    target.ctx = py.Store()
                    itr = c(nodes[3])
                    body = stmt_wrap([c(n) for n in regular(nodes[4:])], auto_return=False)
                    return py.AsyncFor(target, itr, body, [])
                elif get_identifier(nodes[1], "with"):
                    if parlen < 3:
                        cc.diag.error(0, f"Invalid async with: {parlen}", n0)
                        return None
                    item_expr = c(nodes[2])
                    item_var_name = get_identifier(nodes[3]).value if parlen >= 3 else cc.gensym()
                    item_var = py.Name(item_var_name, py.Store())
                    body = stmt_wrap([c(n) for n in regular(nodes[4:])], auto_return=False)
                    return py.AsyncWith([py.withitem(item_expr, item_var)], body)
                else:
                    cc.diag.error(0, f"Unknown async construct: {nodes[1]}", nodes[1])
                    return None

            case "await":
                if parlen == 1:
                    return py.Await(c(nodes[1]))
                else:
                    cc.diag.error(0, f"Invalid number of arguments to await: {parlen}", n0)
                    return None
                
            case "fun":
                if parlen >= 2:
                    name = nodes[1].value
                    args = py.arguments(args=[py.arg(n.value) for n in regular(nodes[2])],
                                        posonlyargs=[], kwonlyargs=[], kw_defaults=[], defaults=[])
                    body = stmt_wrap([c(n) for n in regular(nodes[3:])])
                    return py.FunctionDef(name=name, args=args, body=body, decorator_list=[])
                else:
                    cc.diag.error(0, f"Invalid number of arguments to fun: {parlen}", n0)
                    return None
                
            case "class":
                if len(nodes) < 1:
                    raise Exception(f"Invalid number of arguments to class: {parlen}")
                name = get_identifier(nodes[1], require=True).value
                bases = []
                keywords = []
                body = []
                if len(nodes) >= 3:
                    params_sb = get_square_brackets(nodes[2])
                    if params_sb is None:
                        body = [c(n) for n in nodes[2:]]
                    else:
                        params = operator_parse(params_sb.nodes)
                        for p in params:
                            if ident := get_identifier(p):
                                n = py.Name(ident.value, py.Load())
                                # transfer_pos(ident, n)
                                bases.append(n)
                            elif at := get_binop(p, "."):
                                bases.append(c(at))
                            elif kw := get_binop(p, "="):
                                ident = get_identifier(kw.left, require=True)
                                val = c(kw.right)
                                keywords.append(py.keyword(ident.value, val))
                        body = [c(n) for n in nodes[3:]]
                if not body:
                    # empty class
                    body = [py.Pass()]
                cd = py.ClassDef(name, bases, keywords, body, [])
                return cd
                
            case "for":
                match nodes:
                    case [_, _, *stmts]:
                        target = c(nodes[1])
                        target.ctx = py.Store()
                        itr = c(nodes[2])
                        body = stmt_wrap([c(n) for n in regular(stmts)], auto_return=False)
                        return py.For(target, itr, body, [])
                    case _:
                        cc.diag.error(0, f"Invalid number of arguments to for: {parlen}", n0)
                        return None
                
            case "import" | "importm":
                importm = n0.value == "importm"
                                 
                imports_names = []
                import_from_names = []
                for n in nodes[1:]:
                    if get_identifier(n):
                        imports_names.append(n.value)
                    elif get_binop(n, "."):
                        name = dotted_ident(n)
                        imports_names.append(name)
                    elif get_binop(n, "@"):
                        name = dotted_ident(n.left)
                        rights = regular(n.right.nodes)
                        aliases = [r.value for r in rights]
                        import_from_names.append((name, aliases))
                implib = py.Import([py.alias("importlib")])

                def make_import(name: str) -> py.Import:
                    return py.Import([py.alias(name)])

                if importm:
                    for module, names in import_from_names:
                        cc.import_with_mr_meta(
                            import_module(module), names, cc.meta.symbols)
                    return py.Pass()

                def make_import_from(module: str, names: list[str]) -> py.ImportFrom:
                    return py.ImportFrom(module, [py.alias(n) for n in names], 0)
                
                imports = [make_import(n) for n in imports_names]
                import_froms = flatten([
                    make_import_from(module, names) for module, names in import_from_names])
                imps = flatten([implib] + imports + import_froms)
                        
                return imps
            
            case "include":
                if parlen == 1:
                    path = nodes[1].value[1:-1]
                    with open(path, encoding="utf-8") as f:
                        src = f.read()
                    ns = regular(bracket_parse(src))
                    return c(Sequence(ns))

            case "return":
                if parlen == 0:
                    return py.Return(py.Constant(None))
                elif parlen == 1:
                    return py.Return(c(nodes[1]))
                else:
                    cc.diag.error(0, f"Invalid number of arguments to return: {parlen}", n0)
                    return None
                
            case "yield":
                if parlen == 1:
                    return py.Yield(py.Constant(None))
                elif parlen == 2:
                    return py.Yield(c(nodes[1]))
                else:
                    cc.diag.error(0, f"Invalid number of arguments to yield: {parlen}", n0)
                    return None
                
            case "yieldfrom":
                if parlen == 2:
                    return py.YieldFrom(c(nodes[1]))
                else:
                    cc.diag.error(0, f"Invalid number of arguments to yieldfrom: {parlen}", n0)
                    return None
                
            case "raise":
                if parlen == 1:
                    return py.Raise(None, None, None)
                elif parlen == 2:
                    return py.Raise(c(nodes[1]), None, None)
                elif parlen == 3:
                    return py.Raise(c(nodes[1]), c(nodes[2]), None)
                elif parlen == 4:
                    return py.Raise(c(nodes[1]), c(nodes[2]), c(nodes[3]))
                else:
                    raise Exception(f"Invalid number of arguments to raise: {parlen}")
                
            case "try":
                body, handlers, orelse, finalbody = [], [], [], []
                body_ended = False
                for n in nodes[1:]:
                    if get_curly(n, "catch"):
                        nnodes = operator_parse(regular(n.nodes))
                        if len(nnodes) == 1:
                            # bare catch
                            exnodes = stmt_wrap([c(n) for n in nnodes[1:]], auto_return=False)
                            eh = py.ExceptHandler(None, None, exnodes)
                            handlers.append(transfer_pos(n, eh))
                        else:
                            if get_binop(nnodes[1], ":"):
                                # catch with name and type
                                name = nnodes[1].left.value
                                typ = c(nnodes[1].right)
                            else:
                                # catch with name
                                name = None
                                typ = c(nnodes[1])
                            exnodes = stmt_wrap([c(n) for n in nnodes[2:]], auto_return=False)
                            if not exnodes:
                                exnodes = [py.Pass()]
                            eh = py.ExceptHandler(typ, name, exnodes)
                            handlers.append(transfer_pos(n, eh))
                    elif get_curly(n, "finally"):
                        nnodes = operator_parse(regular(n.nodes))
                        finalbody += stmt_wrap([c(fn) for fn in nnodes[1:]], auto_return=False)
                        body_ended = True
                    elif get_curly(n, "else"):
                        nnodes = operator_parse(regular(n.nodes))
                        orelse += [c(fn) for fn in nnodes[1:]]
                        body_ended = True
                    else:
                        if body_ended:
                            raise Exception(f"Invalid statement after except/else/finally: {n}")
                        body.append(c(n))
                if handlers == [] and finalbody == []:
                    handlers.append(py.ExceptHandler(None, None, [py.Pass()]))
                body = stmt_wrap(body, auto_return=False)
                return py.Try(body, handlers, orelse, finalbody)
            
            case "with":
                if parlen < 2:
                    raise Exception(f"Invalid number of arguments to with: {parlen}")
                item_expr = c(nodes[1])
                item_var_name = get_identifier(nodes[2]).value
                item_var = py.Name(item_var_name, py.Store())
                body = stmt_wrap([c(n) for n in regular(nodes[3:])], auto_return=False)
                w = py.With([py.withitem(item_expr, item_var)], body)
                return w

            case "del":
                if parlen == 1:
                    return py.Delete([c(nodes[1])])
                else:
                    raise Exception(f"Invalid number of arguments to del: {parlen}")
                
            case "assert":
                if parlen == 1:
                    return py.Assert(c(nodes[1]), None)
                elif parlen == 2:
                    return py.Assert(c(nodes[1]), c(nodes[2]))
                else:
                    raise Exception(f"Invalid number of arguments to assert: {parlen}")
                
            case "pass":
                if parlen == 0:
                    return py.Pass()
                else:
                    raise Exception(f"Invalid number of arguments to pass: {parlen}")
                
            case "break":
                if parlen == 0:
                    return py.Break()
                
            case "continue":
                if parlen == 0:
                    return py.Continue()
                
            case "global":
                if parlen >= 1:
                    return py.Global([n.value for n in nodes[1:]])
                else:
                    raise Exception(f"Invalid number of arguments to global: {parlen}")
                
            case "nonlocal":
                if parlen == 1:
                    return py.Nonlocal([nodes[1].value])
                else:
                    raise Exception(f"Invalid number of arguments to nonlocal: {parlen}")
                
            case "async":
                if parlen == 1:
                    return py.AsyncFunctionDef(nodes[1].value, py.arguments([], None, None, []), [c(nodes[2])], [])
                else:
                    raise Exception(f"Invalid number of arguments to async: {parlen}")
                
            case "await":
                if parlen == 1:
                    return py.Await(c(nodes[1]))
                else:
                    raise Exception(f"Invalid number of arguments to await: {parlen}")
                
            case "dict":
                if parlen == 0:
                    return py.Dict([], [])
                elif parlen % 2 == 0:
                    i = 0
                    keys = []
                    values = []
                    while i < parlen:
                        keys.append(c(nodes[i + 1]))
                        values.append(c(nodes[i + 2]))
                        i += 2
                    return py.Dict(keys, values)
                else:
                    raise Exception(f"Invalid number of arguments to dict: {parlen}")
                
            case "set":
                if parlen == 1:
                    return py.Set([])
                elif parlen == 2:
                    return py.Set([c(nodes[1])])
                else:
                    raise Exception(f"Invalid number of arguments to set: {parlen}")

            case "slice":
                if parlen == 1:
                    return py.Slice(None, None, None)
                elif parlen == 2:
                    return py.Slice(c(nodes[1]), None, None)
                elif parlen == 3:
                    return py.Slice(c(nodes[1]), c(nodes[2]), None)
                elif parlen == 4:
                    return py.Slice(c(nodes[1]), c(nodes[2]), c(nodes[3]))
                else:
                    raise Exception(f"Invalid number of arguments to slice: {parlen}")

            case "do":
                id = cc.gensym()
                body = stmt_wrap([c(n) for n in flatten(nodes[1:])])
                args = py.arguments(args=[], posonlyargs=[], kwonlyargs=[],
                                    kw_defaults=[], defaults=[])
                f = py.FunctionDef(id, args, body, [])
                cc.fun_defs.append(f)
                return py.Call(py.Name(id, py.Load()), [], [])

            case "meta":
                cc.meta.run(cc.operator_parse(regular(nodes[1:])))
                return py.Pass()
            
            case "quote":
                q_mr = cc.meta.quote(regular(flatten(nodes[1]))[0])
                q_py = c(q_mr)
                return q_py
            
            case "macro":
                if parlen >= 2:
                    f = Identifier("fun")
                    cb = CurlyBrackets([f, *nodes[1:]])
                    cb._original_nodes = original._original_nodes
                    cc.meta.run([cb])
                    return py.Pass()
                else:
                    raise Exception(f"Invalid number of arguments to macro: {parlen}")

    # curly brackets
    def curly(n: CurlyBrackets) -> py.AST | list[py.AST] | None:
        nodes = n.nodes
        if len(nodes) == 0:
            return py.Constant(None)

        n0 = nodes[0]
        reg_nodes = regular(nodes)

        # operator as function call
        if get_operator(reg_nodes[0]):
            op = reg_nodes[0].value
            if len(reg_nodes) == 1:
                # {+}
                args = ['$left', '$right']
                body = c(BinOp(Identifier(args[0]), op, Identifier(args[1])))
            elif len(reg_nodes) == 2:
                # {+ 2}
                args = '$left'
                body = c(BinOp(reg_nodes[1], op, Identifier(args)))
            else:
                raise Exception(f"Invalid number of arguments to operator: {len(reg_nodes)}")
            r = pb.lambda_(args, body)
            return r

        opp_nodes = cc.operator_parse(reg_nodes)
        opp_n0 = opp_nodes[0]

        if get_identifier(n0):
            # reserved word
            r = compile_curly_reserved(n, cc, compile_mr, opp_nodes)
            if r:
                return r
            
            # meta symbol call
            # BUG: does not handle a.f calls
            if n0.value in cc.meta.symbols:
                if len(nodes) <= 2:  # whitespace after identifier
                    meta_args = []
                else:
                    meta_args = nodes[2:]
                f = cc.meta.symbols[n0.value]
                mrf = f
                # mrf = cc.meta.meta_runnable_func(f)
                result = mrf(meta_args)
                
                if isinstance(result, Node):
                    return c(result)
                return [c(n) for n in regular(result)]

            if get_identifier(opp_n0):
                # function call, identifier
                f = pb.name_ld(opp_n0.value)
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
            if not cc.running_in_meta and value in cc.meta.symbols:
                # meta identifier
                return c(cc.meta.symbols[value])
            # regular identifier
            return pb.name_ld(value)
            
        case String():
            # string constant, bin/oct/hex number, regex, datetime
            n._type = Identifier("str")
            return pb.constant(python_value(n))
        
        case Number():
            # numeric constant
            value = python_value(n)
            n._type = Identifier("int" if isinstance(value, int) else "float")
            return pb.constant(python_value(n))
                       
        case BinOp(left, op, right):
            return compile_binop(n, cc, compile_mr)
        
        case RoundBrackets(nodes):
            nodes = cc.operator_parse(regular(nodes))
            if len(nodes) == 0:
                # () is null
                return pb.constant(None)
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
                return pb.constant(None)
            if len(nodes) == 1:
                return c(nodes[0])
            else:
                return [c(n) for n in cc.operator_parse(nodes)]
            
    raise Exception(f"Unknown type: {type(n)}")
