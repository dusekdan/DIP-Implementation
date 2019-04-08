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
    # Output folder must exist
    try:
        os.makedirs("output")
        print("[I] Output directory did not exist and was created. Is this your first rodeo?")
    except OSError as e:
        if e.errno != errno.EEXIST:
            print("[ERROR] Unable to create 'output' directory. Do you have sufficient rights to write in this location?")
            raise

def prepare_module_folder(module_name):
    try:
        os.makedirs("output/%s/%s" % (cfg.CURRENT_RUN_ID, module_name))
        print("[I] %s module output directory created." % module_name)
    except OSError:
        print("[ERROR] Unable to create output directory for %s module!" % module_name)