import os, errno
import string
import random
import datetime
import core.config as cfg


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


def prepare_tool_environment():
    """
    Executes necessary preparation actions for the tool run.

    This actions include:
        - Creation of 'output' directory under project root
        - ...
    """
    # Output folder must exist
    try:
        os.makedirs("output")
        print("[I] Output directory did not exist and was created. Is this your first rodeo?")
    except OSError as e:
        if e.errno != errno.EEXIST:
            print("[ERROR] Unable to create 'output' directory. Do you have sufficient rights to write in this location?")
            raise


def prepare_module_folder(module_name):
    """
    Creates module folder for module with given name under /output/ directory.
    """
    try:
        os.makedirs("output/%s/%s" % (cfg.CURRENT_RUN_ID, module_name))
        print("[I] %s module output directory created." % module_name)
    except OSError:
        print("[ERROR] Unable to create output directory for %s module!" % module_name)


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


def is_binary_mime_type(type):
    """
    Based on a very brief white-list decides whether mime type is textual
    or binary.

    TODO: Broaden this after consulting:
     - http://www.iana.org/assignments/media-types/media-types.xhtml
    """
    is_binary = True

    if type.split('/')[0] == 'text':
        is_binary = False

    recognized_textual_types = [
        'text/html', 'text/plain', 'text/css', 'application/json'
        'application/javascript', 'application/jwt', 'application/xml'
    ]

    if type in recognized_textual_types:
        is_binary = False

    return is_binary