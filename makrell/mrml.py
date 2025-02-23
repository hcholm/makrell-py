import xml.etree.ElementTree as ET
from makrell.ast import BinOp, CurlyBrackets, Identifier, Node, Number, RoundBrackets, SquareBrackets, String
from makrell.makrellpy.compiler import eval_nodes
from makrell.baseformat import src_to_baseformat, operator_parse
from makrell.tokeniser import regular
from makrell.parsing import NodeReader, get_identifier


def node_str(n: Node) -> str:
    if isinstance(n, Identifier):
        return n.value
    if isinstance(n, String):
        return n.value[1:-1]
    return str(n)


def parse_element(n: Node, parent: ET.Element | None = None, allow_exec: bool = False,
                  globs={}, locs={}) -> ET.Element:
    if not isinstance(n, CurlyBrackets):
        raise Exception("Expected curly brackets at " + n.pos_str())
    if len(n.nodes) == 0:
        raise Exception("Empty curly brackets")
    
    reader = NodeReader(n.nodes)

    elem_name_node = reader.read()
    if isinstance(elem_name_node, Identifier):
        elem_name = elem_name_node.value
    elif isinstance(elem_name_node, String):
        elem_name = elem_name_node.value[1:-1]
    else:
        raise Exception("Expected identifier")
    
    if parent is not None:
        elem = ET.SubElement(parent, elem_name)
    else:
        elem = ET.Element(elem_name)
    reader.skip_whitespace()

    next = reader.peek()
    if isinstance(next, SquareBrackets):
        reader.read()
        attr_nodes = operator_parse(regular(next.nodes))
        for attr_node in attr_nodes:
            if not isinstance(attr_node, BinOp) and not attr_node.type == "=":
                raise Exception("Expected attribute")
            
            name = node_str(attr_node.left)
            ar = attr_node.right

            if isinstance(ar, CurlyBrackets):
                if allow_exec and len(ar.nodes) >= 1 and get_identifier(ar.nodes[0], "$"):
                    ns = regular(ar.nodes[1:])
                    # print(f"exec attr ns: {ns}")
                    value = str(eval_nodes(operator_parse(ns)[0]))
                else:
                    raise Exception("Expected attribute value")
            else:
                value = node_str(ar)
            elem.attrib[name] = value

        reader.skip_whitespace()

    tail_holder = None

    def append_text(text: str):
        if tail_holder is not None:
            if tail_holder.tail:
                tail_holder.tail += text
            else:
                tail_holder.tail = text
        else:
            if elem.text:
                elem.text += text
            else:
                elem.text = text

    while reader.has_more:
        next = reader.read()

        if isinstance(next, CurlyBrackets):
            if allow_exec and len(next.nodes) >= 1 and get_identifier(next.nodes[0], "$"):
                ns = regular(next.nodes[1:])
                r = eval_nodes(operator_parse(ns)[0], None, globals() | globs, locals() | locs)
                append_text(str(r))
            else:
                tail_holder = parse_element(next, elem, allow_exec, globs, locs)
        else:
            if isinstance(next, String):
                text = next.value[1:-1]
            elif isinstance(next, Number):
                text = str(next.value) + str(next.suffix)
            elif isinstance(next, Identifier):
                text = next.value
            elif isinstance(next, RoundBrackets):
                text = "(" + ")"  # TODO
            else:
                text = str(next)
            append_text(text)

    return elem


def parse(src: str, allow_exec: bool = False) -> ET.Element:
    bp = regular(src_to_baseformat(src))
    return parse_element(bp[0], None, allow_exec)


def parse_to_xml(src: str, allow_exec: bool = False) -> str:
    elem = parse(src, allow_exec)
    return ET.tostring(elem, encoding="unicode")
