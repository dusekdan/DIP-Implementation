import os
import importlib

class ModuleLoader:

    def __init__(self, modules_folder):
        print("Initialized module loader")
        self.modules_folder = modules_folder

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

        return instantiated_modules
