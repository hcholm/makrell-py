
from makrell.makrellpy.compiler import eval_src


def _test_mr_import_py():
    src = """
    {import $.interop1}
    {interop.add 2 3}
    """
    res = eval_src(src)
    assert res == 5
