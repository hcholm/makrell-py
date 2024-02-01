import ast as py


bin_ops = {
    "+": py.Add(), "-": py.Sub(), "*": py.Mult(), "/": py.Div(),
    "//": py.FloorDiv(), "%": py.Mod(), "**": py.Pow(),
    "<<<": py.LShift(), ">>>": py.RShift(),
    "|||": py.BitOr(), "^^^": py.BitXor(), "&&&": py.BitAnd(),
}

bool_ops = {
    "&&": py.And(), "||": py.Or(),
}

compare_ops = {
    "==": py.Eq(), "!=": py.NotEq(),
    "<": py.Lt(), "<=": py.LtE(), ">": py.Gt(), ">=": py.GtE(),
}


def simple_reserved(w: str) -> py.AST | None:
    match w:
        case "true":
            return py.Constant(True)
        case "false":
            return py.Constant(False)
        case "null":
            return py.Constant(None)
        case "return":
            return py.Return(py.Constant(None))
        case "yield":
            return py.Yield(py.Constant(None))
        case "yieldfrom":
            return py.YieldFrom(py.Constant(None))
        case "pass":
            return py.Pass()
        case "break":
            return py.Break()
        case "continue":
            return py.Continue()
        case _:
            return None
