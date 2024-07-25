
from typing import Any
from makrell.makrellpy.compiler import eval_src


def run(src: str, expected: Any) -> None:
    r = eval_src(src)
    assert r == expected


def test_scalars() -> None:
    run(" 2 ", 2)
    run(" 2.5 ", 2.5)
    run(" -2.5 ", -2.5)
    run(" 2.5e10 ", 2.5e10)
    run(" -2.5e10 ", -2.5e10)
    run(" 2.5e-10 ", 2.5e-10)
    run(" -2.5e-10 ", -2.5e-10)
    run(" 2.5e+10 ", 2.5e+10)
    run(" -2.5e+10 ", -2.5e+10)

    run('"asd"', "asd")

    run("true", True)
    run("false", False)
    run("null", None)


def test_suffixes() -> None:
    run("2.5k", 2500)
    run("2.5M", 2500000)
    run("2.5G", 2500000000)
    run("2.5T", 2500000000000)
    run("2.5P", 2500000000000000)
    run("2.5E", 2500000000000000000)
    run("2pi", 6.283185307179586)

    run('"ff"hex', 0xff)
    run('"A74FF"hex', 0xa74ff)


def test_array() -> None:
    run("[]", [])
    run("[2 3 5]", [2, 3, 5])
    run("[2 3 [\"æ\" null] false]", [2, 3, ["æ", None], False])


def test_arithmetic() -> None:
    run("2 + 3", 5)
    run("2 - 3", -1)
    run("2 * 3", 6)
    run("2 / 3", 2 / 3)
    # run("2 // 3", 2 // 3)
    run("2 % 3", 2 % 3)
    run("2 ** 3", 8)
    run("2 + 3 * 5", 17)
    run("2 * 3 + 5", 11)
    run("2 * 3 + 5 * 7", 41)

    run("2 * (3 + 5)", 16)
    run("2 * (3 + 5) / 4", 4)
    # run("2 * (3 + 5) // 4", 4)
    run("2 * (3 + 5) % 4", 0)
    run("2 * (3 + 5) ** 2", 128)


def test_arith_array() -> None:
    run("[2 3 + 5 7]", [2, 8, 7])


def test_comparison() -> None:
    run("2 == 3", False)
    run("2 != 3", True)
    run("2 < 3", True)
    run("2 <= 3", True)
    run("2 > 3", False)
    run("2 >= 3", False)
    run("2 == 2", True)
    run("2 != 2", False)
    run("2 < 2", False)
    run("2 <= 2", True)
    run("2 > 2", False)
    run("2 >= 2", True)
    run("2 == 1 + 1", True)
    run("2 != 1 + 1", False)
    run("2 < 1 + 1", False)
    run("2 <= 1 + 1", True)


def test_logical() -> None:
    run("true && true", True)
    run("true && false", False)
    run("false && true", False)
    run("false && false", False)
    run("true || true", True)
    run("true || false", True)
    run("false || true", True)
    run("false || false", False)
    run("{not true}", False)
    run("{not false}", True)
    run("{not 2}", False)
    run("{not 0}", True)
    run("{not \"\"}", True)
    run("{not \"asd\"}", False)
    run("{not []}", True)
    run("{not [2]}", False)


# def test_bitwise() -> None:
#     run("2 &&& 3", 2 & 3)
#     run("2 ||| 3", 2 | 3)
#     run("2 ^ 3", 2 ^ 3)
# #    run("~2", ~2)
#     run("2 << 3", 2 << 3)
#     run("2 >> 3", 2 >> 3)


# def test_string() -> None:
#     run("2 + \"asd\"", "2asd")
#     run("\"asd\" + 2", "asd2")
#     run("\"asd\" + \"qwe\"", "asdqwe")
#     run("\"asd\" + 2 + \"qwe\"", "asd2qwe")

