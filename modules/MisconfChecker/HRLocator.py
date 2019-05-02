import os, random
import requests
import core.config as cfg
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from urllib.parse import urlparse

class HiddenResourcesLocator():
    """
        Responsible for enumerating hidden resources on a target application.        

        |>  This software is a part of the master thesis: 
        |>  "Web Application Penetration Testing Automation"
        |>  Brno, University of Technology, 2019
        |
        |>  Author: Daniel Dušek (@dusekdan - github, gitlab, twitter)
        |>  Contact: dusekdan@gmail.com
        |>  https://danieldusek.com
    """


    def __init__(self, target):
        self.target = target
        self.module_name = "MisconfChecker"
        self.parts = urlparse(self.target)
        
        self.resource_list = self.obtain_list_from_payload_file("resources.txt")
        self.vcs_resources_list = self.obtain_list_from_payload_file(
            "resources_vcs.txt"
        )
        
        self.discovered_resources = []
        self.discovered_vcs_resources = []

        self.MAX_REQUESTS = 1000
        self.RANDOMIZE_SELECTION = True

        # Standard apache files are expected to return 403 even when not 
        # present. Ignore these.
        self.blacklist_403 = [
            '.ht_wsr.txt', '.hta', '.htaccess', '.htaccess-dev', '.htaccess-local','.htaccess-marco', '.htaccess.BAK', '.htaccess.bak', '.htaccess.bak1', '.htaccess.inc', '.htaccess.old', '.htaccess.orig', '.htaccess.sample', '.htaccess.save', '.htaccess.txt', '.htaccess/', '.htaccessBAK', '.htaccessOLD', '.htaccessOLD2', '.htaccess_extra', '.htaccess_orig', '.htaccess_sc', '.htaccess~', '.htgroup', '.htpasswd', '.htpasswd-old', '.htpasswd.bak', '.htpasswd.inc', '.htpasswd/', '.htpasswd_test', '.htpasswds', '.htpasswrd', '.htusers', 
        ]
        
        # TODO: Add support for scanning only high-value dirs (vcs, admins, ...)
        # (This is more 'testing-session' dependent and penetration tester 
        # should prepare their own resources list which applies for them)


    def discover_hidden_resources(self):
        """
        Discovers hidden resources of the target applicatoion based on:
        (1) a list of most commonly ocurring files/resources
        (2) commonly used VCS configuration/tracking files and directories
        """
        requests_done = 0
        if self.RANDOMIZE_SELECTION:
            # When selection is randomized, we need a copy of resource list
            # which can be updated.
            resource_list_cp = self.resource_list.copy()
            for _ in range(len(self.resource_list)):
                if requests_done <= self.MAX_REQUESTS:
                    rnd_resource = random.choice(resource_list_cp)
                    
                    self.request_resource(rnd_resource)
                    requests_done += 1
                    
                    resource_list_cp.remove(rnd_resource)
                else:
                    self.mprint("Resource enumeration terminated, MAX REQUESTS (%s) reached." % self.MAX_REQUESTS)
                    break
        else:
            # When no randomization applies, target first N resources.
            for resource in self.resource_list:
                if requests_done <= self.MAX_REQUESTS:
                    self.request_resource(resource)
                    requests_done += 1
                else:
                    self.mprint("Resource enumeration terminated, MAX REQUESTS (%s) reached." % self.MAX_REQUESTS)
                    break
        
        self.locate_vcs_leftovers()
        
        return (self.discovered_resources, self.discovered_vcs_resources)

    
    def request_resource(self, resource):
        """Send request discovering whether hidden resource is available."""
        try:
            url = self.build_url(resource)
            r = self._retry_session().get(url)

            if r.status_code == 403 and resource in self.blacklist_403:
                return
            
            # If target returns anything other than 404, it's there.
            if r.status_code != 404:
                if self.is_vcs_leftover(resource):
                    self.discovered_vcs_resources.append(url)
                else:
                    if r.status_code in range(200,399):
                        self.discovered_resources.append(url)
                    else:
                        self.mprint("Discovered: %s, but the code was %s so this discovery will not be put into the report." % (url, r.status_code))
        except requests.exceptions.RequestException as e:
            self.mprint("[ERROR] Unable to send resource discovery request for %s" % resource)
            self.fprint(repr(e))


    def obtain_list_from_payload_file(self, file_name):
        """Retrieves contents of the file and converts them into the list."""
        path = os.path.join("payloads", file_name)

        try:
            with open(path, 'r') as f:
                resource_list = f.readlines()
            return [x.replace('\n', '') for x in resource_list]
        except FileNotFoundError as e:
            self.mprint("[ERROR] Unable to retrieve file: %s " % path)
            self.fprint(repr(e))
        except IOError as e:
            self.mprint("[ERROR] Unable to retrieve file: %s " % path)
            self.fprint(repr(e))
        return []


    def build_url(self, resource):
        """Sure-fire builds target url."""
        return self.parts.scheme + "://" + self.parts.netloc + "/" + resource


    def is_vcs_leftover(self, name):
        """Returns True when given resource left-over is known be from VCS."""
        if name in self.vcs_resources_list:
            return True
        return False


    def locate_vcs_leftovers(self):
        """
        Verifies whether VCS leftover directories were accidentally pushed into
        production environment.
        """
        for resource in self.vcs_resources_list:
            try:
                url = self.build_url(resource)
                r = self._retry_session().get(url)

                if r.status_code == 403:
                    if url not in self.discovered_vcs_resources:
                        self.discovered_vcs_resources.append(url)
            except requests.exceptions.RequestException as e:
                self.mprint("[ERROR] Unable to send resource discovery request for %s" % resource)
                self.fprint(repr(e))


    def classify_results_by_severity(self, resources):
        """Classifies discovered resources by their severity/impact."""
        pass

    
    def mprint(self, string):
        """Module-specific print wrapper."""
        print(" [%s]: %s" % ("MisconfChecker", string))
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