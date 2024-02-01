
from makrell.ast import Identifier, LPar, Number, Operator, RPar, String, Unknown, Whitespace
from makrell.tokeniser import regular, src_to_tokens


def test_minimal():
    src = "2 3 5 7 11 13"
    tokens = regular(src_to_tokens(src))
    assert len(tokens) == 6
    assert isinstance(tokens[0], Number)
    assert tokens[0].value == "2"
    assert isinstance(tokens[1], Number)
    assert tokens[1].value == "3"
    assert isinstance(tokens[2], Number)
    assert tokens[2].value == "5"
    assert isinstance(tokens[3], Number)
    assert tokens[3].value == "7"
    assert isinstance(tokens[4], Number)
    assert tokens[4].value == "11"
    assert isinstance(tokens[5], Number)
    assert tokens[5].value == "13"


def test_whitespace():
    src = "a 4"
    tokens = src_to_tokens(src)
    assert len(tokens) == 3
    assert isinstance(tokens[0], Identifier)
    assert tokens[0].value == "a"
    assert isinstance(tokens[1], Whitespace)
    assert tokens[1].value == " "
    assert isinstance(tokens[2], Number)
    assert tokens[2].value == "4"


def test_string():
    src = '"asd" "qwe"'
    tokens = regular(src_to_tokens(src))
    assert len(tokens) == 2
    assert isinstance(tokens[0], String)
    assert tokens[0].value == '"asd"'
    assert isinstance(tokens[1], String)
    assert tokens[1].value == '"qwe"'
    assert tokens[1].suffix == ""


def test_op_and_string():
    src = 'a="asd"'
    tokens = regular(src_to_tokens(src))
    assert len(tokens) == 3
    assert isinstance(tokens[0], Identifier)
    assert tokens[0].value == 'a'
    assert isinstance(tokens[1], Operator)
    assert tokens[1].value == "="
    assert isinstance(tokens[2], String)
    assert tokens[2].value == '"asd"'


def test_suffixed_string():
    src = '"asd"i "qwe"r'
    tokens = regular(src_to_tokens(src))
    assert len(tokens) == 2
    assert isinstance(tokens[0], String)
    assert tokens[0].value == '"asd"'
    assert tokens[0].suffix == "i"
    assert isinstance(tokens[1], String)
    assert tokens[1].value == '"qwe"'
    assert tokens[1].suffix == "r"


def test_number():
    src = "2 13.5 -5.7e-55 0.1e+10å"
    tokens = regular(src_to_tokens(src))
    assert len(tokens) == 4
    assert isinstance(tokens[0], Number)
    assert tokens[0].value == "2"
    assert isinstance(tokens[1], Number)
    assert tokens[1].value == "13.5"
    assert isinstance(tokens[2], Number)
    assert tokens[2].value == "-5.7e-55"
    assert isinstance(tokens[3], Number)
    assert tokens[3].value == "0.1e+10"
    assert tokens[3].suffix == "å"


def test_mixed():
    src = "2 13 asd qwe []}{%()"
    tokens = regular(src_to_tokens(src))
    assert len(tokens) == 11
    assert isinstance(tokens[0], Number)
    assert tokens[0].value == "2"
    assert isinstance(tokens[1], Number)
    assert tokens[1].value == "13"
    assert isinstance(tokens[2], Identifier)
    assert tokens[2].value == "asd"
    assert isinstance(tokens[3], Identifier)
    assert tokens[3].value == "qwe"
    assert isinstance(tokens[4], LPar)
    assert tokens[4].value == "["
    assert isinstance(tokens[5], RPar)
    assert tokens[5].value == "]"
    assert isinstance(tokens[6], RPar)
    assert tokens[6].value == "}"
    assert isinstance(tokens[7], LPar)
    assert tokens[7].value == "{"
    assert isinstance(tokens[8], Operator)
    assert tokens[8].value == "%"
    assert isinstance(tokens[9], LPar)
    assert tokens[9].value == "("
    assert isinstance(tokens[10], RPar)
    assert tokens[10].value == ")"
    

def test_unicode():
    src = "Æﾶʨϕﺱ㘖 ⻚⿌ ˚⇘⋀▆《》 七㉜ ｢｣"
    tokens = src_to_tokens(src)
    assert len(tokens) == 9
    assert isinstance(tokens[0], Identifier)
    assert tokens[0].value == "Æﾶʨϕﺱ㘖"
    assert isinstance(tokens[2], Operator)
    assert tokens[2].value == "⻚⿌"
    assert isinstance(tokens[4], Unknown)
    assert tokens[4].value == "˚⇘⋀▆《》"
    assert isinstance(tokens[6], Identifier)
    assert tokens[6].value == "七㉜"
    assert isinstance(tokens[8], Unknown)
    assert tokens[8].value == "｢｣"


def test_multiline():
    src = """2
    3
    5"""
    tokens = regular(src_to_tokens(src))
    assert len(tokens) == 3
    assert isinstance(tokens[0], Number)
    assert tokens[0].value == "2"
    assert isinstance(tokens[1], Number)
    assert tokens[1].value == "3"
    assert isinstance(tokens[2], Number)
    assert tokens[2].value == "5"
