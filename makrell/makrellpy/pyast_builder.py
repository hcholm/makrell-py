import ast


# Literals

def constant(value):
    return ast.Constant(value)

def list_ld(elts: list[ast.expr]) -> ast.List:
    return ast.List(elts, ctx=ast.Load())

def list_st(elts: list[ast.expr]) -> ast.List:
    return ast.List(elts, ctx=ast.Store())


# Variables

def name_ld(id) -> ast.Name:
    return ast.Name(id, ctx=ast.Load())

def name_st(id) -> ast.Name:
    return ast.Name(id, ctx=ast.Store())

def name_del(id) -> ast.Name:
    return ast.Name(id, ctx=ast.Del())


# Expressions

def expr(value: ast.expr):
    return ast.Expr(value)

def unaryop(op: ast.unaryop, operand: ast.expr) -> ast.UnaryOp:
    return ast.UnaryOp(op, operand)

def uadd() -> ast.unaryop: return ast.UAdd()
def usub() -> ast.unaryop: return ast.USub()
def not_() -> ast.unaryop: return ast.Not()
def invert() -> ast.unaryop: return ast.Invert()

def xuadd(x) -> ast.expr: return unaryop(uadd(), x)
def xusub(x) -> ast.expr: return unaryop(usub(), x)
def xnot(x) -> ast.expr: return unaryop(not_(), x)
def xinvert(x) -> ast.expr: return unaryop(invert(), x)

def binop(left: ast.expr, op: ast.operator, right: ast.expr) -> ast.expr:
    return ast.BinOp(left, op, right)

def add() -> ast.operator: return ast.Add()
def sub() -> ast.operator: return ast.Sub()
def mult() -> ast.operator: return ast.Mult()
def div() -> ast.operator: return ast.Div()
def floordiv() -> ast.operator: return ast.FloorDiv()
def mod() -> ast.operator: return ast.Mod()
def pow() -> ast.operator: return ast.Pow()
def lshift() -> ast.operator: return ast.LShift()
def rshift() -> ast.operator: return ast.RShift()
def bitor() -> ast.operator: return ast.BitOr()
def bitxor() -> ast.operator: return ast.BitXor()
def bitand() -> ast.operator: return ast.BitAnd()
def matmult() -> ast.operator: return ast.MatMult()

def boolop(op: ast.boolop, values: list[ast.expr]) -> ast.BoolOp:
    return ast.BoolOp(op, values)

def and_() -> ast.boolop: return ast.And()
def or_() -> ast.boolop: return ast.Or()

def compare(left: ast.expr, ops: list[ast.cmpop], comparators: list[ast.expr]) -> ast.Compare:
    return ast.Compare(left, ops, comparators)

def eq() -> ast.cmpop: return ast.Eq()
def noteq() -> ast.cmpop: return ast.NotEq()
def lt() -> ast.cmpop: return ast.Lt()
def lte() -> ast.cmpop: return ast.LtE()
def gt() -> ast.cmpop: return ast.Gt()
def gte() -> ast.cmpop: return ast.GtE()
def is_() -> ast.cmpop: return ast.Is()
def isnot() -> ast.cmpop: return ast.IsNot()
def in_() -> ast.cmpop: return ast.In()
def notin() -> ast.cmpop: return ast.NotIn()

def call(func: ast.expr | str, args: list[ast.expr] = [], keywords: list[ast.keyword] = []) -> ast.Call:
    if isinstance(func, str):
        func = name_ld(func)
    return ast.Call(func, args, keywords)

def keyword(arg: str, value: ast.expr) -> ast.keyword:
    return ast.keyword(arg, value)

def ifexp(test: ast.expr, body: ast.expr, orelse: ast.expr) -> ast.IfExp:
    return ast.IfExp(test, body, orelse)

def attribute_ld(value: ast.expr, attr: str) -> ast.Attribute:
    return ast.Attribute(value, attr, ast.Load())

def attribute_st(value: ast.expr, attr: str) -> ast.Attribute:
    return ast.Attribute(value, attr, ast.Store())


# Subscripting

def subscript_ld(value: ast.expr, slice: ast.Slice) -> ast.Subscript:
    return ast.Subscript(value, slice, ast.Load())

def subscript_st(value: ast.expr, slice: ast.Slice) -> ast.Subscript:
    return ast.Subscript(value, slice, ast.Store())

def subscript_del(value: ast.expr, slice: ast.Slice) -> ast.Subscript:
    return ast.Subscript(value, slice, ast.Del())

def slice(lower: ast.expr | None = None, upper: ast.expr | None = None, step: ast.expr | None = None) -> ast.Slice:
    return ast.Slice(lower, upper, step)


# Comprehensions

# Statements

def assign(targets: list[ast.expr], value: ast.expr) -> ast.Assign:
    return ast.Assign(targets, value)

def annassign(target: ast.Name | ast.Attribute | ast.Subscript,
              annotation: ast.expr,
              value: ast.expr | None,
              simple: int) -> ast.AnnAssign:
    return ast.AnnAssign(target, annotation, value, simple)

def augassign(target: ast.Name | ast.Attribute | ast.Subscript,
              op: ast.operator,
              value: ast.expr) -> ast.AugAssign:
    return ast.AugAssign(target, op, value)

def raise_(exc: ast.expr | None = None, cause: ast.expr | None = None) -> ast.Raise:
    return ast.Raise(exc, cause)

def assert_(test: ast.expr, msg: ast.expr | None = None) -> ast.Assert:
    return ast.Assert(test, msg)

def delete(targets: list[ast.expr]) -> ast.Delete:
    return ast.Delete(targets)

def pass_() -> ast.Pass:
    return ast.Pass()

# def typealias

# Imports

# Control flow

def if_(test: ast.expr, body: list[ast.stmt], orelse: list[ast.stmt] = []) -> ast.If:
    return ast.If(test, body, orelse)

def for_(target: ast.expr, iter: ast.expr, body: list[ast.stmt], orelse: list[ast.stmt] = []) -> ast.For:
    return ast.For(target, iter, body, orelse)

def while_(test: ast.expr, body: list[ast.stmt], orelse: list[ast.stmt] = []) -> ast.While:
    return ast.While(test, body, orelse)

def break_() -> ast.Break:
    return ast.Break()

def continue_() -> ast.Continue:
    return ast.Continue()

# Pattern matching

# Type parameters

# Function and class definitions

def function_def(name: str,
                 args: ast.arguments | str | list[str],
                 body: list[ast.stmt],
                 decorator_list: list[ast.expr] = []
                 ) -> ast.FunctionDef:
    if isinstance(args, str):
        args = ast.arguments([ast.arg(args)], [], None, [], [], None, [])
    elif isinstance(args, list):
        args = ast.arguments([ast.arg(arg) for arg in args], [], None, [], [], None, [])
    return ast.FunctionDef(name, args, body, decorator_list)

def lambda_(args: ast.arguments | str | list[str], body: ast.expr) -> ast.Lambda:
    if isinstance(args, str):
        args = ast.arguments([ast.arg(args)], [], None, [], [], None, [])
    elif isinstance(args, list):
        args = ast.arguments([ast.arg(arg) for arg in args], [], None, [], [], None, [])
    return ast.Lambda(args, body)

# Async and await

#

def return_(value: ast.expr | None = None):
    return ast.Return(value)
