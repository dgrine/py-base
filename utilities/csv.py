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

def read_csv(f, guess_data_types = True, header = None, line_skipper = None, transformer = None):
    """
    Returns a list where each element type depends on the given transformer.
    - transformer is not None:
        The given transformation functor must accept a named tuple having 
        the attributes of the CSV file's header and return an object. 
        The type of the named tuple's attributes is either a string,
        or in case the guess_data_types is set to True, a best-guess 
        of the represented data type.
    - transformer is None:
        Each element is a named tuple 'Record' with attributes of the
        CSV file's header. The type of the named tuple's attributes is
        either a string, or in case the guess_data_types is set to True,
        a best-guess of the represented data type.

    Only lines for which line_skipper returns False are presented
    to the transformer. The line_skipper functor must accept an integer and
    list of strings corresponding to the line number and row respectively.

    Unless a header is provided, the attributes of the named tuple are the 
    columns of the first processed row.
    """
    def convert(value):
        if guess_data_types: return guess_convert(value)
        return value
    def transform(record):
        if transformer: return transformer(record)
        return record
    items = []
    Record = None
    reader = UnicodeCSVReader(f)
    for row_idx, row in enumerate(reader):
        if line_skipper is not None and line_skipper(row_idx, row): continue
        if Record is None:
            if header is None: header = row
            Record = collections.namedtuple('Record', ' '.join(header))
        else:
            if len(row) < len(header): row = row + [None] * (len(header)-len(row))
            elif len(row) > len(header): row = row[0:len(header)]
            attributes = {
                header[n]: convert(value) 
                for n, value in enumerate(row)
            }
            record = Record(**attributes)
            item = transform(record)
            items.append(item)
    return items

def write_csv(filename, rows, header = None):
    with open(filename,'w') as f:
        writer = UnicodeCSVWriter(f)
        if header is None and len(rows) > 0: writer.write_row(rows[0]._fields)
        writer.write_rows(rows)
