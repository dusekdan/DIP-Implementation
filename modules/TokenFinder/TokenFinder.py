import os
import math

import core.utils as utils
import core.config as cfg
from core import constants as Consts

class TokenFinder():


    def __init__(self):
        self.dependencies = [
            {
                "depends_on": "SiteCopier",
                "dependency_type": "output",
                "is_essential": True
            }
        ]
        self.module_name = "TokenFinder"
        self.ENTROPY_TRESHOLD = 4.5
        self.MIN_TOKEN_LEN = 20
        self.B64_SET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
        self.secrets = {}
        self.sitecopier_results = {}


    def mprint(self, string):
        """Module-specific print wrapper."""
        print(" [%s]: %s" % (self.module_name, string))


    def execute(self, param):
        self.mprint("===================================%s===================================" % self.module_name)
        self.target = param

        # Acquire artifacts from sitecopier to search
        source = os.path.join("output", cfg.CURRENT_RUN_ID, "SiteCopier")
        for id in range(len(os.listdir(source))):
            response = os.path.join(source, str(id), "%s.response" % id)
            self.find_secrets(response, id)

        self.mprint("Discovered %s secrets." % len(self.secrets))
        self.mprint("===================================%s===================================" % self.module_name)


    def provide_results(self, results_structure):
        """
        Allows TokenFinder to access results of other modules. TokenFinder makes
        a copy of results provided by the modules it is dependent on.
        """
        if "SiteCopier" in results_structure.keys():
            self.sitecopier_results = results_structure["SiteCopier"]["results"]


    def get_results(self):
        """Provides module artifacts back to module launcher to be shared."""
        return {
            "nonparsable": self.secrets,
            "parsable": {}
        }


    def get_dependencies(self):
        """Provides information about the module's dependency requirements."""
        return self.dependencies


    def leaves_physical_artifacts(self):
        """Does the module leave artifacts phisically on filesystem?"""
        return False


    def obtain_response_encoding(self, target_file):
        """
        Looks into the .headers file for suitable encoding to use.
        
        Possible TODO: Test whether this works well for cp1250 encoded sites 
        or whether it will be required to write a translation function 
        windows1250->cp1250 etc.
        """
        target_file = "%s.headers" % target_file
        return utils.get_charset_from_headers_file(target_file)


    def obtain_id_url(self, id):
        """
        Looks up results structure returned by SiteCopier module for source 
        URL of a given secret.
        """
        return self.sitecopier_results["parsable"]["anyProcessor"][0]["crawledUrls"][id]


    def find_secrets(self, target_file, id):
        """
        Searches file for highly entropic strings which are considered
        to be potentially secret/access token.
        """
        file_encoding = self.obtain_response_encoding(target_file)
        try:
            with open(target_file,
            encoding=file_encoding, errors="replace") as f:
                # Go through the file line by line
                line_number = 0
                for line in f.read().split('\n'):
                    line_number += 1
                    # Tokenize each line by white-spaces
                    for token in line.split():
                        # And then tokenize once more into base 64 tokens
                        for b64t in self.extract_b64_tokens(token, self.MIN_TOKEN_LEN):
                            entropy = self.shannon_entropy(b64t)
                            if entropy > self.ENTROPY_TRESHOLD:
                                url = self.obtain_id_url(id)
                                self.store_secret(
                                    token, url, 
                                    line_number, entropy
                                )
        except LookupError:
            self.mprint("[ERROR] Unable to open the file with %s encoding" % file_encoding)


    def store_secret(self, secret_string, url, line_number, entropy):
        """
        Conditionally stores discovered secret into the self.secrets property.
        Based on whether secret string was present or not creates/updates its
        record.
        """
        if secret_string not in self.secrets.keys():
            self.secrets[secret_string] = [{
                "url": url, "line": line_number, "entropy": entropy
            }]
        else:
            # Secret was already discovered for another response. First we
            # verify whether this particular secret was already recorded and if
            # not, then add it.
            add_secret_record = True
            for secret in self.secrets[secret_string]:
                if (secret["url"] == url
                and secret["line"] == line_number):
                    add_secret_record = False
            
            if add_secret_record:
                self.secrets[secret_string].append({
                    "url": url, "line": line_number, "entropy": entropy
                })


    def shannon_entropy(self, data):
        """
        Calculates shannon entropy of a string (result lies in the inclusive
        interval between 1.0 (lowest entropy) and 8.0 (highest entropy)).

        Very slightly modified implementation of the:
         |-> http://blog.dkbza.org/2007/05/scanning-data-for-entropy-anomalies.html
         |-> https://deadhacker.com/2007/05/13/finding-entropy-in-binary-files/
         |-> https://github.com/dxa4481/truffleHog/
        """
        if not data:
            return 0
        entropy = 0
        for x in self.B64_SET:
            p_x = float(data.count(x))/len(data)
            if p_x > 0:
                entropy += - p_x*math.log(p_x, 2)
        return entropy


    def extract_b64_tokens(self, token, max_len):
        """
        Tokenizes string into tokens that are composed of characters permitted
        a valid base64 string.

        Implementation inspired by:
         |-> https://github.com/dxa4481/truffleHog/
        """
        b64_tokens = []
        token_chars = Consts.EMPTY_STRING
        
        for character in token:
            if character in self.B64_SET:
                token_chars += character
            else:
                if len(token_chars) > max_len:
                    b64_tokens.append(token_chars)
                token_chars = Consts.EMPTY_STRING
        
        if len(token_chars) > max_len:
            b64_tokens.append(token_chars)
        
        return b64_tokens