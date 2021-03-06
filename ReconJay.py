"""
    ReconJay Tool for non-destructive and non-permanent trace leaving 
    penetration testing.

    |>  This software is a part of the master thesis: 
    |>  "Web Application Penetration Testing Automation"
    |>  Brno, University of Technology, 2019
    |
    |>  Author: Daniel Dušek (@dusekdan - github, gitlab, twitter)
    |>  Contact: dusekdan@gmail.com
    |>  https://danieldusek.com
"""
import os
import sys
import importlib
import core.config as cfg
from core import utils 
from core.helpers import PresentationHelper
from core.module_loader import ModuleLoader
from debugger import DEBUG

DBG = DEBUG(DEBUG_ENABLED=True)
dprint = DBG.dprint
fprint = DBG.fprint

MODULES_FOLDER = "modules"
cfg.CURRENT_RUN_ID = utils.generate_run_id()
utils.prepare_tool_environment(cfg.CURRENT_RUN_ID)

# FUTURE: Think about the way I am retrieving the target and remove default WP
if len(sys.argv) >= 2:
    run_target = sys.argv[1]
else:
    dprint(" [!] Target URL was not specified. The tool will run against danieldusek.com")
    dprint(" [!] Pass the target application's URL as the first parameter (python ReconJay.py https://target.url)")
    run_target = "https://danieldusek.com"

# 1 - Discover modules

ML = ModuleLoader(MODULES_FOLDER)
options = ML.load_module_options()
instantiated_modules = ML.discover_modules()
DBG.discovered_modules()

# 2 - Classify modules by their ability to be run

independent, satisfiable, nonrunnable = ML.classify_modules(instantiated_modules)
DBG.classified_modules(independent, satisfiable, nonrunnable)

# 3 - Run independent modules and store run outputs

modules_done = {}
module_results = {}

for module_name, instance in independent.items():
    
    physical_artifacts = instance.leaves_physical_artifacts()
    if physical_artifacts:
        utils.prepare_module_folder(module_name)

    if module_name in options:
        instance.set_options(options[module_name])

    exit_flag = instance.execute(run_target)
    results = instance.get_results()
    
    module_results[module_name] = {
        "exit_flag": exit_flag,
        "results": results,
        "left_physical_artifacts": physical_artifacts
    }
    

    dprint(" [I] Module %s finished and saved results." % module_name)
    modules_done[module_name] = instance

dprint(" [I] Independent run finished.")

# 4 - Check and run satisfiably dependent modules

try_again = True
while try_again:

    try_again = False

    for module_name, instance in satisfiable.items():
        required_dependencies = instance.get_dependencies()

        can_run = True
        for dependency in required_dependencies:
            if dependency["depends_on"] not in module_results.keys():
                dprint(" [W] Some modules can not be run. Dependency is not present in module_results.")
                dprint("\t %s -> %s" % (module_name, dependency["depends_on"]))
                nonrunnable[module_name] = "Circular or non-existent dependency."
                can_run = False
                break
        
        if can_run:
            
            if module_name in options:
                instance.set_options(options[module_name])
            
            instance.provide_results(module_results)
            exit_flag = instance.execute(run_target)
            results = instance.get_results()
            physical_artifacts = instance.leaves_physical_artifacts()

            module_results[module_name] = {
                "exit_flag": exit_flag,
                "results": results,
                "left_physical_artifacts": physical_artifacts
            }

            modules_done[module_name] = instance

            try_again = True
    
    # Remove modules that were already run (their result is recorded in module_results)
    for module_name in module_results.keys():
        satisfiable.pop(module_name, None)

ML.show_module_loading_errors(nonrunnable)

# 5 - Compose OSINT Report and other output artifacts from modules
report_name = "Vulnerability Report (%s)" % (cfg.CURRENT_RUN_ID)
PH = PresentationHelper(report_name)
presentation_options = {
    "show_module_description": True
}
PH.set_options(presentation_options)
report_type = "BWFormal"
for module_name, instance in modules_done.items():
    fprint(" [I] Calling presenter on module: %s, required style: %s" % (module_name, report_type))
    presenter = instance.get_presenter(module_results)
    presentable = presenter.present_content(report_type)
    PH.add_part(module_name, presentable["description"], presentable["content"], presenter.get_importance())

dprint(" [I] Result parts obtained from presenters, generating final report...")
PH.generate_report(report_type, run_target)