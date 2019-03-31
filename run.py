import os
import sys
import importlib
from core import utils 
from core.module_loader import ModuleLoader

from debugger import DEBUG

modules_folder = "modules"
DBG = DEBUG(DEBUG_ENABLED=True)

ML = ModuleLoader(modules_folder)
instantiated_modules = ML.discover_modules()

# DBG.imported_modules()
DBG.discovered_modules()

# 3 - Run them via standardized calls (Is this called the API?) 
# # TODO: Make this follow process flow described in module.loading.strategy.md
for module_name, instance in instantiated_modules.items():
    DBG.starting_module(module_name)
    instance.execute()



# TODO: X - Optional: Verify loaded modules are in standardized shape (have proper methods etc.)
# If this todo is not worked in, loading will start to fail once the improperly written modules
# start to appear. Huge except-catch potential here.



# Old code fragmets. To be deleted, due 10th April, 2019

# 1 - Obtain existing modules from modules folder.
#discovered_modules = [m for m in os.listdir(modules_folder) if os.path.isdir(modules_folder + "/" + m)]
#DBG.discovered_modules(discovered_modules)