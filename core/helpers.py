import os
import core.utils as utils
from core import constants as Consts
from core import config as cfg
from urllib.parse import urlparse, urljoin, parse_qs, parse_qsl
from requests.models import PreparedRequest
from collections import OrderedDict


class PresentationHelper():
    """
    Contains functionality for generating the report and anything that is 
    relevant to working with template files, report files and generally 
    application output.
    """

    def __init__(self, report_title):

        """Displayed in title-tag/document name"""
        self.report_title = report_title

        """Relative address from root to libs directory (platform independent)"""
        self.path_to_libs = os.path.join("core", "presentation", "libs")
        
        """Templates available for final report."""
        self.template_source = {
            "BWFormal": {
                "main": os.path.join("core", "presentation", "BWFormal", "template.htm"),
                "part": os.path.join("core", "presentation", "BWFormal", "part.report.template.htm")
            }
        }

        """Accumulates output from presenters before it is rendered."""
        self.parts = {}

        pass


    def set_options(self, options):
        """Allows setting of some presenting parameters"""
        self.options = options


    def add_part(self, module, description, content, importance):
        """
        Adds information about report part (outputs from module execution) into
        the internal structure.
        """
        self.parts[module] = {
            "description": description,
            "content": content,
            "importance": importance
        }


    def replace_template_wildcards(self, template, title, parts, target):
        """Replaces template wildards with their respective contents."""
        return template.replace(
            '{REPORT_TITLE}', title
            ).replace(
                '{PARTS}', parts
            ).replace(
                '{REPORT_TARGET}', utils.encode_for_html(target)
            )


    def replace_part_wildcards(self, part, title, description, part_output):
        """Replaces part template wildcards with their respective contents."""

        if "show_module_description" in self.options:
            if not self.options["show_module_description"]:
                description = Consts.EMPTY_STRING

        return part.replace(
            '{PART_TITLE}', title
        ).replace(
            '{PART_DESCRIPTION}', description
        ).replace(
            '{PART_CONTENT}', part_output
        )


    def generate_report(self, style_type, target):
        """
        Generates report in output format as specified by 'style_type' 
        parameter. At the moment HTML only.

        FUTURE: Extend this method to be able to re-generate PDF out of HTML.
        """

        if style_type not in self.template_source:
            # FUTURE: UX+=1, dump everything 'as is' in plaintext
            print(" [ERROR] CAN NOT GENERATE REPORT. TEMPLATE NOT SUPPORTED")
            return

        # Standard processing path for HTML templates, load it, replace it,
        # and render it.
        try:
            template_files = self.template_source[style_type]
            with open(template_files["main"], 'r', encoding='utf-8') as t:
                template = t.read()
            with open(template_files["part"], 'r', encoding='utf-8') as p:
                part = p.read()
            
            parts = {}
            for module_name, part_record in self.parts.items():

                current_part = part
                part_output = self.replace_part_wildcards(
                        current_part, module_name,
                        part_record["description"], 
                        part_record["content"]
                )

                if part_record["importance"] in parts:
                    parts[part_record["importance"]].append(
                        part_output
                    )
                else:
                    parts[part_record["importance"]] = [part_output]

            # Go through the parts output and craft value for {PARTS}, ordered
            # by importance as reported by the module.
            parts_render = Consts.EMPTY_STRING
            for _, to_render in utils.sort_dict_by_key(
                parts, reverse=True).items():
                for render_part in to_render:
                    parts_render += render_part
            
            final_report = self.replace_template_wildcards(template, 
            self.report_title, parts_render, target)

            report_path = os.path.join("reports", cfg.CURRENT_RUN_ID + ".htm")
            with open(report_path, 'w', errors="ignore") as f:
                f.write(final_report)

            print(" [ALL-DONE] Review the report file in: %s " % report_path)

        except FileNotFoundError as e:
            print(" [ERROR] Template %s improperly structured." % style_type)
            print(e)
        except IOError as e:
            print(" [ERROR] Unable to read template %s file." % style_type)
            print(e)
            


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
        # FUTURE: skip this at the moment, because this is not how URL should be written
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


    def replace_parameter_value(self, url, parameter_name, value):
        """
        Replaces value of the parameter in query string with desired value.
        """
        parts = urlparse(url)
        query_dict = dict(parse_qsl(parts.query))
        query_dict[parameter_name] = value
        req = PreparedRequest()
        req.prepare_url(
            parts.scheme + "://" + parts.netloc + parts.path, query_dict
        )
        return req.url


    def order_query_string_params(self, url):
        """
        Orders query string parameters alphabetically. E.g. for:
        |-> Translates https://domain.test/?z=1&b=2&a=3&d=4&e=4
        |-> To         https://domain.test/?a=3&b=2&d=4&e=4&z=1

        When multiple parameters of the same name have different values, these
        will also be sorted (in an ascending order).
        """
        parts = urlparse(url)
        params = parse_qs(parts.query)
        params_ordered = OrderedDict()

        for key in sorted(list(params.keys())):
            params_ordered[key] = sorted(params[key])
        
        r = PreparedRequest()
        r.prepare_url(
            parts.scheme + "://" + parts.netloc + parts.path, params_ordered
        )
        return r.url


    def add_query_string_param(self, url, param, value):
        """Adds provided parameter and values to the url as query string."""
        req = PreparedRequest()
        req.prepare_url(url, {param: value})
        return req.url


    def remove_query_string_param(self, url, param):
        """Removes query string parameter by name."""
        parts = urlparse(url)
        params = parse_qs(parts.query)
        
        if param in params:
            params.pop(param)
        
        req = PreparedRequest()
        req.prepare_url(
            parts.scheme + "://" + parts.netloc + parts.path, params
        )
        return req.url


    def update_query_string_param(self, url, param, value):
        """Updates query string parameter by name."""
        parts = urlparse(url)
        params = parse_qs(parts.query)

        if param in params:
            params[param] = value
        
        req = PreparedRequest()
        req.prepare_url(
            parts.scheme + "://" + parts.netloc + parts.path, params
        )
        return req.url