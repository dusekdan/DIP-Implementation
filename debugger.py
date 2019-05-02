"""
    ReconJay Tool for non-destructive and non-permanent trace leaving 
    penetration testing - auxiliary debugging class.

    |>  This software is a part of the master thesis: 
    |>  "Web Application Penetration Testing Automation"
    |>  Brno, University of Technology, 2019
    |
    |>  Author: Daniel Dušek (@dusekdan - github, gitlab, twitter)
    |>  Contact: dusekdan@gmail.com
    |>  https://danieldusek.com
"""
import os, sys
import types
import core.config as cfg

class DEBUG(object):


    def __init__(self, DEBUG_ENABLED = False):
        self.enabled = DEBUG_ENABLED


    def __getattribute__(self, attr):
        """Prevents methods from executing when DEBUG is disabled."""
        if object.__getattribute__(self, "enabled"):
            method = object.__getattribute__(self, attr)
            if not method:
                raise Exception("Method %s is not implemented." % attr)
            return method
        else:
            return object.__getattribute__(self, "__empty__")


    def __empty__(self, *argv):
        """Replacement method called instead of actual functional methods when
        debug is set to False"""
        pass


    def dprint(self, string):
        """Conditionally executed print function."""
        if self.enabled:
            print(string)


    def fprint(self, string):
        """Write into the current log file instead of STDOU."""
        file_name = os.path.join(".", "output", cfg.CURRENT_RUN_ID, "run.log")
        try:
            with open(file_name, 'a') as f:
                f.write(string + '\n')
        except IOError:
            print("[DBG-ERROR] Unable to write to file: %s" % file_name)


    def discovered_modules(self):
        all_modules = sys.modules.keys()
        self.fprint(" [D] Discovered modules:")
        for module_name in all_modules:
            if module_name.startswith('modules.') and module_name.count('.') == 1:
                self.fprint("\t|-> %s" % module_name)


    def classified_modules(self, independent, satisfiable, nonrunnable):
        self.dprint(" [D] Module classification done.")

        self.dprint("  Independent modules: ")
        for module_name, instance in independent.items():
            self.dprint("\t|-> %s" % module_name)
        
        self.dprint("  Potentially satisfiable modules: ")
        for module_name, instance in satisfiable.items():
            self.dprint("\t|-> %s" % module_name)
        
        if len(nonrunnable) > 0:
            self.dprint("  Non-runnable modules: ")
            for module_name, reason in nonrunnable.items():
                self.dprint("\t|-> %s (%s)" % (module_name, reason))


    def importing_module(self, module_name):
        self.dprint(" Importing module: %s" % module_name)


    def starting_module(self, module_name):
        self.dprint(" Attempting to start module: %s" % module_name)


    def imported_modules(self):
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
        self.dprint(
            list(filter(lambda x: x not in filtered, all_modules))
        )
