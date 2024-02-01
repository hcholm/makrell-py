import re
from typing import Any
from makrell.ast import Identifier, Number, Sequence, SquareBrackets, CurlyBrackets, Node, String
from makrell.makrellpy.compiler import eval_nodes
import makrell.baseformat as mp
from makrell.tokeniser import regular
from makrell.parsing import get_identifier, python_value, pairwise


class MronObject:
    def __init__(self, data: dict[str, Any]):
        self._data = data

    def __getattr__(self, name: str) -> Any:
        return self._data[name]

    def __getitem__(self, name: str) -> Any:
        return self._data[name]

    def __str__(self) -> str:
        return str(self._data)

    def __repr__(self) -> str:
        return repr(self._data)
    
    def __iter__(self):
        return iter(self._data)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, MronObject):
            return self._data == other._data
        if isinstance(other, dict):
            return self._data == other
        return False


rx_int = re.compile(r'^-?\d+$')


def parse_token(n: Node, allow_exec: bool = False) -> Any:
    if isinstance(n, Identifier):
        return n.value
    elif isinstance(n, String):
        return python_value(n)
    elif isinstance(n, Number):
        return python_value(n)
    elif isinstance(n, CurlyBrackets):
        if allow_exec and len(n.nodes) >= 2 and get_identifier(n.nodes[0], "$"):
            r = eval_nodes(mp.operator_parse(n.nodes[1:])[0])
            return r
        return parse_token_pairs(regular(n.nodes))
    elif isinstance(n, SquareBrackets):
        return [parse_token(ni) for ni in regular(n.nodes)]
    elif isinstance(n, Sequence):
        return parse_token_pairs(regular(n.nodes))
    else:
        raise Exception(f"Unknown node type: {type(n)}")
    

def parse_token_pairs(ns: list[Node], allow_exec: bool = False) -> MronObject:
    pairs = pairwise(ns)
    d = {parse_token(k, allow_exec): parse_token(v, allow_exec) for k, v in pairs}
    return MronObject(d)


def parse_nodes(ns: list[Node], allow_exec: bool = False) -> MronObject | Any:
    if len(ns) == 0:
        return None
    if len(ns) == 1:
        v = parse_token(ns[0], allow_exec)
        return v
    if len(ns) % 2 == 0:
        return parse_token_pairs(ns, allow_exec)


def parse_src(text: str, allow_exec: bool = False) -> MronObject | Any:
    tokens = regular(mp.src_to_tokens(text))
    ns = mp.nodes_to_baseformat(tokens)
    if len(ns) == 0:
        return None
    if len(ns) == 1:
        v = parse_token(ns[0], allow_exec)
        return v
    if len(ns) % 2 == 0:
        return parse_token_pairs(ns, allow_exec)
    raise Exception(f"Illegal number ({len(ns)}) of root level expressions")


def parse_file(path: str, allow_exec: bool = False) -> MronObject | Any:
    with open(path, encoding='utf-8') as f:
        src = f.read()
        return parse_src(src, allow_exec)
