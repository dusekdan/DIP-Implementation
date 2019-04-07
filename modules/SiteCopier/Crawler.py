import os
import sys
import requests 

from urllib.parse import urlparse
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class Crawler():


    def __init__(self):
        self.URLHelper = URLHelper()
        self.storer = Storer()
        self.current_request_number = 0


    def set_target(self, target):
        self.target = target
        self.requests_queue = [self.URLHelper.normalize(target)]
        self.requests_done = []
        self.requests_failed = []
        self.requests_filtered_out = []


    def set_options(self, options={}):
        self.options = options

    
    def mprint(self, string):
        print(" [SiteCopier][CRAWLER]: %s" % string)


    def crawl(self):
        """
        Crawls the target web application starting from the specified entry point.
        """
        while len(self.requests_queue) != 0:
            # Make a request on the first request in the queue
            target = self.requests_queue[0]
            self.mprint("Requesting: %s" % target)
            
            self.issue_request(target)

           # Extract the links and add them into the queue
            # -> Condition this by adding only normalized links that ARE NOT IN DONE QUE
            
            # Move finished requests to "requests done"
            self.requests_done = self.requests_queue.pop(0)
            self.current_request_number += 1

            # Execution will continue as long as there is a request in the queue

        return "Crawling done"


    def issue_request(self, target):
        """
        Issues request against the target and processes response.
        """
        try:
            req = self._retry_session().get(target)
            self.process_response(req)
        except Exception:
            print("Request to %s failed after retrying. Adding to failed requests." % target)
            self.requests_failed.append(target)


    def process_response(self, request):
        """
        Distributes responsibilities for processing the response.
        """
        # Extract links and add them into the queue
        # - Requires BeautifulSoap
        # - Normalize it, absolutize it and put into the request queue (condition on whether it already is there)
        # - For contexts TODO (will need to extend this to understand contexts)
        self.storer.store(request, self.current_request_number)

    
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

class Storer():

    def __init__(self):
        self.output_dir = "output/%s" % sys.CURRENT_RUN_ID
        self.text_content_types = [
            "text/plain", "text/html"
        ]
        self.binary_content_types = [
            "application/octets"
        ]

    
    def store(self, request, id):
        # Store request headers, response headers and response body and 
        # based on the response content-type take action.
        save_to = os.path.join(self.output_dir, str(id))
        os.mkdir(save_to)

        req_header_file = os.path.join(save_to, "%s.request" % id)
        response_body_file = os.path.join(save_to, "%s.response" % id)
        response_headers_file = os.path.join(save_to, "%s.response.headers" % id)

        with open(req_header_file, 'w') as f:
            f.write("Some header content")
        
        with open(response_body_file, 'w') as f:
            f.write(request.text)

        with open(response_headers_file, 'w') as f:
            f.write(str(request.headers))



class URLHelper():


    def __init__(self):
        pass


    def normalize(self, url):
        """
        Puts provided URL into standardized form. Helps avoiding duplicates.

        Additional information on possibilities of normalization:
         |-> https://en.wikipedia.org/wiki/URL_normalization
        """
        normalized_url = url
                
        # Remove the trailing slash
        # TODO: Potential issue when target does not return for the slashed
        # version the same content as for the not slashed version. Potential
        # solution would be to send both requests and calculate the difference
        # between them (not only 200 == 200, but also from content perspective)
        if normalized_url[-1] == '/':
            normalized_url = normalized_url[0:-1]
        
        # Convert scheme and host part into lowercase
        url_parts = urlparse(normalized_url)
        url_parts = url_parts._replace(
            scheme=url_parts.scheme.lower(),
            netloc=url_parts.netloc.lower()
        )

        return url_parts.geturl()


    def normalize_for(self, source, url):
        """Normalizes URL for specific source address"""
        # If the URL is not absolute, make it be.
        normalized_url = url
        if not self.is_absolute(url):
            normalized_url = self.absolutize(source, url)
        
        return self.normalize(normalized_url)



    def absolutize(self, source, url):
        """
        Turns a relative address into an absolute one. If provided url is 
        absolute already, does nothing.
        """
        if self.is_absolute(url):
            return url
        
        url_parts = urlparse(source)

        # Cases to catch:
        # www.domain.com / domain.com (missing protocol)
        # -> Check if left-hand prefix of netloc is the same, if yes, 
        # append protocol
        # TODO: Future (skip this at the moment, because this is not how 
        # URL should be written)
        #if url_parts.netloc.startswith(self.remove_trailing_slash(url)):

        # /relative/address (relative address from the root)
        if url[0] == '/':
            return url_parts.scheme + "://" + url_parts.netloc + url
        
        # ./relative/address || ../relative2/address
        return urljoin(source, url)


    def remove_trailing_slash(self, url):
        if url[-1] == '/':
            return url[0:-1]
        return url


    def is_absolute(self, url):
        """
        Checks whether given URL is absolute.
        
        Source:
         |-> https://stackoverflow.com/a/8357518
        """
        return bool(urlparse(url).netloc)