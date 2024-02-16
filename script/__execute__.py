import importlib
import sys

import humps

__module_name = humps.decamelize(humps.camelize(f"script.{sys.argv[1]}"))
__executable = importlib.import_module(__module_name)
__executable.execute()
