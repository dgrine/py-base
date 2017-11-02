################################################################################
# base.finance.timeseries
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
from base.py.modules import this_module_path_relative
from base.utilities.misc import nearest_elements
from base.utilities.csv import read_csv, write_csv
import matplotlib.pyplot as plt
from datetime import datetime
import math
import os

class Timeseries(object):
    def __init__(self, series_name, description = None, unit = None, data = None):
        super(Timeseries, self).__init__()
        self._filename = '{}.csv'.format(series_name)
        self.description = description
        self.unit = unit
        self._data = self._get_data() if data is None else data
        assert 0 != len(self.data), "No data available"

    @property
    def start_date(self): return self.data[0].date

    @property
    def end_date(self): return self.data[-1].date

    @property
    def data(self): return self._data

    def value(self, date):
        def nearest_date(p1, p2): return math.fabs((p1.date - p2.date).days)
        p = type(self.data[0])(date = date, value = 0)
        return nearest_elements([p], self.data, distance = nearest_date)[0]

    @property
    def cached_file(self): return this_module_path_relative('data', self._filename)

    def plot(self):
        fig = plt.figure()
        dates = [p.date for p in self.data]
        values = [p.value for p in self.data]
        plt.plot(dates, values)
        plt.xlabel('Time')
        if self.unit is not None: plt.ylabel(self.unit)
        if self.description is not None: plt.title(self.description)

    def _get_data(self):
        data = self._get_data_offline()
        if 0 == len(data):
            data = self._get_data_online()
            assert 0 != len(data), "No data received"
            write_csv(self.cached_file, data)
            return data
        else:
            last_offline_date = data[-1].date
            today = datetime.today()
            if last_offline_date.year == today.year and last_offline_date.month != today.month:
                data = self._get_data_online()
                write_csv(self.cached_file, data)
        return data

    def _get_data_offline(self):
        if not os.path.exists(self.cached_file): return []
        with open(self.cached_file, 'r') as f: return read_csv(f)

    def _get_data_online(self): raise NotImplementedError()
