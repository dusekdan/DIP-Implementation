import os, re
import requests
from time import sleep

import core.utils as utils
import core.config as cfg
from core import constants as Consts
from core.helpers import URLHelper
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from . import Presenter as p

class XSSFinder():
    """
        XSSFinder module takes reflected and hidden parameters as its input
        and then checks these parameters on reflected XSS vulnerability.

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
            {   "depends_on": "RequestMiner",
                "dependency_type": "output",
                "is_essential": True },
        ]
        self.module_name = "XSSFinder"
        self.requestminer_results = {}
        self.URLHelper = URLHelper()
        self.DELAY = 0.1
        self.results = {}


    def mprint(self, string):
        """Module-specific print wrapper."""
        print(" [%s]: %s" % (self.module_name, string))


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
        self.mprint("Looking for XSS...")
        self.target = param

        group1, group2 = self.get_reflected_params()

        discovered_xss = []
        for param, meta in group1.items():
            for url in meta["reflects_on"]:
                discovered_xss += self.reflects_XSS(url, param)
        
        for param, meta in group2.items():
            for url in meta["reflects_on"]:
                discovered_xss += self.reflects_XSS(url, param)
        
        self.fprint(discovered_xss)
        self.results = discovered_xss

        self.mprint("XSS search done...")


    def reflects_XSS(self, url, param):
        """Check whether there is a reflected XSS in parameter on given URL."""
        discovered = []
        detector_string = '<"\'>'

        start_sep = utils.get_rnd_string(8)
        end_sep = utils.get_rnd_string(8)
        payload = start_sep + detector_string + end_sep 

        target = self.URLHelper.update_query_string_param(url, param, payload)

        self.fprint("XSS-Checking: %s" % target)

        try:
            # Acquire response for given payload for further inspection.
            r = self._retry_session().get(target)
            sleep(self.DELAY)
        except requests.exceptions.RequestException as e:
            print("Exception occurred when sending a request.")
            print(e)
            return []

        # XSS is only possible when content around it is of text/html c-type.
        if not r.headers['content-type'] or \
            not r.headers['content-type'].strip().startswith('text/html'):
            self.mprint("XSS Reflection check skipped (content-type is missing or not text/html).")
            self.mprint("(%s)" % url)
            return []

        # Locate reflections
        reflections = utils.find_all_between_str(r.text, start_sep, end_sep)
        if len(reflections) > 0:
            ref_index = 0
            for ref in reflections:
                protection_level = self.detect_protection_level(
                    detector_string, ref.strip()
                )

                # Unsanitized reflection requires no more testing.
                if protection_level == "None":
                    self.mprint("Parameter %s is vulnerable to XSS." % param)
                    discovered.append(
                        self.craft_discovered_XSS_object(url, param, "None")
                    )
                else:
                    # Classify XSS based on whether sanitization was a success
                    # or a RMS Tayleur-class failure.
                    discovered.append(
                        self.classify_XSS(url, r, param, ref, protection_level,
                        start_sep, end_sep, ref_index)
                    )

                ref_index += 1
        else:
            # Maybe more simple payload will trigger some response.
            self.mprint("Complex check did not trigger desired response. Trying more simple payload.")
            try:
                target = self.URLHelper.update_query_string_param(url, param, detector_string)
                r = self._retry_session().get(target)
            except requests.exceptions.RequestException:
                self.mprint("[ERROR] Exception occurred when sending a request.")
                self.fprint(repr(e))
                return []

            if detector_string in r.text:
                discovered.append(
                    self.craft_discovered_XSS_object(url, param, "None")
                )
        
        return [x for x in discovered if x != Consts.EMPTY_OBJECT]


    def detect_protection_level(self, detector_string, reflection):
        """
        Based on reflection received from the target determines what level of 
        protection against XSS is implemented.
        """
        # Completely unsanitized reflection == sure-fire XSS
        if reflection == detector_string:
            return "None"
        else:
            # Reflected payload was changed, we need to determine how much 
            ref = reflection
            
            if  '<' not in ref and '>' not in ref and \
                '"' not in ref and "'" not in ref:
                return "Encoded"
            elif    '<' not in ref and '>' not in ref and \
                    '"' in ref and "'" in ref:
                return "EncodedForHTML"
            elif    '"' not in ref and "'" not in ref:
                return "EncodedForAttributes"

            # Some modification was done to the payload but it is not
            # one of the known protection approaches.
            return "OtherwiseModified"


    def craft_discovered_XSS_object(self, url, param, protection_type, context=None):
        """Creates discovered XSS object out of its properties."""
        if context:
            return {
                "url": url,
                "param": param,
                "protection": protection_type,
                "context": context
            }
        return {
            "url": url,
            "param": param,
            "protection": protection_type,
        }


    def classify_XSS(
        self, url, response, param, reflection,
        protection_level, start_sep, end_sep, ref_index):
        """
        Based on the reflections and their context classifies XSS and returns
        either vulnerable places with their type and optionally context, or
        returns an empty object.
        """
        # Get index of the n-th openinig adn n-th closing separator
        start_index = utils.find_nth(start_sep, response.text, ref_index+1)
        end_index = utils.find_nth(end_sep, response.text, ref_index+1)
        
        # Acquire boundaries immediatelly next to payload
        lh_bound = response.text[start_index-3:start_index]
        rh_bound = response.text[end_index+len(end_sep):end_index+len(end_sep)+3]
        param_bound_end = param[len(param)-2:] + '='
        
        ctx = self.get_XSS_context(lh_bound, rh_bound, param_bound_end)

        if ctx == 'ATTR':
            # We need " or ' to be reflected (to decrease false positives
            # require both to be reflected.)
            if "'" in reflection and '"' in reflection:
                return self.craft_discovered_XSS_object(url, param, protection_level, context=ctx)
        else:
            # We need < and/or > for XSS.
            if ">" in reflection and "<" in reflection:
                return self.craft_discovered_XSS_object(url, param, protection_level, context=ctx)
        
        return Consts.EMPTY_OBJECT


    def get_XSS_context(self, lh_bound, rh_bound, param_bound_end):
        """
        Determines in what context was the XSS detector payload rendered. 

        TAG context = XSS is rendered outside HTML tag attribute
        ATTR context = XSS is rendered as a value of an HTML tag attribute

        From implementation point of view, it is always TAG context, unless
        there is an evidence of it being rendered inside the attribute.
        """
        ctx = 'TAG'
        # Cover low-hanging attr scenarios (if not an attribute, go with body)
        if  lh_bound[2] == '"' and rh_bound[0] == '"' or \
            lh_bound[2] == "'" and rh_bound[0] == "'":
            # Wrapped in quotes -> still can be just reflected search
            if '=' in lh_bound[:2]:
                # Decent chance we are in an attribute
                ctx = 'ATTR'
            if bool(re.search(r"(\s{2}|(\s[a-zA-Z]))", rh_bound[1:])):
                # Covers all the possible 2-character sequences following 
                # attr context.
                ctx = 'ATTR'
        
        # Scenarios where while reflection is inside the attribute, it is 
        # not enclosed in quotes/apostrophes.
        
        if ("'>" == rh_bound[:2] or '">' == rh_bound[:2]) and \
            lh_bound == param_bound_end:
            # Covers scenario when reflection is before the tag closes
            # e.g. current URL is reflected into the page.
            ctx = 'ATTR'            
        
        return ctx


    def get_reflected_params(self):
        """Extracts reflected parameters from RequestMiner results structure."""
        parsable = self.requestminer_results["parsable"]
        return (
            self.filter_reflected_only(parsable["existing_params"]), 
            self.filter_reflected_only(parsable["hidden_params"], False)
        )


    def filter_reflected_only(self, param_struct, existing=True):
        """Returns only parameter records that reflect."""
        filtered = {}
        if existing:
            for param, record in param_struct.items():
                if record["reflects"]:
                    filtered[param] = record
        else:
            # Reflected parameters structure needs to be unified with 
            # existing reflected parameters structure.
            # TODO: Maybe address this in RequestMiner already?
            for param in param_struct["reflected"]:
                reflects_on = [
                    self.URLHelper.add_query_string_param(
                    param_struct["source_url"], param, "any")
                ]
                filtered[param] = {
                    "sources": [],
                    "values": [],
                    "reflects": True,
                    "reflects_on": reflects_on
                }
        
        return filtered


    def provide_results(self, results_structure):
        """
        Allows XSSFinder to access results of other modules. XSSFinder makes
        a copy of results provided by the modules it is dependent on.
        """
        if "RequestMiner" in results_structure.keys():
            self.requestminer_results = results_structure["RequestMiner"]["results"]

    
    def get_results(self):
        """Provides module artifacts back to module launcher to be shared."""
        return {
            "parsable": {},
            "nonparsable": {
                "discovered_xss": self.results,
            }
        }


    def set_options(self, options):
        """Sets options for a module."""
        if "DELAY" in options:
            self.DELAY = options["DELAY"]


    def get_dependencies(self):
        """Provides information about the module's dependency requirements."""
        return self.dependencies


    def get_presenter(self, results):
        """Prepares module's presenter with results structure."""
        self.presenter = p.Presenter(results)
        return self.presenter


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