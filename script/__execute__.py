import importlib
import sys

if __name__ == "__main__":
    sys.argv.pop(0)
    # NOTE: Convert kebab case to snake case
    __module_name = f"script.{sys.argv[0]}".replace("-", "_")
    __executable = importlib.import_module(__module_name)
    __executable.execute(*sys.argv[1:])
