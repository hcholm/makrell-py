
from makrell.ast import Identifier, Node, Number, SquareBrackets, String
from makrell.parsing import python_value


def match(value, pattern: Node) -> dict[str, Node] | bool:

    match pattern:
        case Identifier("_"):
            return True
        case String():
            return value == python_value(pattern)
        case Number():
            return value == python_value(pattern)
        case SquareBrackets(xs):
            return isinstance(value, list) \
                and len(value) == len(xs) \
                and all(match(x, y) for x, y in zip(value, xs))
        case _:
            return False
