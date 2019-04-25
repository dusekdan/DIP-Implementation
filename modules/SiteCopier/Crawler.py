import os
import sys
import random
import requests 
import core.utils as utils
import core.config as cfg
from core.helpers import URLHelper
from core import constants as Consts
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

        self.TOTAL_REQUESTS_LIMITATION = 100


    def set_target(self, target):
        """Sets the crawling target and initializes the request queue."""
        self.target = target
        self.requests_queue = [self.URLHelper.normalize(target)]


    def set_options(self, options={}):
        """
        TODO: Allow setting options for the crawler (probably based on reading 
        the module config).
        - Sleep length customization (currently 0.2)
        - File size download
        - 
        """
        self.options = options

    
    def mprint(self, string):
        """Module-specific print wrapper."""
        print(" [SiteCopier]: %s" % string)


    def crawl(self):
        """
        Crawls the target web application starting from the specified entry point.
        """
        while len(self.requests_queue) != 0:
            # Make a request on the last (first if single) request in the queue
            target = self.requests_queue.pop()
            self.current_target = target
            self.mprint("Requesting: %s" % target)
            
            self.issue_request(target)
            
            # Move finished requests to "requests done"
            self.requests_done.append(target)
            self.current_request_number += 1

            # Shuffle the array to decrease chances of processing the very same
            # kind of a request (randomly smaller looping chance).
            random.shuffle(self.requests_queue)

            # Execution will continue as long as there is a request in the queue
            self.mprint("Number of requests done: %s" % len(self.requests_done))
            self.mprint("Number of requests in the queue: %s" % len(self.requests_queue))
            self.mprint("Number of requests filtered: %s" % len(self.requests_filtered_out))
            self.mprint("Number of requests failed: %s" % len(self.requests_failed))
            sleep(0.2)

            # Prevent infinite looping in e.g. calendar app by hard limiting 
            # total number of requests.
            if self.TOTAL_REQUESTS_LIMITATION == len(self.requests_done):
                self.mprint(
                "TOTAL_REQUESTS_LIMITATION (%s) REACHED" % self.TOTAL_REQUESTS_LIMITATION
                )
                break

        return [{
            "crawledUrls": self.requests_done,
            "failedUrls": self.requests_failed,
            "filteredUrls": self.requests_filtered_out 
            }]


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
            else:
                self.mprint("Determined that I should not continue ")

        except requests.exceptions.RequestException as e:
            self.mprint("[ERROR] Request to %s failed after retrying. Adding to failed requests." % target)
            print(repr(e))
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

        # Experimentally determined positive approach on missing content-type.
        if 'content-type' not in headers:
            return True

        content_type = utils.extract_mime_type(headers['content-type'])

        if utils.is_image_mime_type(content_type):
            return True
        
        if utils.is_binary_mime_type(content_type):
            if 'content-length' not in headers:
                self.mprint("False: content-length not in headers.")
                return False

            if int(headers['content-length']) > request_size_treshold:
                self.mprint("False: CL header exceeded limit: %s" % int(headers['Content-Length']))
                return False
        return True


    def process_response(self, target, response):
        """
        Distributes responsibilities for processing the response.
        """
        self.storer.store(target, response, self.current_request_number)

        # TODO: Add handling for other link_group members.
        # TODO: Add handling of link extraction for other content-types.
        content_type = utils.extract_mime_type(
            response.headers['Content-Type']
        ).lower()

        if not utils.is_binary_mime_type(content_type):
            if content_type == 'text/html':

                link_group = self.extract_links_from_html(response.text)
                self.process_a_links(link_group['a'])
                self.process_a_links(link_group['media'])
                self.process_resource_links(link_group['link'])

            elif content_type == 'text/css':

                self.mprint("No link parsers for CSS files implemented yet.")

            elif (
                content_type == 'application/javascript'
                or content_type == 'application/json'
            ):

                self.mprint("No link parsers for JS/JSON files implemented yet.")

            else:

                self.mprint("Content-Type %s has no parsers.")

        else:

            self.mprint("Response is binary, no links will be extracted.")


    def process_resource_links(self, link_group):
        """
        Proccesses targets of 'link' and 'script' tags and loads them up
        into the queues accordingly. All external and internal links are
        scheduled for request.
        """
        for link in self.apply_basic_link_target_filtering(link_group):
            self.add_to_queue(link)


    def process_a_links(self, link_group):
        """
        Loads desired 'a' link targets up into the request or filtered request
        queue. All external 'a' links are filtered out, fragments are removed
        and local URLs are kept.
        """
        for link in self.apply_basic_link_target_filtering(link_group):
            if self.URLHelper.is_in_scope(self.target, link):
                self.add_to_queue(link)
            else:
                self.add_to_filtered(link)


    def extract_links_from_html(self, body):
        """
        Extracts links from various elements and returns them in given context.
        """
        soup = BeautifulSoup(body, 'html.parser')
        # A-group
        # Done: a, (frame - not tested)
        # TODO: iframe (watch out: they have other attrs than src)
        a = soup.find_all('a')
        a_urls = [link.get('href') for link in a if link != None]
        
        frame = soup.find_all('frame')
        frame_urls = [link.get('src') for link in frame if link != None] + [
            link.get('longdesc') for link in frame if link != None]

        # Media-group
        # Done: img
        # TODO: applet, audio, video, track
        img = soup.find_all('img')
        img_urls = [url.get('src') for url in img if url != None]
        
        # Link-group
        # Done: link, script
        links = soup.find_all('link')
        link_urls = [url.get('href') for url in links if url != None]
        scripts = soup.find_all('script')
        script_urls = [url.get('src') for url in scripts if url != None]

        return { 'a': a_urls + frame_urls, 'media': img_urls, 'link': link_urls + script_urls }


    def extract_links_from_css(self, body):
        """
        TODO: Prepared for implementation at later date.
        """
        pass


    def extract_links_from_js(self, body):
        """
        TODO: Preared for implementation at later date.
        """
        pass


    def apply_basic_link_target_filtering(self, link_group):
        """
        Algorithmically gets rid of undesirable link targets, as follows:
            - (1) Filter out empty, fragments-only and None links
            - (2) Normalize, Absolutize, Defragmentize
            - (3) Order query string parameters alphabetically
            - (4) Remove duplicates
        """
        return list(set([
            self.URLHelper.normalize(
                self.URLHelper.order_query_string_params(
                    self.URLHelper.remove_fragment(
                        self.URLHelper.absolutize(self.target, link)
                ))) for link in link_group 
                    if link != None and not link.startswith('#') and link != ''
        ]))
    
    
    def add_to_queue(self, address):
        """
        Conditional adding to the queue. If the given url is present in either
        of the request queues (planned, failed, filtered, done) it will not be
        added again.
        """
        if (address not in self.requests_done 
            and address not in self.requests_filtered_out 
            and address not in self.requests_failed
            and address not in self.requests_queue
            and address != self.current_target):
            self.requests_queue.append(address)


    def add_to_filtered(self, address):
        """
        Adds request to the filtered queue, if it was not there already.
        """
        if address not in self.requests_filtered_out:
            self.requests_filtered_out.append(address)


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
                f.write(self.format_headers(response.headers))
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
            except LookupError as e:
                # If that fails, save as binary content
                # DBG: print("[ERROR][R:%s] Text response writting in server-provided encoding error: %s" % (id, e))
                try:
                    with open(response_body_file, 'wb') as f:
                        f.write(response.content)
                except IOError as e:
                    print("[ERROR][R:%s] Response writting as binary failed too: %s" % (id, e))


    def format_headers(self, header_dict):
        """
        Translates headers dictionary returned from requests into HTTP-like 
        header file (one header field per line, standard NAME: Value style)
        """
        header_string = Consts.EMPTY_STRING
        for header, value in header_dict.items():
            header_string += "%s: %s\n" % (header, value)
        
        return header_string