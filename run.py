import os
import sys
import importlib
from debugger import DEBUG
#from SiteMapper import SiteMapper
#from modules.Requester import Requester

modules_folder = "modules"
DBG = DEBUG(DEBUG_ENABLED=True)

# 1 - Obtain existing modules from modules folder.
discovered_modules = [m for m in os.listdir(modules_folder) if os.path.isdir(modules_folder + "/" + m)]
DBG.discovered_modules(discovered_modules)

# 2 - Import them using the importlib.import_module 
# |-> see https://stackoverflow.com/a/301146/3444151
# |-> see https://stackoverflow.com/a/4821120/3444151
instantiated_modules = {}
for module in discovered_modules:
    module_path = modules_folder + "." + module + "." + module
    DBG.importing_module(module_path)
    
    imported_module = importlib.import_module(module_path)

    instantiable = getattr(imported_module, module)
    instantiated_modules[module] = instantiable()

DBG.imported_modules()

# TODO: X - Optional: Verify loaded modules are in standardized shape (have proper methods etc.)
# If this todo is not worked in, loading will start to fail once the improperly written modules
# start to appear. Huge except-catch potential here.

# 3 - Run them via standardized calls (Is this called the API?)
for module_name, instance in instantiated_modules.items():
    DBG.starting_module(module_name)
    instance.execute()