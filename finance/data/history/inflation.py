################################################################################
# base.finance.data.history.inflation
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
from base.finance.data.history.cpi import CPIHistory
from base.finance.timeseries import Timeseries

class InflationHistory(object):
    def __init__(self):
        super(InflationHistory, self).__init__()
        self.timeseries = self._compute_timeseries()

    @property
    def inflation_numbers(self): return self.timeseries.data

    def inflation(self, date): return self.timeseries.value(date)

    def _compute_timeseries(self):
        """
        Inflation is here calculated as the year-on-year percentage change of the CPI.
        """
        history = CPIHistory()
        cpi_start_date = history.timeseries.start_date
        start_date = cpi_start_date.replace(year = cpi_start_date.year + 1)
        Record = type(history.cpis[0])
        cpis = [cpi for cpi in history.cpis if cpi.date >= start_date]
        data = [Record(date = cpi.date, value = (1. - history.cpi(cpi.date.replace(year = cpi.date.year - 1)).value / cpi.value)) for cpi in cpis]
        return Timeseries(series_name = 'inflation', description = 'Inflation', data = data)

