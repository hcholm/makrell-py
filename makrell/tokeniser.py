import regex
from makrell.ast import (
    BinOp, Comment, Identifier, LPar, Node, Operator, RPar, Sequence, String, Unknown, Whitespace, Number)


rxs = [
    (regex.compile(r'\s+', regex.MULTILINE), Whitespace),
    (regex.compile(r'#.*$', regex.MULTILINE), Comment),
    (regex.compile(r'/\*(.*?)\*/', regex.DOTALL), Comment),

    (regex.compile(r'[\p{L}_\$][\p{L}\p{N}_\$]*'), Identifier),
    (regex.compile(r'("(?:\\.|[^"\\])*")([\p{L}\p{N}_]*)', regex.DOTALL), String),
    (regex.compile(r'((?:-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?))([\p{L}\p{N}_]*)'), Number),

    (regex.compile(r'[\(\[\{]'), LPar),
    (regex.compile(r'[\)\]\}]'), RPar),

    (regex.compile(r'[[\p{Sm}\p{So}\p{Pd}\p{Po}]--["\'#\$]]+', regex.VERSION1), Operator),

    (regex.compile(r'[^"\'{}()\[\]\s]+'), Unknown),
]


def is_regular_node(n: Node) -> bool:
    return not isinstance(n, (Comment, Whitespace, Unknown))


def regular(nodes: list[Node], recurse: bool = False) -> list[Node]:
    def r(n) -> Node:
        if isinstance(n, Sequence):
            children = regular(n.nodes, True)
            return type(n)(children)
        if isinstance(n, BinOp):
            left = r(n.left)
            right = r(n.right)
            return BinOp(left, n.op, right)
        return n

    if recurse:
        return [r(n) for n in nodes if is_regular_node(n)]
    else:
        return [n for n in nodes if is_regular_node(n)]


def src_to_tokens(src: str) -> list[Node]:
    nodes = []
    pos = 0
    line = 1
    column = 1

    while pos < len(src):
        match = None
        for rx, node_type in rxs:
            match = rx.match(src, pos)
            if match:
                if node_type in {String, Number}:
                    value = match.group(1)
                    suffix = match.group(2)
                    node = node_type(value, suffix)
                else:
                    value = match.group()
                    node = node_type(value)
                nodes.append(node)

                node._start_line = line
                node._start_column = column
                
                pos += len(match.group())
                line_increment = value.count('\n')
                if line_increment > 0:
                    line += line_increment
                    column = len(value) - value.rfind('\n')
                else:
                    column += len(value)

                node._end_line = line
                node._end_column = column
                break

        if not match:
            raise ValueError(f"Unrecognized character sequence at {line}:{column}")
    
    return nodes


def file_to_tokens(path: str) -> list[Node]:
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    return src_to_tokens(src)
