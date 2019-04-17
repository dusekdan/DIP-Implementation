from urllib.parse import urlparse, urljoin, parse_qs, parse_qsl
from requests.models import PreparedRequest
from collections import OrderedDict

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