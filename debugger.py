import sys

class DEBUG():

    def __init__(self, DEBUG_ENABLED = False):
        self.enabled = DEBUG_ENABLED

    def discovered_modules_DEPRECATED(self, discovered_modules):
        if (self.enabled):
            print(" Discovered modules:")
            for module in discovered_modules:
                print("\t|-> %s" % module)
    
    def discovered_modules(self):
        all_modules = sys.modules.keys()
        print(" Discovered modules:")
        for module_name in all_modules:
            if module_name.startswith('modules.') and module_name.count('.') == 1:
                print("\t|-> %s" % module_name)

    def importing_module(self, module_name):
        if (self.enabled):
            print(" Importing module: %s" % module_name)
    
    def starting_module(self, module_name):
        if (self.enabled):
            print(" Attempting to start module: %s" % module_name)

    def imported_modules(self):
        if (self.enabled):
            filtered = ['builtins', 'sys', '_frozen_importlib', 
            '_imp', '_warnings', '_thread', '_weakref', '_frozen_importlib_external',
            '_io', 'marshal', 'nt', 'winreg', 'zipimport', 'encodings', 'codecs',
            '_codecs', 'encodings.aliases', 'encodings.utf_8', '_signal', '__main__',
            'encodings.latin_1', 'io', 'abc', '_weakrefset', 'site', 'os', 'errno', 
            'stat', '_stat', 'ntpath', 'genericpath', 'os.path', '_collections_abc',
            '_sitebuiltins', 'sysconfig', '_bootlocale', '_locale', 'encodings.cp1250',
            'types', 'functools', '_functools', 'collections', 'operator', '_operator',
            'keyword', 'heapq', '_heapq', 'itertools', 'reprlib', '_collections', 'weakref',
            'collections.abc', 'encodings.cp437', 'importlib', 'importlib._bootstrap',
            'importlib._bootstrap_external', 'warnings', 'debugger'
            ]
            all_modules = sys.modules.keys()
            print(
                list(filter(lambda x: x not in filtered, all_modules))
            )
