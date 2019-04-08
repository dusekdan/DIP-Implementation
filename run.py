import os
import sys
import importlib
from core import utils 
from core.module_loader import ModuleLoader

from debugger import DEBUG
DBG = DEBUG(DEBUG_ENABLED=True)
dprint = DBG.dprint

utils.prepare_tool_environment()

MODULES_FOLDER = "modules"
CURRENT_RUN_ID = utils.generate_run_id()
sys.CURRENT_RUN_ID = CURRENT_RUN_ID

# TODO: Prepare directory for that run? Also utils responsibility? Or RunHelper?
os.mkdir("output/%s" % CURRENT_RUN_ID)


# 1 - Discover modules

ML = ModuleLoader(MODULES_FOLDER)
instantiated_modules = ML.discover_modules()
DBG.discovered_modules()

# 2 - Classify modules by its ability to be run

independent, satisfiable, nonrunnable = ML.classify_modules(instantiated_modules)
DBG.classified_modules(independent, satisfiable, nonrunnable)

# 3 - Run independent modules and store run outputs

module_results = {}

for module_name, instance in independent.items():
    
    exit_flag = instance.execute("https://danieldusek.com/")
    results = instance.get_results()
    physical_artifacts = instance.leaves_physical_artifacts()
    
    module_results[module_name] = {
        "exit_flag": exit_flag,
        "results": results,
        "left_physical_artifacts": physical_artifacts
    }

    dprint("[I] Module %s finished and saved results." % module_name)

dprint("[I] Independent run finished.")

# 4 - Check and run satisfiably dependent modules

try_again = True
while try_again:

    try_again = False

    for module_name, instance in satisfiable.items():
        required_dependencies = instance.get_dependencies()

        can_run = True
        for dependency in required_dependencies:
            if dependency["depends_on"] not in module_results.keys():
                dprint("[W] Some modules can not be run. Dependency is not present in module_results.")
                dprint("\t %s -> %s" % (module_name, dependency["depends_on"]))
                nonrunnable[module_name] = "Circular or non-existent dependency."
                can_run = False
                break
        
        if can_run:
            exit_flag = instance.execute("https://danieldusek.com")
            results = instance.get_results()
            physical_artifacts = instance.leaves_physical_artifacts()

            module_results[module_name] = {
                "exit_flag": exit_flag,
                "results": results,
                "left_physical_artifacts": physical_artifacts
            }

            try_again = True
    
    # Remove modules that were already run (their result is recorded in module_results)
    for module_name in module_results.keys():
        satisfiable.pop(module_name, None)

ML.show_module_loading_errors(nonrunnable)

# 3 - Run them via standardized calls (Is this called the API?) 
# # TODO: Make this follow process flow described in module.loading.strategy.md
#for module_name, instance in instantiated_modules.items():
#    DBG.starting_module(module_name)
#    instance.execute()



# TODO: X - Optional: Verify loaded modules are in standardized shape (have proper methods etc.)
# If this todo is not worked in, loading will start to fail once the improperly written modules
# start to appear. Huge except-catch potential here.