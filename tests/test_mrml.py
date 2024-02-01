from makrell.mrml import parse_to_xml


def to_xml(src: str, allow_exec: bool = False) -> str:
    xml = parse_to_xml(src, allow_exec)
    return xml


def test_simple():
    src = "{a}"
    v = to_xml(src)
    assert v == "<a />"


def test_content():
    src = "{a 2}"
    v = to_xml(src)
    assert v == "<a>2</a>"

    src = "{a b 2 b 2}"
    v = to_xml(src)
    assert v == "<a>b 2 b 2</a>"


def test_mixed_content():
    src = '{a b()2")" {c d 3}"asd"}'
    v = to_xml(src)
    assert v == "<a>b()2) <c>d 3</c>asd</a>"


def test_attributes():
    src = '{a [b="2" c=3]}'
    v = to_xml(src)
    assert v == '<a b="2" c="3" />'


def test_attributes_mixed():
    src = '{a [b="2" c=3] a"b"}'
    v = to_xml(src)
    assert v == '<a b="2" c="3">ab</a>'


def test_exec():
    src = '{a {$ [2 3 5 7] | sum}}'
    v = to_xml(src, True)
    assert v == "<a>17</a>"


def test_attr_exec():
    src = '{a [b = {$ [2 3 5 7] | sum}] asd}'
    v = to_xml(src, True)
    assert v == '<a b="17">asd</a>'

