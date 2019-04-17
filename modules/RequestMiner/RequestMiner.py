import os
import random
import requests
import core.utils as utils
import core.config as cfg
from core.helpers import URLHelper

from urllib.parse import urlparse, urljoin, parse_qs, parse_qsl

class RequestMiner():

    def __init__(self):
        self.dependencies = [
            {
                "depends_on": "SiteCopier",
                "dependency_type": "output",
                "is_essential": True
            }
        ]
        self.module_name = "RequestMiner"
        self.sitecopier_results = {}

        self.URLHelper = URLHelper()

        self.CANARY_LENGTH = 8
        self.MAX_REFLECTION_REQUESTS = 10

        # struct[param] = {
        #   "sources": ['url1', 'url2', 'url3'],
        #   "values": ['value1', 'value2', 'value3'],
        #   "reflects": True|False|None
        #   "reflects_on": ['url1', 'url2']
        # }
        self.discovered_params = {}
        self.discovered_headers = []
    
    
    def mprint(self, string):
        print(" [%s]: %s" % (self.module_name, string))
    

    def execute(self, param):
        self.mprint("===================================%s===================================" % self.module_name)
        self.target = param

        self.mprint("Seaching for used query string parameters & headers...")
        source = os.path.join("output", cfg.CURRENT_RUN_ID, "SiteCopier")
        for id in range(len(os.listdir(source))):
            url = self.obtain_id_url(id)
            # TODO: uncomment this - commented out only for testing on dd.com
            #if not self.URLHelper.is_in_scope(self.target, url):
            #    continue
            response = os.path.join(source, str(id), "%s.response" % id)
            headers = "%s.headers" % response

            # Existing Parameter Discovery
            params = parse_qs(urlparse(url).query, keep_blank_values=True)
            self.mprint(
            "Discovered %s new parameters." % self.add_discovered_params(url, params)
            )

            # Existing Header Discovery
            discovered_headers = self.filter_common_headers(
            self.discover_headers(headers))
            self.mprint(
            "Discovered %s new headers." % self.add_discovered_headers(discovered_headers)
            )



        # ! Find hidden URL parameters
        # TODO: Fuzz discover URL params (probably on the most URL-param-rich sites?)
        # * IMPLEMENTATION OUTLINE
        # * - Determine what heuristic to use for 'mining' URL selection
        # * - Determine how to properly mine it (how to verify response, how to react to
        # * specific responses, how to 'pre-flight' it first)
        # * - How to record it: Separate hidden params structure vs Shared structure
        # * - 
        
        # ! Find hidden Headers
        # TODO: Fuzz discover headers



        
        # Go through the existing URL parameters and figure out whether some of
        # them are reflected into the response.
        for param_name, param_record in self.discovered_params.items():
            reflections = self.test_parameter_reflection(param_name, param_record)
            if reflections:
                # Update discovered qpars structure with reflects: True and reflects on.
                self.mprint("Parameter %s reflects!" % param_name)
                self.discovered_params[param_name]["reflects"] = True
                self.discovered_params[param_name]["reflects_on"] = reflections
            else:
                self.mprint("Nope, Param %s does not reflect." % param_name)


        # FUTURE: Evaluate security standing for discovered headers (will require
        # keeping values of the headers (not currently doing that... aaah))
        # Maybe this functionality will fit better under SSL eval module?
        
        # TODO: Check reflections on URL/Headers
        
        self.mprint("Request mining completed....")
        self.mprint("===================================%s===================================" % self.module_name)


    def test_parameter_reflection(self, parameter_name, parameter_record):
        """
        Checks under which condition the parameter is reflected in the response
        body using the randomly generated canary. Reflection is checked for all
        unique combinations of the given parameter and other parameters used
        together with it (as specified in sources).
        Alternatively, no further requests if MAX_REFLECTION_REQUESTS is 
        exceeded.
        """
        canary = utils.get_rnd_string(self.CANARY_LENGTH)
        url_classes = self.classify_param_sources(parameter_record["sources"])
        reflection_requests = 0
        reflects_on = []

        
        for url_class, values in url_classes.items():
            # Pick exactly 1 candidate from each group
            current_target = self.URLHelper.replace_parameter_value(values[0],
                parameter_name, canary)

            if reflection_requests <= self.MAX_REFLECTION_REQUESTS:
                try:
                    r = requests.get(current_target)
                    reflection_requests += 1
                    if canary in r.text:
                        reflects_on.append(values[0])
                except Exception as e:
                    self.mprint("Exception reflection testing: %s" % e)
            else:
                self.mprint("TERMINATED REFLECTION CHECK: TOO MANY REQUESTS.")
                break
        
        return reflects_on


    def classify_param_sources(self, sources):
        """
        Classify parameter sources by the number of parameters that appear in
        their query string. For each class, only one reflection should be 
        checked.
        """
        classes = {}
        for source in sources:
            parts = urlparse(source)
            query = parts.query
            query_hash = ''.join(sorted(list(parse_qs(query).keys())))
            
            if query_hash not in classes:
                classes[query_hash] = [source]
            else:
                classes[query_hash].append(source)
        return classes


    def add_discovered_params(self, url, params):
        """
        Adds newly discovered parameter into the list (if it was not there).
        Returns a number of newly discovered parameters.
        """
        discovered = 0
        for param, values in params.items():
                if param not in self.discovered_params.keys():
                    # Record for given parameter does not exist
                    self.discovered_params[param] = {
                        "sources": [url],
                        "values": values,
                        "reflects": None
                    }
                    discovered += 1
                else:
                    # Source not recorded yet
                    if url not in self.discovered_params[param]["sources"]:
                        self.discovered_params[param]["sources"].append(url)
                    
                    # Update discovered values - Note that this erases any 
                    # assumptions about the order of values.
                    self.discovered_params[param]["values"] += values
                    self.discovered_params[param]["values"] = list(
                        set(self.discovered_params[param]["values"])
                    )
        
        return discovered


    def add_discovered_headers(self, headers):
        """
        Adds header into the discovered headers list if it was not already there.
        """
        discovered = 0
        for header in headers:
            if header not in self.discovered_headers:
                discovered += 1
                self.discovered_headers.append(header)
        return discovered


    def discover_headers(self, response_file):
        """
        Detects headers from response file contents.
        """
        headers = []
        try:
            with open(response_file, 'r') as f:
                for line in f.readlines():
                    parts = line.split(':')
                    if len(parts) >= 2:
                        headers.append(parts[0].lower())
        except IOError:
            self.mprint("[ERROR] Unable to read response file. Rights?")
        return headers


    def filter_common_headers(self, headers):
        """
        Common types of headers (which are of no interest for pentesting) are
        stripped from the discovered headers.
        """
        common_headers = set(['content-type', 'content-length', 
        'content-encoding', 'date', 'expires', 'vary', 'cache-control', 
        'accept-ranges', 'connection', 'etag', 'last-modified'])
        
        filtered = []
        for header in headers:
            if header not in common_headers:
                filtered.append(header)
        
        return filtered


    def obtain_id_url(self, id):
        """
        Looks up results structure returned by SiteCopier module for source 
        URL of a given secret.
        """
        return self.sitecopier_results["parsible"]["anyProcessor"][0]["crawledUrls"][id]


    def provide_results(self, results_structure):
        """
        Allows ParamMiner to access results of other modules. ParamMiner makes
        a copy of results provided by the modules it is dependent on.
        """
        if "SiteCopier" in results_structure.keys():
            self.sitecopier_results = results_structure["SiteCopier"]["results"]


    def get_results(self):
        return {"dummy":"results"}


    def get_dependencies(self):
        return self.dependencies


    def leaves_physical_artifacts(self):
        return False