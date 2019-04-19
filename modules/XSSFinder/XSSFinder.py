import os

import core.utils as utils
import core.config as cfg
from core import constants as Consts

class XSSFinder():

    def __init__(self):
        self.dependencies = [
            {   "depends_on": "RequestMiner",
                "dependency_type": "output",
                "is_essential": True },
        ]
        self.module_name = "XSSFinder"
        self.requestminer_results = {}


    def mprint(self, string):
        """Module-specific print wrapper."""
        print(" [%s]: %s" % (self.module_name, string))


    def execute(self, param):
        self.mprint("===================================%s===================================" % self.module_name)
        self.target = param


        self.mprint("Discovering XSS or at least trynna to...")


        self.mprint("===================================%s===================================" % self.module_name)


    def provide_results(self, results_structure):
        """
        Allows XSSFinder to access results of other modules. XSSFinder makes
        a copy of results provided by the modules it is dependent on.
        """
        if "RequestMiner" in results_structure.keys():
            self.requestminer_results = results_structure["RequestMiner"]["results"]

    
    def get_results(self):
        """Provides module artifacts back to module launcher to be shared."""
        # TODO: Return actual results.
        return Consts.DUMMY_MODULE_RESULTS


    def get_dependencies(self):
        return self.dependencies


    def leaves_physical_artifacts(self):
        return False