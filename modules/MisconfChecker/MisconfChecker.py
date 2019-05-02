import os
import requests
import core.config as cfg
from core.helpers import URLHelper
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from . import Presenter as p
from . import DLDetector as _DLD
from . import HRLocator as _HRL

class MisconfChecker():
    """
        MisconfChecker looks for VCS and IIS misconfiguration on a target, such
        as enabled directory listing, leftover .git/.svn/.hg files and also
        hidden resources that are available, but not linked from the app.

        |>  This software is a part of the master thesis: 
        |>  "Web Application Penetration Testing Automation"
        |>  Brno, University of Technology, 2019
        |
        |>  Author: Daniel Dušek (@dusekdan - github, gitlab, twitter)
        |>  Contact: dusekdan@gmail.com
        |>  https://danieldusek.com
    """

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
        self.fprint(string)

    
    def fprint(self, string):
        """Write into the current log file instead of STDOU."""
        file_name = os.path.join(".", "output", cfg.CURRENT_RUN_ID, "run.log")
        message = " [%s]: %s" % (self.module_name, string)
        try:
            with open(file_name, 'a') as f:
                f.write(message + '\n')
        except IOError:
            print("[DBG-ERROR] Unable to write to file: %s" % file_name)


    def execute(self, param):
        self.mprint("Checking IIS/VCS misconfigurations...")
        self.target = param

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
        self.fprint("Discovered following resources: %s" % self.resources)
        self.fprint("Discovered following VCS resources: %s" % self.vcs_resources)
        self.fprint("Detected directory listing in: %s" % self.directory_listing)

        self.mprint("Discovered resources: %s | VCS: %s | Directory Listing: %s" %(
            len(self.resources),
            len(self.vcs_resources),
            len(self.directory_listing)))
        self.mprint("Misconfiguration checks done.")


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
