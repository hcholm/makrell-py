from dataclasses import dataclass, field
import typing as t


class ParseError(Exception):
    pass


# copied code
def not_found_error(expected: 'Node | type', val: str | None, found: 'Node') -> ParseError:
    expected_descr = node_name(expected)
    if val is not None:
        expected_descr += f" with value {val}"
    pos = found.pos_str()
    found_value = None
    if isinstance(found, Identifier):
        found_value = found.value
    elif isinstance(found, String):
        found_value = found.value
    found_descr = f"{node_name(found)} with value {found_value}"
    return ParseError(f"Expected {expected_descr} at {pos}, found {found_descr}")


@dataclass
class Node:
    _start_line: int = field(default=0, init=False)
    _start_column: int = field(default=0, init=False)
    _end_line: int = field(default=0, init=False)
    _end_column: int = field(default=0, init=False)
    _type: t.Any = field(default=t.Any, init=False)

    def pos_str(self) -> str:
        return f"{self._start_line}:{self._start_column}"
    
    def to_code(self, indent: int = 0):
        return " " * indent
    

@dataclass
class Comment(Node):
    value: str

    def __str__(self):
        return self.value
    
    def __repr__(self) -> str:
        return f"CO:{self.value}"


@dataclass
class Whitespace(Node):
    value: str

    def __str__(self):
        return self.value
    
    def __repr__(self) -> str:
        return "WS"


@dataclass
class Unknown(Node):
    value: str

    def __str__(self):
        return self.value


@dataclass
class MacroPlaceholder(Node):
    value: str

    def __str__(self):
        return self.value


@dataclass
class Identifier(Node):
    value: str

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Identifier):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False

    def __str__(self):
        return self.value
    
    def __repr__(self) -> str:
        return f"ID:{self.value}"
    
    def to_code(self, indent: int):
        return self.value


@dataclass()
class String(Node):
    value: str
    suffix: str | None = None

    def __str__(self):
        return self.value + (self.suffix or "")
    
    def __repr__(self) -> str:
        return f"S:{self.value}"
    
    def to_code(self, indent: int):
        return self.value + (self.suffix or "")


@dataclass
class Number(Node):
    value: str
    suffix: str | None = None

    def __str__(self):
        return self.value + (self.suffix or "")
    
    def __repr__(self) -> str:
        return f"N:{self.value}"
    
    def to_code(self, indent: int):
        return self.value + (self.suffix or "")


@dataclass
class Operator(Node):
    value: str

    def __str__(self):
        return self.value
    
    def __repr__(self) -> str:
        return f"OP:{self.value}"
    
    def to_code(self, indent: int):
        return self.value

@dataclass
class BinOp(Node):
    left: Node
    op: str
    right: Node

    def __str__(self):
        return f"{str(self.left)}{self.op}{str(self.right)}"

    def __repr__(self) -> str:
        return f"BO:<{repr(self.left)} {self.op} {repr(self.right)}>"
    
    def to_code(self, indent: int):
        return (indent * " " + "(" + self.left.to_code(indent) +
                " " + self.op + " " + self.right.to_code(indent) + ")")


@dataclass
class LPar(Node):
    value: str


@dataclass
class RPar(Node):
    value: str


@dataclass
class Sequence(Node):
    """Abstract base class"""
    nodes: t.List[Node]

    _original_nodes: t.List[Node] = field(default_factory=list, init=False)

    @property
    def original_nodes_str(self) -> str:
        return "".join([str(n) for n in self._original_nodes])
    
    def __str__(self):
        return self.original_nodes_str

    # make iterable and subscriptable
    def __iter__(self):
        return iter(self.nodes)
    
    def __getitem__(self, key):
        return self.nodes[key]
    
    def __len__(self):
        return len(self.nodes)
    
    def __contains__(self, item):
        return item in self.nodes
    
    def __reversed__(self):
        return reversed(self.nodes)
    
    def __add__(self, other):
        return self.nodes + other
    
    def __radd__(self, other):
        return other + self.nodes
    
    def to_code(self, indent: int):
        return indent * " " + " ".join([n.to_code(indent) for n in self.nodes])


@dataclass
class NoBrackets(Sequence):

    def __str__(self):
        ns = [str(n) for n in self.nodes]
        return ''.join(ns)


@dataclass
class CurlyBrackets(Sequence):

    def __str__(self):
        return f"{{{self.original_nodes_str}}}"
    
    def __repr__(self) -> str:
        return f"CB:{{{' '.join([repr(n) for n in self.nodes])}}}"

    def to_code(self, indent: int):
        return indent * " " + "{" + " ".join([n.to_code(indent) for n in self.nodes]) + "}"


@dataclass
class RoundBrackets(Sequence):

    def __str__(self):
        return f"({self.original_nodes_str})"
    
    def __repr__(self) -> str:
        return f"RB:({' '.join([repr(n) for n in self.nodes])})"

    def to_code(self, indent: int):
        return indent * " " + "(" + " ".join([n.to_code(indent) for n in self.nodes]) + ")"


@dataclass
class SquareBrackets(Sequence):

    def __str__(self):
        return f"[{self.original_nodes_str}]"
    
    def __repr__(self) -> str:
        return f"SB:[{' '.join([repr(n) for n in self.nodes])}]"

    def to_code(self, indent: int):
        return indent * " " + "[" + " ".join([n.to_code(indent) for n in self.nodes]) + "]"


def node_name(n: Node | type) -> str:
    if isinstance(n, type):
        nname = n.__name__
    else:
        nname = n.__class__.__name__

    match nname:
        case "Identifier":
            return "identifier"
        case "String":
            return "string"
        case "Number":
            return "number"
        case "Operator":
            return "operator"
        case "LPar":
            return "left bracket"
        case "RPar":
            return "right bracket"
        case "Whitespace":
            return "whitespace"
        case "Comment":
            return "comment"
        case "Unknown":
            return "unknown"
        case "RoundBrackets":
            return "round brackets"
        case "SquareBrackets":
            return "square brackets"
        case "CurlyBrackets":
            return "curly brackets"
        case "Sequence":
            return "sequence"
        case "BinOp":
            return "binary operation"
        case nname:
            return nname


def dump(n: Node, indent: int = 4, include_attributes: bool = False) -> str:
    
    def d(dn: Node, current_indent: int) -> str:
        if isinstance(dn, list):
            print("LIST s")
            return "\n".join([d(ni, current_indent) for ni in dn])

        r = ""
        ind = current_indent * " "
        ind2 = (current_indent + indent) * " "
        r += ind + "{" + dn.__class__.__name__ + "\n"
        
        def chk_print_attr(a):
            if a.startswith("__"):
                return False
            if a == "_original_nodes":
                return False
            return not include_attributes or not a.startswith("_")
        
        nattrs = [a for a in dir(dn) if chk_print_attr(a)]
        for nattr in nattrs:
            attr = getattr(dn, nattr)
            if isinstance(attr, int):
                r += ind2 + nattr + " " + str(attr) + "\n"
            if isinstance(attr, list):
                r += ind2 + nattr + " [\n"
                for a in attr:
                    r += d(a, current_indent + 2 * indent) + "\n"
                r += ind2 + "]\n"
        r += ind + "}\n"
        return r
              
    print(repr(n), type(n))
    rr = ""
    if isinstance(n, list):
        print("LIST")
        for ni in n:
            rr += d(ni, 0) + "\n"
    else:
        rr = d(n, 0)
    return rr
