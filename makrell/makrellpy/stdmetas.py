import ast as py


def intsuffix_i(s: str) -> py.expr:
    svalue = int(s)
    # AST for `complex(0, svalue)`
    n = py.Call(py.Name("complex", py.Load()), [py.Constant(0), py.Constant(svalue)], [])
    return n


def floatsuffix_i(s: str) -> py.expr:
    svalue = float(s)
    # AST for `complex(0, svalue)`
    n = py.Call(py.Name("complex", py.Load()), [py.Constant(0), py.Constant(svalue)], [])
    return n


def strsuffix_hex(s: str) -> py.expr:
    svalue = int(s, 16)
    return py.Constant(svalue)


def strsuffix_dt(s: str) -> py.expr:
    # AST for `datetime.fromisoformat(s)`
    n = py.Call(py.Attribute(py.Name("datetime", py.Load()), "fromisoformat", py.Load()), [py.Constant(s)], [])
    return n


# {def operator >> 100
#     [x] -> (x | $left | $right)
# }

def operator_rightshift_rightshift(left: py.expr, right: py.expr) -> py.expr:
    # AST for `lambda x: right(left(x))`
    args = py.arguments([py.arg("x")], [], None, [], [], None, [])
    n = py.Lambda(args,
                  py.Call(right, [
                      py.Call(left, [py.Name("x", py.Load())], [])], []))
    return n


_mr_defs = {
    'intsuffix': {
        'i': intsuffix_i,
    },
    'floatsuffix': {
        'i': floatsuffix_i,
    },
    'strsuffix': {
        'hex': strsuffix_hex,
        'dt': strsuffix_dt,
    },
}


__all__ = ['_mr_defs']
