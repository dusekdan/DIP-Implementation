import os
import importlib

class ModuleLoader:

    def __init__(self, modules_folder):
        print("Initialized module loader")
        self.modules_folder = modules_folder
        self.available_dependencies = []

    def discover_modules(self, do_not_import = False):
        """
        Imports tool modules from the given module folder.

        When it is desirable to return only names of the discovered modules, 
        optional parameter do_not_import can be specified to prevent discovered
        modules from being imported.

        Implementation was inspired by the following sources:
         |-> https://stackoverflow.com/a/301146
         |-> https://stackoverflow.com/a/4821120
        """
        discovered_modules = [
            m for m in os.listdir(self.modules_folder) 
            if os.path.isdir(self.modules_folder + "/" + m)
        ]
        
        if do_not_import:
            return discovered_modules

        instantiated_modules = {}
        for module in discovered_modules:
            module_path = self.modules_folder + "." + module + "." + module
                
            imported_module = importlib.import_module(module_path)

            instantiable = getattr(imported_module, module)
            instantiated_modules[module] = instantiable()
            
            # Update internal information about dependencies that are available.
            self.available_dependencies.append(module)

        return instantiated_modules
    
    def classify_modules(self, modules):
        """
        Classifies modules into following categories:
            - independent
            - satisfiable
            - nonrunnable
        
        Based on the dependencies that the given module needs to have in order
        to be run.
        """
        NO_DEPENDENCIES = []
       
        independent = {}
        satisfiable = {}
        nonrunnable = {}

        for module_name, instance in modules.items():

            try: 
                current_dependencies = instance.get_dependencies()
            except AttributeError: 
                print("[E] Module '%s' does not implement get_dependencies() method (Invalid Module)" % module_name)
                nonrunnable[module_name] = "Module API invalid."
                continue

            if current_dependencies == NO_DEPENDENCIES:
                independent[module_name] = instance
                continue
            
            missing_dependencies = NO_DEPENDENCIES
            for dependency in current_dependencies:
                if dependency["depends_on"] not in self.available_dependencies:
                    missing_dependencies.append(dependency["depends_on"])
            
            if missing_dependencies != NO_DEPENDENCIES:
                nonrunnable[module_name] = "Missing dependencies: %s" % missing_dependencies
                continue
            
            satisfiable[module_name] = instance

        return (independent, satisfiable, nonrunnable)

    def show_module_loading_errors(self, errors):
        """Prints out information about why modules could not be imported/run."""
        print("\n There are modules that could not be run for the following reasons: ")
        for module_name, error in errors.items():
            print(" \tName: %s \tReason: %s" % (module_name, error))
        print()