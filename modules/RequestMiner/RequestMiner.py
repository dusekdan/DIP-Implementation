import os
import random
import requests
import core.utils as utils
import core.config as cfg
from core.helpers import URLHelper
from requests.models import PreparedRequest
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from . import Presenter as p

from urllib.parse import urlparse, urljoin, parse_qs, parse_qsl
from time import sleep


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

        self.DELAY = 0.1
        self.CANARY_LENGTH = 8
        self.MAX_REFLECTION_REQUESTS = 10

        self.URLPARAM_DISCOVERY_HEURISTICS = "START_PAGE"
        self.MAX_ACCEPTED_URL_LENGTH = 2000 # Sourced: https://stackoverflow.com/a/417184/

        # struct[param] = {
        #   "sources": ['url1', 'url2', 'url3'],
        #   "values": ['value1', 'value2', 'value3'],
        #   "reflects": True|False|None
        #   "reflects_on": ['url1', 'url2']
        # }
        self.discovered_params = {}
        self.discovered_headers = []
        self.hidden_params = {
            "discovered": [],
            "reflected": [],
            "source_url": ""
        }

        self.url_discovery_parameters = []
    
    
    def mprint(self, string):
        """Module-specific print wrapper."""
        print(" [%s]: %s" % (self.module_name, string))
    

    def execute(self, param):
        self.mprint("===================================%s===================================" % self.module_name)
        self.target = param

        # Existing parameters & headers discovery
        source = os.path.join("output", cfg.CURRENT_RUN_ID, "SiteCopier")
        for id in range(len(os.listdir(source))):
            url = self.obtain_id_url(id)
            if not self.URLHelper.is_in_scope(self.target, url):
                continue
            response = os.path.join(source, str(id), "%s.response" % id)
            headers = "%s.headers" % response

            # Existing Parameter Discovery
            params = parse_qs(urlparse(url).query, keep_blank_values=True)
            self.add_discovered_params(url, params)

            # Existing Header Discovery
            discovered_headers = self.filter_common_headers(
            self.discover_headers(headers))
            self.add_discovered_headers(discovered_headers)

        self.mprint("%s parameters & %s headers detected." % (
            len(self.discovered_params), len(self.discovered_headers)
        ))


        # Find hidden URL parameters
        pd_target = self.urlparam_startpage_heuristics()
        self.hidden_params["source_url"] = pd_target
        self.mprint(
            "Initializing parameter mining: %s" % pd_target
        )
        discovered_ps, reflected_ps = self.discover_hidden_url_parameters(pd_target)
        self.hidden_params["discovered"] = discovered_ps
        self.hidden_params["reflected"] = reflected_ps
        self.mprint("Discovered params: %s | Reflecting params: %s" % (len(discovered_ps), len(reflected_ps)))


        # FUTURE: Find hidden Headers

        # Detect existing url parameter reflections.
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
        # keeping values of the headers (not currently doing that... aaah) - or
        # maybe calling securityheaders.com instead?)
        # Maybe this functionality will fit better under SSL eval module?
        
        self.mprint("Request mining completed....")
        self.mprint("===================================%s===================================" % self.module_name)


    def discover_hidden_url_parameters(self, target):
        """
        Rains down the furious requeststorm upon thy target to figure out what
        parameters it had enshrouded.
        """
        discovery_urls, canaries = self.prepare_param_discovery_urls(target)
        discovered_params = []
        reflected_params = []
        
        # Preliminary analysis of target response to certain requests.
        ok_response = {}
        non_existing_q_param = utils.get_rnd_string(15)
        non_existing_q_param_value = utils.get_rnd_string(10)
        param_not_exists_response = {}
        try:
            std_r = self._retry_session().get(target)
            ok_response["code"] = std_r.status_code
            ok_response["text"] = std_r.text
            ok_response["headers"] = std_r.headers

            pne_r = self._retry_session().get(
                self.URLHelper.add_query_string_param(
                    target, non_existing_q_param, non_existing_q_param_value
                ))
            param_not_exists_response["code"] = pne_r.status_code
            param_not_exists_response["text"] = pne_r.text
            param_not_exists_response["headers"] = pne_r.headers

            # Randomly generated query string param was discovered in the response,
            # there is a strong chance that every string param is reflected.
            if (non_existing_q_param in param_not_exists_response["text"] 
                or non_existing_q_param_value in param_not_exists_response["text"]):
                discovered_params.append(non_existing_q_param)
                reflected_params.append(non_existing_q_param)
        
        except requests.exceptions.RequestException as e:
            self.mprint("[ERROR][Preflight] Mining request failed (%s). Mining ops terminated." % e)
            return []

        hidden_parameters = self.mine_hidden_parameters(discovery_urls, 
            canaries, ok_response, param_not_exists_response
        )

        discovered_params += hidden_parameters["discovered"]
        reflected_params += hidden_parameters["reflected"]
        
        return (discovered_params, reflected_params)


    def mine_hidden_parameters(self, urls, canaries, ref_ok, ref_pne):
        """
        Sends requests to prepared discovery URLs and returns lists of 
        discovered parameters & list of reflective parameters.

        FUTURE: Calculate the difference between .text responses and use it as an indicator.
        """
        reflected_params = []
        discovered_params = []
        run_through = 0
        for url in urls:
            try:
                r = self._retry_session().get(url)
                # Indicators of whether parameter has any effect
                # [code, headers, text], forEach x, x € [0, 0.5, 1]
                indicators = [
                self.rate_indicators(
                    r.status_code, 
                    ref_ok["code"], 
                    ref_pne["code"]
                ),
                self.rate_indicators(
                    len(r.headers), 
                    len(ref_ok["headers"]), 
                    len(ref_pne["headers"])
                ),
                self.rate_indicators(
                    len(r.text), len(ref_ok["text"]), len(ref_pne["text"]))
                ]

                # Look for canaries & responsible parameters
                if sum(indicators) > 0:
                    self.mprint("Found something... will try to pinpoint the parameter.")
                    effective_params = self.identify_parameter(url, ref_ok, ref_pne)
                    if effective_params:
                        self.mprint("Determined: %s" % effective_params)
                        discovered_params += effective_params

                    for name, value in canaries.items():
                        if value in r.text:
                            reflected_params.append(name)

                sleep(self.DELAY)

            except requests.exceptions.RequestException as e:
                self.mprint("[ERROR][Discovery] Mining request failed (%s). Mining ops terminated." % e)
                break
            
            # If first run-through discovers too many reflected parameters, all
            # of the parameters are likely reflected.
            if run_through == 0 and len(discovered_params) > 25:
                self.mprint("Detecting too many reflections. Probably everything is reflected.")
                break
            run_through += 1

        return {"reflected": reflected_params, "discovered": discovered_params}


    def identify_parameter(self, url, ok, notok):
        """
        Identifies parameters in URL that are responsible for detected changes
        in the way target application replies. Request heavy and calls it off
        when more than half of the batch of parameters influence responses.
        """
        added_params = list(
            set(
                list(parse_qs(urlparse(url).query).keys())
            ) & set(self.url_discovery_parameters)
        )
        effective_params = []

        for _ in range(len(added_params)):
            to_append = random.choice(added_params)
            appended = self.URLHelper.add_query_string_param(
                self.urlparam_startpage_heuristics(), 
                to_append, utils.get_rnd_string()
            )
            try:
                r = self._retry_session().get(appended)
                
                ci = self.rate_indicators(
                    r.status_code, ok["code"], notok["code"]
                )
                hi = self.rate_indicators(
                    len(r.headers), len(ok["headers"]), len(notok["headers"])
                )
                ti = self.rate_indicators(
                    len(r.text), len(ok["text"]), len(notok["text"])
                )

                if sum([ci, hi, ti]) > 0:
                    effective_params.append(to_append)
                
                sleep(self.DELAY)
            
            except requests.exceptions.RequestException as e:
                self.mprint("[ERROR][Pinpointing] Mining request failed (%s). Mining ops terminated." % e)
                return None

        return effective_params


    def identify_parameter_OBSOLETE(self, url, ok, notok):
        """
        Identifies which of the parameters in URL is responsible for detected
        change in the way target application replied. Kinda request heavy.
        FUTURE: Figure how to do this efficiently with interval splitting.
        FUTURE: Make it work / Use strip_tags()-like logic to compare plaintext.
        """
        # Intersection of params in URL and params from our parameter list.
        added_params = list(
            set(
                list(parse_qs(urlparse(url).query).keys())
            ) & set(self.url_discovery_parameters)
        )
        to_remove = random.choice(added_params)

        for _ in range(len(added_params)):
            removed = self.URLHelper.remove_query_string_param(url, to_remove)
            try:
                r = self._retry_session().get(removed)

                ci = self.rate_indicators(
                    r.status_code, ok["code"], notok["code"]
                )
                hi = self.rate_indicators(
                    len(r.headers), len(ok["headers"]), len(notok["headers"])
                )
                ti = self.rate_indicators(
                    len(r.text), len(ok["text"]), len(notok["text"])
                )

                # This means that the parameter to_remove made the change
                # If it's >0, then the remaining parameters made the change
                if sum([ci, hi, ti]) == 0:
                    return to_remove
                elif sum([ci, hi, ti]) > 0:
                    url = removed

                added_params.remove(to_remove)
                if len(added_params) != 0:
                    to_remove = random.choice(added_params)

                sleep(self.DELAY)

            except requests.exceptions.RequestException as e:
                self.mprint("[ERROR] Mining request failed (%s). Mining ops terminated." % e)
                return None


    def rate_indicators(self, current, ok, pne):
        """
        Returns likelyhood with which current request contained parameter that
        affected target's response.
        """
        if pne == ok:
            if ok == current:
                return 0
            else:
                return 1
        else:
            if current == pne:
                return 0
            elif current == ok:
                return 1
            else:
                return 0.5


    def prepare_param_discovery_urls(self, base_url):
        """
        For given URL generates bunch of parameter discovery URLs with 
        canaries and returns this information back.
        """
        PARAM_SEP_LEN = 2 ; CANARY_LEN = self.CANARY_LENGTH
        url_len = len(base_url)
        
        discovery_urls = []
        param_dict = {}
        canary_dict = {}

        try:
            with open('payloads/parameters.txt', 'r') as f:
                param_list = f.read().splitlines()
                self.url_discovery_parameters = param_list
        except IOError as e:
            self.mprint("[ERROR] Unable to open payloads/parameters.txt.")
            self.mprint(e)
            return
        
        for param in param_list:
            if (url_len + len(param) + PARAM_SEP_LEN + CANARY_LEN) < self.MAX_ACCEPTED_URL_LENGTH:
                # URL Character limit not exceeded yet.
                canary = utils.get_rnd_string(CANARY_LEN)
                param_dict[param] = canary
                canary_dict[param] = canary
                url_len += (PARAM_SEP_LEN + len(param) + CANARY_LEN)
            else:
                # Add to URLs, start preparing a new one. 
                r = PreparedRequest()
                r.prepare_url(base_url, param_dict)
                discovery_urls.append(r.url)
                param_dict = {}
                url_len = len(base_url)
        
        # Leftovers after depleting all parameters from paramlist.
        if len(param_dict) != 0:
            r = PreparedRequest()
            r.prepare_url(base_url, param_dict)
            discovery_urls.append(r.url)

        return (discovery_urls, canary_dict)


    def urlparam_startpage_heuristics(self):
        """
        Select which URL will be used as a base URL against which the query 
        parameters discovery will be executed.
        FUTURE: Selection heuristics can be influenced by the set_options
        Available heuristics:
        - (A) Base URL (main page)
        - (B) Page with the highest amount of query parameters (NotImplemented)
        """
        if self.URLPARAM_DISCOVERY_HEURISTICS == "START_PAGE":
            return self.target
        else:
            return self.target


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

        for _, values in url_classes.items():
            # Pick exactly 1 candidate from each group
            current_target = self.URLHelper.replace_parameter_value(values[0],
                parameter_name, canary)

            if reflection_requests <= self.MAX_REFLECTION_REQUESTS:
                try:
                    r = requests.get(current_target)
                    reflection_requests += 1
                    if canary in r.text:
                        reflects_on.append(values[0])
                except requests.exceptions.RequestException as e:
                    self.mprint("[ERROR] Mining request failed (%s)." % e)
            else:
                self.mprint("REFLECTION CHECK TERMINATED: TOO MANY REQUESTS.")
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
        except FileNotFoundError as e:
            self.mprint("[WARNING][404] Skipping %s" % response_file)
        except IOError as e:
            self.mprint("[ERROR] Unable to read response file. Rights?")
            self.mprint("File: %s" % response_file)
            self.mprint(e)
        
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
        return self.sitecopier_results["parsable"]["anyProcessor"][0]["crawledUrls"][id]


    def provide_results(self, results_structure):
        """
        Allows RequestMiner to access results of other modules. RequestMiner 
        makes a copy of results provided by the modules it is dependent on.
        """
        if "SiteCopier" in results_structure.keys():
            self.sitecopier_results = results_structure["SiteCopier"]["results"]


    def get_results(self):
        """Provides module artifacts back to module launcher to be shared."""
        return {
            "nonparsable": {
                "existing_params": self.discovered_params,
                "existing_headers": self.discovered_headers,
            },
            "parsable": {
                "existing_params": self.discovered_params,
                "existing_headers": self.discovered_headers,
                "hidden_params": self.hidden_params,
            }
        }


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