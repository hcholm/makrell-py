import ast as py
from importlib import import_module
from makrell.ast import (Identifier, Sequence, CurlyBrackets, Node)
from makrell.baseformat import (Associativity, operator_parse)
from makrell.makrellpy._compiler_common import CompilerContext
from makrell.tokeniser import regular
from makrell.parsing import (get_binop, get_curly, get_square_brackets, flatten, get_identifier)
from ._compiler_common import dotted_ident, stmt_wrap, transfer_pos
import makrell.makrellpy.pyast_builder as pb


def compile_curly_reserved(n: CurlyBrackets, cc: CompilerContext, compile_mr, opp_nodes) -> py.AST | list[py.AST] | None:
    reg_nodes = regular(n.nodes)
    nodes = opp_nodes
    original = n

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

    n0: Identifier = nodes[0]  # type: ignore
    if not get_identifier(n0):
        return None
    parlen = len(nodes) - 1

    match n0.value:
        case "not":
            if parlen == 1:
                return pb.xnot(c(nodes[1]))
            else:
                raise Exception(f"Invalid number of arguments to not: {parlen}")

        case "if":
            pars = regular(nodes[1:])
            if len(pars) == 0:
                cc.diag.error(0, "No arguments to if.", n0)
                return None
            if len(pars) == 1:
                return pb.constant(None)
            
            def iff(ps: list[Node]) -> py.expr:
                if len(ps) == 0:
                    return pb.constant(None)
                if len(ps) == 1:
                    return c(ps[0])
                return pb.ifexp(c(ps[0]), c(ps[1]), iff(ps[2:]))
            
            return iff(pars)
            
        case "when":
            body = stmt_wrap([c(n) for n in regular(nodes[2:])], auto_return=False)
            return pb.if_(c(nodes[1]), body)

        case "while":
            if parlen >= 2:
                test = c(nodes[1])
                body = stmt_wrap([c(n) for n in regular(nodes[2:])], auto_return=False)
                return py.While(test, body, [])
            else:
                cc.diag.error(0, f"Invalid number of arguments to while: {parlen}", n0)
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
                if nid := get_identifier(n):
                    imports_names.append(nid.value)
                elif get_binop(n, "."):
                    name = dotted_ident(n)
                    imports_names.append(name)
                elif nbo := get_binop(n, "@"):
                    name = dotted_ident(nbo.left)
                    rights = regular(nbo.right.nodes)
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
                return pb.return_()
            elif parlen == 1:
                return pb.return_(c(nodes[1]))
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
                return py.Raise(None, None)
            elif parlen == 2:
                return py.Raise(c(nodes[1]), None)
            elif parlen == 3:
                return py.Raise(c(nodes[1]), c(nodes[2]))
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
                        if nbo := get_binop(nnodes[1], ":"):
                            # catch with name and type
                            name = nbo.left.value
                            typ = c(nbo.right)
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
                return pb.assert_(c(nodes[1]))
            elif parlen == 2:
                return pb.assert_(c(nodes[1]), c(nodes[2]))
            else:
                raise Exception(f"Invalid number of arguments to assert: {parlen}")
            
        case "pass":
            if parlen == 0:
                return pb.pass_()
            else:
                raise Exception(f"Invalid number of arguments to pass: {parlen}")
            
        case "break":
            if parlen == 0:
                return pb.break_()
            
        case "continue":
            if parlen == 0:
                return pb.continue_()
            
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
                return py.AsyncFunctionDef(nodes[1].value, py.arguments([], None, None, []),
                                           [c(nodes[2])], [])
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
            cc.push_fun_defs_scope()
            id = cc.gensym()
            stmts = stmt_wrap([c(n) for n in flatten(nodes[1:])])
            fun_defs = cc.pop_fun_defs_scope()
            body = fun_defs + stmts
            # body = stmt_wrap([c(n) for n in flatten(nodes[1:])])
            # body = cc.fun_defs.pop() + body
            args = py.arguments(args=[], posonlyargs=[], kwonlyargs=[],
                                kw_defaults=[], defaults=[])
            f = py.FunctionDef(id, args, body, [])
            cc.add_to_fun_defs_scope(f)
            return py.Call(py.Name(id, py.Load()), [], [])

        case "meta":
            cc.meta.run(cc.operator_parse(regular(nodes[1:])))
            return pb.pass_()
        
        case "quote":
            q_mr = cc.meta.quote(regular(flatten(nodes[1]))[0])
            q_py = c(q_mr)
            return q_py
        
        case "def":
            # print(reg_nodes)
            # print(nodes)
            if len(reg_nodes) >= 3:
                deftype = reg_nodes[1].value
                match deftype:

                    case "macro":
                        f = Identifier("fun")
                        cb = CurlyBrackets([f, *reg_nodes[2:]])
                        cb._original_nodes = original._original_nodes  # type: ignore
                        cc.meta.run([cb])
                        return pb.pass_()
                    
                    case "operator":
                        if len(reg_nodes) < 3:
                            raise Exception(f"Invalid number of arguments to operator: {len(reg_nodes)}")
                        is_rass = get_identifier(reg_nodes[3], "rightassoc")
                        op = reg_nodes[2].value
                        precedence = int(reg_nodes[3].value)
                        associativity = Associativity.RIGHT if is_rass else Associativity.LEFT
                        cc.operators[op] = (precedence, associativity)

                        expr_start = 5 if is_rass else 4
                        expr_nodes = reg_nodes[expr_start:]
                        body = c(operator_parse(expr_nodes, cc.op_precedence)[0])
                        arguments = ["$left", "$right"]
                        expr = pb.lambda_(arguments, body)
                        cc.meta.symbols[op] = expr
                        return pb.pass_()
                    
                    case "pattern":
                        raise Exception("Pattern matching not implemented.")
                    
                    case "strsuffix":
                        raise Exception("String suffix not implemented.")
                    
                    case "intsuffix":
                        raise Exception("Int suffix not implemented.")
                    
                    case "floatsuffix":
                        raise Exception("Float suffix not implemented.")
                    
                    case _:
                        raise Exception(f"Invalid def type: {deftype}")
            else:
                raise Exception(f"Invalid number of arguments to def: {parlen}")

    return None
