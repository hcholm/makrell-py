import importlib.abc
import importlib.machinery
import os
import sys
import makrell.makrellpy.compiler as mrpy_compiler
from importlib.metadata import version

__version__ = version("makrell")

class MakrellLoader(importlib.abc.SourceLoader):

    def __init__(self, fullname, path):
        self.fullname = fullname
        self.path = path

    def get_filename(self, fullname):
        return self.path    
    
    def get_data(self, path: str):
        if path.endswith(".pyc"):
            with open(path, "rb") as f:
                data = f.read()
            return data
        with open(path, "r", encoding='utf-8') as f:
            data = f.read()
        return data

    def source_to_code(self, data, path, _optimize=-1):
        m = mrpy_compiler.src_to_module(data)
        c = compile(m, filename=path, mode="exec")
        return c


class MakrellFinder():

    def find_spec(self, fullname, path, target=None):
        if path is None:
            path = []
        if not isinstance(path, list):
            path = [path]
        path.append(os.getcwd())
        here_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.join(here_dir, "..")
        path.append(root_dir)

        for entry in path:
            if os.path.isdir(entry):
                fullname_parts = fullname.split('.')
                fullname_path = os.path.join(*fullname_parts)
                entry_path = os.path.join(entry, fullname_path)
                is_dir = os.path.isdir(entry_path)
                if is_dir:
                    mr_init = os.path.join(entry_path, '__init__.mr')
                    if os.path.exists(mr_init):
                        return importlib.machinery.ModuleSpec(
                            fullname, MakrellLoader(fullname, mr_init),
                            origin=entry_path, is_package=True)
                    py_init = os.path.join(entry_path, '__init__.py')
                    if os.path.exists(py_init):
                        return importlib.machinery.ModuleSpec(
                            fullname, MakrellLoader(fullname, py_init),
                            origin=py_init)
                filename = entry_path + '.mr'
                if os.path.exists(filename):
                    ms = importlib.machinery.ModuleSpec(
                        fullname, MakrellLoader(fullname, filename),
                        origin=filename)
                    return ms


sys.meta_path.append(MakrellFinder())
