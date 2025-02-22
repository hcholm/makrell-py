import os
from makrell.ast import CurlyBrackets, Identifier, Sequence
from makrell.baseformat import src_to_baseformat
from makrell.tokeniser import regular
from makrell.makrellpy.compiler import exec_nodes


mr_files = [
    'test_funcs.mr',
    'test_special_constructs.mr',
    'test_core.mr',
    'test_meta.mr',
    'test_classes.mr',
    'test_flow.mr',
    'test_estrings.mr',
    'test_coroutines.mr',
    'test_patmatch.mr',
]


here_dir = os.path.dirname(os.path.abspath(__file__))


def get_test_blocks(filename):
    tests_path = os.path.join(here_dir, filename)
    print(f"Processing file: {tests_path}")
    setup = None
    blocks = []
    with open(tests_path, encoding='utf-8') as f:
        src = f.read()
        ns = src_to_baseformat(src)
        for n in regular(ns):
            if not isinstance(n, CurlyBrackets):
                continue
            tns = regular(n.nodes)
            if len(tns) < 2:
                continue
            if not isinstance(tns[0], Identifier):
                continue
            if tns[0].value == "setup":
                setup = tns[1:]
            elif tns[0].value == "test":
                name = tns[1].value[1:-1]
                rest = tns[2:]
                if setup is not None:
                    rest = setup + rest
                seq = Sequence(rest)
                # assert False
                blocks.append((filename[:-3], name, seq))
    return blocks


def pytest_generate_tests(metafunc):
    if "name" in metafunc.fixturenames:
        blocks = []
        for mr_file in mr_files:
            test_blocks = get_test_blocks(mr_file)
            blocks.extend(test_blocks)

        metafunc.parametrize("filename, name, seq", blocks)


def test_func(filename, name, seq):
    print(f"Test: {filename}/{name}")
    exec_nodes(seq)
