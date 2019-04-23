import os, errno
import re, string
import cgi
import random
import datetime
import core.config as cfg
from collections import OrderedDict


def generate_run_id():
    """Generates unique and timestamped identifier for the tool's run."""
    now = datetime.datetime.now()
    time_prefix = now.strftime("%Y-%m-%d_%H%M%S")
    return time_prefix + "_" + get_rnd_string(5)


def get_rnd_string(length=10):
    """
    Returns random string composed of uppercase letters of English alphabet
    and numbers.
    Taken from: https://stackoverflow.com/a/2257449
    """
    characters = string.digits + string.ascii_uppercase
    return ''.join(random.choice(characters) for _ in range(length))


def find_between_str(s, start, end):
    """Finds a string between start and end strings."""
    return s.split(start)[1].split(end)[0]


def find_all_between_str(s, start, end):
    """Finds all occurrences of a string between start and end strings."""
    # (.*?) - The question mark makes * non-greedy, which results in properly
    # returned matches (if it was not there, a single match between the very 
    # first separator and the very last separator would be returned.
    matches = re.findall(start + "(.*?)" + end, s)
    return matches


def find_nth(sub, string, n):
    """Finds n-th occurence of substring within the string."""
    if n == 1:
        return string.find(sub)
    return string.find(sub, find_nth(sub, string, n - 1) + 1)


def prepare_tool_environment(run_id):
    """
    Executes necessary preparation actions for the tool run.

    This actions include:
        - Creation of 'output' directory under project root
        - ...
    """
    # Ensure 'output' folder exists.
    try:
        os.makedirs("output")
        print(" [I] 'Output' directory did not exist and was created. Is this your first rodeo?")
        os.makedirs("reports")
        print(" [I] 'Reports' directory did not exist and was created. Is this your first rodeo?")
    except OSError as e:
        if e.errno != errno.EEXIST:
            print(" [ERROR] Unable to create essential directories. Do you have sufficient rights to write in this location?")
            print(e)
            raise

    # Create 'output/run_id' folder.
    try:
        os.makedirs(os.path.join("output", run_id))
        print(" [I] Run directory %s created." % run_id)
    except OSError as e:
        if e.errno != errno.EEXIST:
            print(" [ERROR] Unable to create 'output/%s' directory for current run. Do you have sufficient rights to write in this location?")
            print(e)
            raise


def prepare_module_folder(module_name):
    """
    Creates module folder for module with given name under /output/ directory.
    """
    try:
        os.makedirs("output/%s/%s" % (cfg.CURRENT_RUN_ID, module_name))
        print(" [I] %s module output directory created." % module_name)
    except OSError as e:
        print(" [ERROR] Unable to create output directory for %s module!" % module_name)
        print(e)


def extract_mime_type(content_type_header_value):
    """
    Splits the 'Content-Type' header and extracts the mime-type of 
    the returned content.
    """
    return content_type_header_value.split(';')[0].strip()


def extract_charset(content_type_header_value):
    """
    Extracts charset value from 'Content-Type' header. If charset is not 
    specified, "unknown" string constant is returned.
    """
    charset_part = content_type_header_value.split('charset=')
    if len(charset_part) > 1:
        if charset_part[1][-1] == ';':
            charset_part = charset_part[1][:-1]
        return charset_part[1]
    return "unknown"

def get_charset_from_headers_file(headers_file):
    """
    Retrieves charset value from provided headers file if the charset was 
    specified in 'Content-Type' header. Returns None if it was not.
    """
    try:
        with open(headers_file, 'r', errors="ignore") as f:
            for line in f.readlines():
                if line.lower().startswith('content-type'):
                    charset = extract_charset(line.split(':')[1])
                    if charset != "unknown":
                        return charset
        return None
    except FileNotFoundError as e:
        print(" [ERROR][Utils]: [404] %s" % headers_file)
    except IOError as e:
        print(" [ERROR][Utils] Could not read %s file. Does it exist? Do you have sufficient rights?" % headers_file)
        print(e)

def get_mimetype_from_headers_file(headers_file):
    """
    Retrieves 'content-type' header value from headers file.
    """
    try:
        with open(headers_file, 'r', errors="ignore") as f:
            for line in f.readlines():
                if line.lower().startswith('content-type'):
                    return line.split(':')[1]
        return None
    except FileNotFoundError as e:
        print(" [ERROR][Utils]: [404] %s" % headers_file)
    except IOError as e:
        print(" [ERROR][Utils] Could not read %s file. Does it exist? Do you have sufficient rights?" % headers_file)
        print(e)


def is_binary_mime_type(c_type):
    """
    Based on a very brief white-list decides whether mime type is textual
    or binary.

    TODO: Broaden this after consulting:
     - http://www.iana.org/assignments/media-types/media-types.xhtml
    """
    if c_type.split('/')[0] == 'text':
        return False

    recognized_textual_types = [
        'text/html', 'text/plain', 'text/css', 'application/json',
        'application/javascript', 'application/jwt', 'application/xml',
        'application/rss+xml', 
    ]

    if c_type in recognized_textual_types:
        return False

    return True


def sort_dict_by_key(dictionary, reverse=False):
    """Takes dict and returns OrderedDict sorted by keys."""
    od = OrderedDict()
    for key in sorted(dictionary.keys(), reverse=reverse):
        od[key] = dictionary[key]
    
    return od


def encode_for_html(string):
    """Replaces "dangerous" characters for HTML rendering inside a string."""
    if type(string) is not str:
        string = str(string)
    
    return cgi.escape(string)


def get_rid_of_windows_nl(response):
    pass