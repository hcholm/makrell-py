import os
import sys

here_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.join(here_dir, "..", "..")
sys.path.append(root_dir)

import importlib
from makrell.makrellpy.compiler import exec_file, eval_src
import makrell.makrellpy.repl as repl
import makrell


def print_help():
    print("usage: makrell [-h] [-m] [-c CODE] [FILE]")


def main():
    args = sys.argv[1:]

    if len(args) == 0:
        repl.run()
        return
    
    if args[0] == "-m" and len(args) == 2:
        sys.path.append('.')
        print("importlib.import_module", args[1])
        importlib.import_module(args[1])
        return
    
    if args[0] == "-c" and len(args) == 2:
        r = eval_src(args[1])
        if r is not None:
            print(r)
        return
    
    if args[0] == "-h" or args[0] == "--help":
        print_help()
        return

    if args[0] == "-v" or args[0] == "--version":
        print(f"Makrell: {makrell.__version__}")
        return
    
    if len(args) == 1:
        exec_file(args[0])
        return
    
    print_help()


if __name__ == '__main__':
    main()
