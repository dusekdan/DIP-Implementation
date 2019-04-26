import sys, os, argparse
import requests, json, ftplib
from time import sleep
import signal
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class PastebinTracker():
    """
    This tool is intended for continuous monitoring of the pastebin sidechannel
    over the time during penetration testing session.

    To run this program, first create a keywords.txt file in which you put 
    keywords that you want to monitor for, separated by newline character.

    Then run this program with python3+:

        python PastebinTracker.py -k keywords.txt

    The tool will start monitoring Pastebin.com scraping API for new pastes
    that contain keywords you inputted into the keywords.txt file. When such
    pastes are found, they are stored into the `recorded_pastes` directory
    or the directory you specified in -o/--output-dir parameter.

    WARNING: Setting --fetch-interval parameter value to less than 5 seconds
    is not recommended and will not enhance the tool performace.

    REQUIREMENTS: In order to be able to scrape Pastebin.com API, you need to
    have lifetime pro account on Pastebin.com and whitelist your IP to be 
    allowed to access the API. Without that, the tool will not work.

        |>  This software is a part of the master thesis: 
        |>  "Web Application Penetration Testing Automation"
        |>  Brno, University of Technology, 2019
        |
        |>  Author: Daniel Dušek (@dusekdan - github, gitlab, twitter)
        |>  Contact: dusekdan@gmail.com
        |>  https://danieldusek.com
    """


    def __init__(self, keywords_file, output_dir='recorded_pastes'):
        
        self.keywords = self.load_keywords(keywords_file)
        self.output_dir = output_dir
        self.discovered_pastes = {}
        self.session = requests.session()

        # Pastebin-specific API endpoints
        self.LISTING_ENDPOINT = "https://scrape.pastebin.com/api_scraping.php?limit={LIMIT}"
        self.ITEM_ENDPOINT = "https://scrape.pastebin.com/api_scrape_item.php?i={PASTE_KEY}"
        self.FETCH_TIMEOUT = 10


    def start(self):
        """
        Starts Pastebin.com monitoring.
        """
        self.ensure_environment()
        while True:
            discovered = self.fetch_new_pastes()
            print(" [I] %s new pastes discovered!" % len(discovered))
            print(" |-> %s " % [key for key,value in discovered.items()])

            for key, _ in discovered.items():
                content = self.fetch_paste_contents(key)
                if self.is_interesting(content):
                    self.store_paste(key, content)

            sleep(self.FETCH_TIMEOUT)


    def ensure_environment(self):
        """
        Makes sure that necessary directory structure is in place for results.
        """
        if os.path.exists(os.path.join(".", self.output_dir)):
            print(" [I] Output folder exists. Proceeding...")
        else:
            try:
                target = os.path.join(".", self.output_dir)
                os.makedirs(target)
                print(" [I] Output folder was created in %s." % target)
            except OSError as e:
                print(" [ERROR] Unable to prepare output folder (%s). Can not proceed." % target)
                print(repr(e))
                raise


    def fetch_new_pastes(self):
        """Retrieves new pastes that appear on the scraping endpoint address."""
        new_pastes = {}

        try:
            r = self._retry_session().get(
                self.LISTING_ENDPOINT.replace('{LIMIT}', '20')
            )

            pastes = json.loads(r.text)
            for paste in pastes:
                if paste['key'] not in self.discovered_pastes:
                    self.discovered_pastes[paste['key']] = {}
                    new_pastes[paste['key']] = paste
        except requests.exceptions.RequestException as e:
            print(" [ERROR] RequestException ocurred when fetching new pastes.")
            print(repr(e))
        except ValueError as e:
            print(" [ERROR] Received response with new pastes was not a valid JSON.")
            print(" [ERROR] Do you white-listed your IP address with Pastebin.com first?")
            print(repr(e))

        return new_pastes


    def fetch_paste_contents(self, key):
        """Retrieves contents of the paste with given key."""
        try:
            r = self._retry_session().get(
                self.ITEM_ENDPOINT.replace('{PASTE_KEY}', key)
            )
            paste_content = r.text
        except requests.exceptions.RequestException as e:
            print(" [ERROR] RequestException ocurred when fetching new pastes.")
            print(repr(e))

        return paste_content

    
    def is_interesting(self, paste_content):
        """
        Checks whether some of the keywords that the user is interested in was
        present in the paste's content.
        """
        for keyword in self.keywords:
            if keyword in paste_content:
                return True

        return False

    
    def store_paste(self, paste, content, store=None):
        """
        Backups the paste content.
        - Allows passing of custom store which will take care of saving
        procedures. E.g. exporter to remote REST API could be included.
        """
        if store is not None:
            store.store(paste, content)
        else:
            try:
                target = os.path.join(".", self.output_dir, paste)
                with open(target, 'w', encoding='utf-8', errors='replace') as f:
                    f.write(content)
                print(" [I] Paste %s stored in %s" % (paste, target))
            except IOError:
                print(" [E] Paste %s could not be saved. Do you have sufficient rights?" % paste)


    def load_keywords(self, file):
        """Loads keywords from file."""
        try:
            with open(os.path.join('.', file), 'r') as f:
                keywords = f.readlines()
            self.keywords = [x.strip('\n') for x in keywords]
        except FileNotFoundError as e:
            print(" [ERROR] Keywords file %f not found." % file)
            print(repr(e))
        
        return keywords


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



if __name__ == '__main__':

    def signal_handler(sig, frame):
        """
        Handles program termination via CTRL+C
         |-> Source: https://stackoverflow.com/a/1112350/
        """
        print(" ========================================================================")
        print(" [Q] CTRL+C / ^C press detected. Monitoring stopped.")
        print(" [Q] Pastes captured up to now should be saved in appropriate directory.")
        print(" [Q] Goodbye!")
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--keywords-file', help='Path to file with newline separated keywords to watch.', dest='keywords_file')
    parser.add_argument('--fetch-interval', help='Delay between requests to Pastebin.com\'s API. In seconds.', dest='interval')
    parser.add_argument('-o', '--output-dir', help='Output', dest='output')
    args = parser.parse_args()

    keywords = args.keywords_file
    interval = args.interval
    output = args.output

    if not keywords:
        keywords = "keywords.txt"

    if not output:
        output = "recorded_pastes"
    
    PT = PastebinTracker(keywords, output_dir=output)

    if interval:
        PT.FETCH_TIMEOUT = int(interval)
    
    PT.start()