from importlib import import_module as __import_module
from sys import argv as __argv

from src.library.util import kebab_to_snake_case as __kebab_to_snake_case

if __name__ == "__main__":
    __argv.pop(0)
    __module_name = __kebab_to_snake_case(f"script.{__argv[1]}")
    __executable = __import_module(__module_name)
    __executable.execute()
