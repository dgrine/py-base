################################################################################
# base.utilities.csv
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
from base.utilities.conversion import guess_convert
import cStringIO
import codecs
import collections
import unicodecsv

class UTF8Recoder(object):
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        super(UTF8Recoder, self).__init__()
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeCSVReader(object):
    def __init__(self, f, dialect = unicodecsv.excel, encoding = 'utf-8-sig', **kwds):
        super(UnicodeCSVReader, self).__init__()
        f = UTF8Recoder(f, encoding)
        self.reader = unicodecsv.reader(f, dialect = dialect, **kwds)

    def next(self):
        """
        This function reads and returns the next line as a Unicode string.
        """
        row = self.reader.next()
        return [s if unicode == type(s) else unicode(s, 'utf-8') for s in row]

    def __iter__(self):
        return self

class UnicodeCSVWriter(object):
    def __init__(self, f, dialect = unicodecsv.excel, encoding = 'utf-8-sig', **kwds):
        super(UnicodeCSVWriter, self).__init__()
        self.queue = cStringIO.StringIO()
        self.writer = unicodecsv.writer(self.queue, dialect = dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def write_row(self, row):
        """
        This function takes a Unicode string and encodes it to the output.
        """
        encoded_row = [s.encode('utf-8') if type(s) == str else s for s in row]
        self.writer.writerow(encoded_row)
        data = self.queue.getvalue()
        data = data.decode('utf-8')
        data = self.encoder.encode(data)
        self.stream.write(data)
        self.queue.truncate(0)

    def write_rows(self, rows):
        for row in rows: self.write_row(row)

def read_csv(filename, guess_data_types = True, transform_function = None):
    """
    Returns a list where each element type depends on the given transformation funtion.
    - transform_function is not None:
        The given transformation function must accept a named tuple having 
        the attributes of the CSV file's header and return an object. 
        The type of the named tuple's attributes is either a string,
        or in case the guess_data_types is set to True, a best-guess 
        of the represented data type.
    - transform_function is None:
        Each element is a named tuple 'Record' with attributes of the
        CSV file's header. The type of the named tuple's attributes is
        either a string, or in case the guess_data_types is set to True,
        a best-guess of the represented data type.
    """
    def convert(value):
        if guess_data_types: return guess_convert(value)
        return value
    def transform(record):
        if transform_function: return transform_function(record)
        return record
    records = []
    with open(filename) as f:
        Record = None
        reader = UnicodeCSVReader(f)
        header = None
        for n, row in enumerate(reader):
            if 0 == n:
                header = row
                Record = collections.namedtuple('Record', ' '.join(header))
            else:
                attributes = {header[n]: convert(value) for n, value in enumerate(row)}
                record = transform(Record(**attributes))
                records.append(record)
    return records

