################################################################################
# base.utilities.misc
# Author: Djamel Grine.
#
# Copyright 2017. Djamel Grine.
#
# Redistribution and use in source and binary forms, with or without 
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, 
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, 
#    this list of conditions and the following disclaimer in the documentation 
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.
################################################################################
from collections import defaultdict
import datetime
import dateutil.parser
import json
import os
import random
import re
import string

class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime.datetime):
                return obj.isoformat() #strftime('%Y-%m-%dT%H:%M:%SZ')
            iterable = iter(obj)

        except TypeError:
            pass
        else:
            return list(iterable)

        return json.JSONEncoder.default(self, obj)

def disable_http_logging():
    import logging
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests.packages.urllib3').setLevel(logging.WARNING)

def generate_key(size = 6, chars = string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def get_filename_extension(filename):
    full_extension = os.path.splitext(filename)[1] # This includes the '.'
    if not '.' in full_extension: return full_extension
    return full_extension[1:]

def current_timestamp(format_string = None):
    if None != format_string:
        assert type(format_string) in (str, unicode), "Expected string type"
        return datetime.datetime.utcnow().strftime(format_string)
    return datetime.datetime.utcnow()

def parse_timestamp(ts_string):
    return dateutil.parser.parse(ts_string)

def parse_bool(bool_string):
    value_lowercase = bool_string.lower()
    if 'true' == value_lowercase:
        return True
    return False

_read_version_from_file_regex = re.compile(r'[a-zA-Z-_]+=([0-9]+)')
def read_version_from_file(file):
    """
    Reads a 'version' file.
    A version file is a file where each line has the format key=value, 
    where key is a string and value an integer. The resulting version
    is obtained by joining the values in the declared order with a dot
    separation. For example:
    
    major=2
    minor=7
    revision=1
    
    Becomes '2.7.1'.
    """
    # Sanity check
    assert os.path.isfile(file), "'%s' is not a file" % file

    with open(file, 'r') as f:
        return ".".join([_read_version_from_file_regex.match(line).groups()[0] for line in f.readlines()])

def remove_duplicates(seq):
    """
    Removes duplicates from a sequence while preserving ordering.
    """
    seen = set()
    seen_add = seen.add # Optimization relying on faster resolution of look-up
                        # of local variable than method of object 'seen'
    return [x for x in seq if not (x in seen or seen_add(x))]

def recursively_default_dict():
    return defaultdict(recursively_default_dict)

_first_cap_re = re.compile('(.)([A-Z][a-z]+)')
_all_cap_re = re.compile('([a-z0-9])([A-Z])')
def convertCamelcaseToUnderscore(name):
    """
    Converts a camelCase string to under_score string.
    """
    s1 = _first_cap_re.sub(r'\1_\2', name)
    return _all_cap_re.sub(r'\1_\2', s1).lower()

def convertUnderscoreToCamelcase(name):
    parts = name.split('_')
    if 0 == len(parts): return name

    parts_new = [parts[0]]
    for part in parts[1:]:
        parts_new.append(part.capitalize())
    return type(name)().join(parts_new)

def round_number(number, nof_decimals = 2):
    number_type = type(number)
    assert number_type in (int, long, float), "Expected numeric type"
    assert int == type(nof_decimals), "Expected int type"
    return float(str(round(number, nof_decimals)))

