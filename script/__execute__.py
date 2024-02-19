import importlib
import sys


def kebab_to_snake_case(string: str) -> str:
    return string.replace("-", "_")


__module_name = kebab_to_snake_case(f"script.{sys.argv[1]}")
__executable = importlib.import_module(__module_name)
__executable.execute()
