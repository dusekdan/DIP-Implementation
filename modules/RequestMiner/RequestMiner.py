import os
import core.utils as utils
import core.config as cfg

from urllib.parse import urlparse, urljoin, parse_qs

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

        # structure[parameterName] = [baseUrl1, baseUrl2]
        self.discovered_q_pars = {}
        self.discovered_headers = []
    
    
    def mprint(self, string):
        print(" [%s]: %s" % (self.module_name, string))
    

    def execute(self, param):
        self.mprint("===================================%s===================================" % self.module_name)
        self.target = param

        # TODO: Discover Headers + Filter standard (uninteresting) response headers
        self.mprint("Seaching for URL parameters...")
        source = os.path.join("output", cfg.CURRENT_RUN_ID, "SiteCopier")
        for id in range(len(os.listdir(source))):
            url = self.obtain_id_url(id)
            if not self.is_in_scope(self.target, url):
                continue
            response = os.path.join(source, str(id), "%s.response" % id)
            headers = "%s.headers" % response
            
            params = parse_qs(urlparse(url).query, keep_blank_values=True).keys()
            self.mprint(
            "Discovered %s new parameters." % self.add_discovered_params(url, params)
            )

            discovered_headers = self.filter_common_headers(
                self.discover_headers(headers))
            self.mprint(
            "Discovered %s new headers." % self.add_discovered_headers(discovered_headers)
            )

        # TODO: Evaluate security standing for discovered headers (will require
        # keeping values of the headers (not currently doing that... aaah))
        # TODO: Check reflections on URL/Headers
        # TODO: Fuzz discover URL params (probably on the most URL-param-rich sites?)
        # TODO: Fuzz discover Header params

        self.mprint("Terminating...")
        self.mprint("===================================%s===================================" % self.module_name)


    def add_discovered_params(self, url, params):
        """
        Adds param into the discovered params list if it was not already there.
        """
        discovered = 0
        parts = urlparse(url)
        base_url = parts.scheme + "://" + parts.netloc + parts.path
        for param in params:
            # Param already discovered
            if param in self.discovered_q_pars.keys():
                # But origin URL not registered
                if base_url not in self.discovered_q_pars[param]:
                    self.discovered_q_pars[param].append(base_url)
            # Param is new
            else:
                discovered += 1
                self.mprint("%s on %s (%s)" % (param, base_url, url))
                self.discovered_q_pars[param] = [base_url]
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


    def is_in_scope(self, scope, url):
        """
        Decides whether given URL is within the scope of the target 
        application.

        Subdomain 'www.' is automatically considered to be in-scope.

        REFACTOR: Once URLHelper is in utils, use it from there (2/3 copy rule)
        """
        url_parts = urlparse(url)
        scope_parts = urlparse(scope)

        if url_parts.netloc == scope_parts.netloc:
            return True
        
        if url_parts.netloc == 'www.' + scope_parts.netloc:
            return True
        
        return False