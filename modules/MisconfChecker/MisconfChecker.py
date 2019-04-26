import os
import requests

from core.helpers import URLHelper
from . import Presenter as p
from . import DLDetector as _DLD
from . import HRLocator as _HRL

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class MisconfChecker():


    def __init__(self):
        self.dependencies = [
        {
            "depends_on": "SiteCopier",
            "dependency_type": "output",
            "is_essential": True
        }
        ]
        self.module_name = "MisconfChecker"
        self.sitecopier_results = {}

        self.directory_listing = []

        self.URLHelper = URLHelper()

        self.DELAY = 0.1

        """Structures to hold findings discovered by the scan."""
        self.resources = []
        self.vcs_resources = []
        self.directory_listing = []


    def mprint(self, string):
        """Module-specific print wrapper."""
        print(" [%s]: %s" % (self.module_name, string))


    def execute(self, param):
        self.mprint("===================================%s===================================" % self.module_name)
        self.target = param
        self.mprint("Executing %s module!" % self.module_name)

        # Hidden resources & VCS leftover resources discovery
        HRL = _HRL.HiddenResourcesLocator(self.target)
        self.mprint("Locating hidden resources...")
        self.resources, self.vcs_resources = HRL.discover_hidden_resources()
        
        # Enabled directory listing discovery
        sc_artifacts = self.sitecopier_results["parsable"]["anyProcessor"][0]
        urls_seen = (
            sc_artifacts["crawledUrls"] + sc_artifacts["failedUrls"] + 
            self.resources + self.vcs_resources
        )
        DLD = _DLD.DLDetector(urls_seen, self.target)
        self.mprint("Searching for enabled directory listing...")
        self.directory_listing = DLD.detect_directory_listing()

        # Debug only outputs.
        self.mprint("Discovered following resources: %s" % self.resources)
        self.mprint("Discovered following VCS resources: %s" % self.vcs_resources)
        self.mprint("Detected directory listing in: %s" % self.directory_listing)

        self.mprint("===================================%s===================================" % self.module_name)


    def provide_results(self, results_structure):
        """
        Allows MisconfChecker to access results of other modules. MisconfChecker
        makes a copy of results provided by the modules it is dependent on.
        """
        if "SiteCopier" in results_structure.keys():
            self.sitecopier_results = results_structure["SiteCopier"]["results"]


    def get_results(self):
        """Provides module artifacts back to module launcher to be shared."""
        return {
            "nonparsable": {
                "hidden_resources": self.resources,
                "vcs_resources": self.vcs_resources,
                "directory_listing": self.directory_listing,
            },
            "parsable": {}
        }


    def get_dependencies(self):
        """Provides information about the module's dependency requirements."""
        return self.dependencies


    def get_presenter(self, results):
        """Prepares module's presenter with results structure."""
        self.presenter = p.Presenter(results)
        return self.presenter


    def set_options(self, options):
        """Sets options for a module."""
        if "DELAY" in options:
            self.DELAY = options["DELAY"]
        if "RANDOMIZE_SELECTION" in options:
            self.RANDOMIZE_SELECTION = bool(options["RANDOMIZE_SELECTION"])
        if "MAX_REQUESTS" in options:
            self.MAX_REQUESTS = options["MAX_REQUESTS"]


    def leaves_physical_artifacts(self):
        """Does the module leave artifacts phisically on filesystem?"""
        return False


    def _retry_session(self, 
        retries = 5, 
        backoff_factor = 0.3, 
        status_forcelist = (500,502,503,504),
        session = None):
        """
        Gets a retry session with default parameters unless specifically
        requested otherwise.
        """
        session = session or requests.Session()
        retry = Retry(
            total= retries, read = retries, connect = retries,
            backoff_factor = backoff_factor, status_forcelist = status_forcelist
        )

        adapter = HTTPAdapter(max_retries = retries)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
