import os
import sys
import importlib
from core import utils 
from core.module_loader import ModuleLoader

from debugger import DEBUG
DBG = DEBUG(DEBUG_ENABLED=True)


MODULES_FOLDER = "modules"

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
    
    exit_flag = instance.execute("https://danieldusek.com")
    results = instance.get_results()
    physical_artifacts = instance.leaves_phisical_artifacts()
    
    module_results[module_name] = {
        "exit_flag": exit_flag,
        "results": results,
        "left_physical_artifacts": physical_artifacts
    }

    print("[I] Module %s finished and saved results." % module_name)

print("[I] Independent run finished.")

# 4 - Check whether it is possible to run satisfiably dependent modules

try_again = False
# TODO: This needs to be wrapped in while loop until try again == False (update the condition)
for module_name, instance in satisfiable.items():
    
    required_dependencies = instance.get_dependencies()
    
    can_run = True
    for dependency in required_dependencies:
        if dependency["depends_on"] not in module_results.keys():
            can_run = False
            print("[W] Some modules can not be run. Dependency is not present in module_results.")
            print("\t %s -> %s" % (module_name, dependency["depends_on"]))
            break
    
    if can_run:
        exit_flag = instance.execute("https://danieldusek.com")
        results = instance.get_results()
        physical_artifacts = instance.leaves_phisical_artifacts()

        module_results[module_name] = {
            "exit_flag": exit_flag,
            "results": results,
            "left_physical_artifacts": physical_artifacts
        }

        try_again = True
    
    if try_again == False:
        print("[W] Some modules can not be run. Maybe there is a circular dependency?")


# 3 - Run them via standardized calls (Is this called the API?) 
# # TODO: Make this follow process flow described in module.loading.strategy.md
#for module_name, instance in instantiated_modules.items():
#    DBG.starting_module(module_name)
#    instance.execute()



# TODO: X - Optional: Verify loaded modules are in standardized shape (have proper methods etc.)
# If this todo is not worked in, loading will start to fail once the improperly written modules
# start to appear. Huge except-catch potential here.



# Old code fragmets. To be deleted, due 10th April, 2019

# 1 - Obtain existing modules from modules folder.
#discovered_modules = [m for m in os.listdir(modules_folder) if os.path.isdir(modules_folder + "/" + m)]
#DBG.discovered_modules(discovered_modules)