import os
import sys
import requests 
import core.utils as utils
import core.config as cfg
from urllib.parse import urlparse
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from time import sleep
from bs4 import BeautifulSoup


class Crawler():
    """
    Responsible for crawling the target application.
    """


    def __init__(self):
        self.URLHelper = URLHelper()
        self.storer = Storer()
        self.current_request_number = 0
        self.requests_done = []
        self.requests_failed = []
        self.requests_filtered_out = []
        self.requests_queue = []


    def set_target(self, target):
        """Sets the crawling target and initializes the request queue."""
        self.target = target
        self.requests_queue = [self.URLHelper.normalize(target)]


    def set_options(self, options={}):
        """
        TODO: Allow setting options for the crawler (probably based on reading 
        the module config).
        - Sleep length customization
        - File size download
        - 
        """
        self.options = options

    
    def mprint(self, string):
        """Crawler logging marker."""
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
            
            # Move finished requests to "requests done"
            self.requests_done.append(self.requests_queue.pop(0))
            self.current_request_number += 1

            # Execution will continue as long as there is a request in the queue
            self.mprint("Number of requests done: %s" % len(self.requests_done))
            self.mprint("Number of requests in the queue: %s" % len(self.requests_queue))
            self.mprint("Number of requests filtered: %s" % len(self.requests_filtered_out))
            self.mprint("Number of requests failed: %s" % len(self.requests_failed))
            sleep(0.2)

        return "Crawling done"


    def issue_request(self, target):
        """
        Issues request against the target and processes response.
        """
        try:

            # Check whether it is worth it to download issue request
            head_response = self._retry_session().head(target)
            should_continue = self.should_request(head_response.headers)

            # If positive, issue the request
            if should_continue:
                response = self._retry_session().get(target)
                self.process_response(target, response)

        except Exception as x:
            print("Request to %s failed after retrying. Adding to failed requests." % target)
            print(x)
            self.requests_failed.append(target)
    
    def should_request(self, headers):
        """
        Based on the HEAD response headers decide whether to send a request or
        not. In the future, parameters to decide this should be configurable.
        
        At the moment: Download binary files smaller than 20 MB.

        TODO: Allow specification of the filesize and filetype that should be
        downloaded. Possibly through self.set_options() member.
        """
        request_size_treshold = 20000000
        content_type = utils.extract_mime_type(headers['Content-Type'])
        
        if utils.is_binary_mime_type(content_type):
            if headers['Content-Length'] > request_size_treshold:
                return False
        
        return True


    def process_response(self, target, response):
        """
        Distributes responsibilities for processing the response.
        """
        # Extract links and add them into the queue
        # - Requires BeautifulSoap
        # - TODO (will need to extend this to understand link contexts)
        self.storer.store(target, response, self.current_request_number)

        # TODO: Refactor this method hard
        # - Needs to use all of the members of link_group (and filter them appropriately)
        # - Write methods to filter specific link groups (e.g. for css/scripts to be downloaded even if outside the scope)

        content_type = utils.extract_mime_type(response.headers['Content-Type'])
        if not utils.is_binary_mime_type(content_type):
            link_group = self.extract_links(content_type, response.text)

            # Remove fragments & None/empty stubs
            a = [
                link for link in link_group['a'] 
                if link != None 
                and not link.startswith('#') 
                and link != ''
            ]

            # - Normalize it, absolutize it and put into the request queue (condition on whether it already is there)
            a = [self.URLHelper.absolutize(self.target, link) for link in a]

            a = [self.URLHelper.remove_fragment(link) for link in a]

            a = [self.URLHelper.normalize(link) for link in a]

            # Remove dupes
            a = list(set(a))

            for link in a:
                if self.URLHelper.is_in_scope(self.target, link):
                    self.add_to_queue(link)
                else:
                    self.add_to_filtered(link)

            #print(a)
        else:
            print("Response was binary.")


    def add_to_queue(self, address):
        """
        Conditional adding to the queue. If the given url is present in either
        of the request queues (planned, failed, filtered, done) it will not be
        added again.
        """
        if (address not in self.requests_done 
            and address not in self.requests_filtered_out 
            and address not in self.requests_failed
            and address not in self.requests_queue):
            self.requests_queue.append(address)


    def add_to_filtered(self, address):
        """
        Adds request to the filtered queue, if it was not there already.
        """
        if address not in self.requests_filtered_out:
            self.mprint("Link %s is external. Filtering out." % address)
            self.requests_filtered_out.append(address)
            


    def extract_links(self, content_type, body):
        """
        Extract links from various elements depending on the content type from
        which the body comes from.

        TODO: Implement link processing for other mime-types.
        """
        if content_type == 'text/html':

            soup = BeautifulSoup(body, 'html.parser')

            # Four main groups: 'a', 'media', 'links' and 'forms'
            
            # A-group
            # Done: a
            # TODO: frame, iframe (watch out: they have other attrs than src)
            a = soup.find_all('a')
            a_urls = [link.get('href') for link in a if link != None]

            # Media-group
            # Done: img
            # TODO: applet, audio, video, track
            img = soup.find_all('img')
            img_urls = [url.get('src') for url in img if url != None]

            # Link-grop
            # Done: link, script
            links = soup.find_all('link')
            link_urls = [url.get('href') for url in links if url != None]
            scripts = soup.find_all('script')
            script_urls = [url.get('src') for url in scripts if url != None]

            return { 'a': a_urls, 'media': img_urls, 'link': link_urls + script_urls }
        elif content_type == 'text/css':
            return {}
        else:
            return {} # just regex it
    
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
    """
    Stores issued requests and responses into directory structure under current
    run and module folders.

    For run initiated on 2019-04-06 00:00:00 with codename ID2S4 that included
    250 requests, 250 directories named 0~249 will be created in directory
    2019-04-06_00_ID2S4. Each of them will contain 3 files named as follows:

        - id.request
        - id.response
        - id.response.headers
    """


    def __init__(self):
        self.output_dir = "output/%s/SiteCopier/" % cfg.CURRENT_RUN_ID

    
    def store(self, target, response, id):
        """
        Stores request headers, response headers and response body into 
        directory corresponding to the request's id.

        Request headers and response headers are stored into file 'as they are'
        because there should be no character set hell.

        When request body is textual, an attempt is made to store it in the 
        encoding provided by the server. If that fails, it is stored as binary
        data and the processing hell is postponed for later.
        """
        save_to = os.path.join(self.output_dir, str(id))
        os.mkdir(save_to)
        req_header_file = os.path.join(save_to, "%s.request" % id)
        response_body_file = os.path.join(save_to, "%s.response" % id)
        response_headers_file = os.path.join(save_to, "%s.response.headers" % id)

        # Save request headers and response headers
        try:
            with open(req_header_file, 'w') as f:
                f.write("URL: %s" % target)
                # FUTURE: Request headers tampering is implemented

            with open(response_headers_file, 'w') as f:
                f.write(str(response.headers))
        except IOError as e:
            print("[ERROR][R:%s] Writing request/response headers failed." % id)
            print(e)

                
        # Do your best to save the response body
        content_type = utils.extract_mime_type(response.headers['Content-Type'])
        if utils.is_binary_mime_type(content_type):
            
            try:
                with open(response_body_file, 'wb') as f:
                    f.write(response.content)
            except IOError as e:
                print("[ERROR][R:%s] Binary response writting error: %s" % (id, e))

        else:
            # Try to save with encoding provided by the server
            charset = utils.extract_charset(response.headers['Content-Type'])
            try: 
                with open(response_body_file, 'w', encoding=charset) as f:
                    f.write(response.text)
            except Exception as e:
                # If that fails, save as binary content
                print("[ERROR][R:%s] Text response writting in server-provided encoding error: %s" % (id, e))
                try:
                    with open(response_body_file, 'wb') as f:
                        f.write(response.content)
                except IOError as e:
                    print("[ERROR][R:%s] Response writting as binary failed too: %s" % (id, e))


class URLHelper():
    """
    Helps with parsing, normalizing and making URLs absolute. Contains utility
    functions usefull for the crawler operations.
    """


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


    def remove_fragment(self, url):
        """Strips the fragment part of the URL."""
        return url.split('#')[0]


    def is_in_scope(self, scope, url):
        """
        Decides whether given URL is within the scope of the target 
        application.

        Subdomain 'www.' is automatically considered to be in-scope.
        """
        url_parts = urlparse(url)
        scope_parts = urlparse(scope)

        if url_parts.netloc == scope_parts.netloc:
            return True
        
        if url_parts.netloc == 'www.' + scope_parts.netloc:
            return True
        
        return False


    def remove_trailing_slash(self, url):
        """
        Strips the trailing slash from the supplied URL. If the URL misses the
        trailing slash, it is returned unmodified.
        """
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