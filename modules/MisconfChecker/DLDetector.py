import requests
import os
import core.config as cfg
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from core.helpers import URLHelper

from time import sleep

from urllib.parse import urlparse, urljoin, parse_qs, parse_qsl

class DLDetector():
    """
        Responsible for detecting enabled directory listing on a target.

        |>  This software is a part of the master thesis: 
        |>  "Web Application Penetration Testing Automation"
        |>  Brno, University of Technology, 2019
        |
        |>  Author: Daniel Dušek (@dusekdan - github, gitlab, twitter)
        |>  Contact: dusekdan@gmail.com
        |>  https://danieldusek.com
    """

    def __init__(self, urls, target):
        self.urls = urls
        self.module_name = "MisconfChecker"
        self.target = target
        self.URLHelper = URLHelper()
        self.directory_listings = []
        
        self.DELAY = 0.1

    def detect_directory_listing(self):
        """
        Discovers subdirectories on given target based on what has been
        observed in the crawling phase (SiteCopier)
        """
        self.virtual_dirs = []
        for url in self.urls:
            # Detect virtual directories (and update the list of them)
            if self.URLHelper.is_in_scope(self.target, url):
                self.update_virtual_dirs(
                    self.detect_virtual_directories(url)
                )

        parts = urlparse(self.target)
        for directory_address in self.virtual_dirs:
            url = parts.scheme + '://' + parts.netloc + '/' + directory_address
            
            self.fprint("Checking: %s" % url)
            try:
                r = self._retry_session().get(url)
                sleep(self.DELAY)
            except requests.exceptions.RequestException as e:
                self.mprint("[ERROR] Request to %s failed." % url)
                self.fprint(repr(e))
            
            if self.is_dl_reply(r.text):
                self.directory_listings.append(
                    url
                )      

        return self.directory_listings


    def is_dl_reply(self, response):
        """
        Inspects response for directory listing indicators and determines
        whether DL is enabled.
        """
        title_indicator = heading_indicator = above_indicator = False
        
        if '<title>Index of' in response:
            title_indicator = True

        if '<h1>Index of' in response:
            heading_indicator = True

        # First two conditions are standard.
        # Later two conditions were discovered in startupgarden.fi's directory
        # listing response-
        if '<a href="../">../</a>' in response or \
            "<a href='../'>../</a>" in response or \
            '<a href="/">Parent Directory</a>' in response or\
            "<a href='/'>Parent Directory</a>" in response:
            above_indicator = True
        
        return title_indicator and heading_indicator and above_indicator


    def detect_virtual_directories(self, url):
        """Detects what virtual directories are present in the URL"""
        parts = urlparse(url)
        path = parts.path
        components = path.split('/')
        components.remove('')
        
        if not components:
            return components

        # Do not consider file to be a directory.
        if '.' in components[-1]:
            components.pop()

        return self.build_virtual_directory_components(components)


    def build_virtual_directory_components(self, components):
        """Recursively builds all possible directory paths."""
        if not components:
            return components
        ccomp = components.copy()
        results = ['/'.join(ccomp)]
        ccomp.pop()
        results += self.build_virtual_directory_components(ccomp)
        return results


    def update_virtual_dirs(self, new_directories):
        """
        Merges current values of the virtual_dir property with newly retrieved
        virtual directory values.
        """
        self.virtual_dirs += new_directories
        self.virtual_dirs = list(set(self.virtual_dirs))


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