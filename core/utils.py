import string
import random
import datetime

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