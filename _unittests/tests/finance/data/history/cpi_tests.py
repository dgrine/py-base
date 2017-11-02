################################################################################
# base._unittests.tests.finance.data.history.cpi_tests
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
from testing import TestCase
from datetime import datetime
import matplotlib.pyplot as plt

def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month

class Test_CPIHistory(TestCase):
    def setUp(self):
        self.history = CPIHistory()

    def test_up_to_date(self):
        cpis = self.history.cpis
        self.assertNotEqual(0, len(cpis))
        expected_nr_months = diff_month(datetime.today(), cpis[0].date) - 1
        self.assertEqual(expected_nr_months, len(cpis))

    def test_fit(self):
        ts_reference = self.history.cpis[len(self.history.cpis)/2].date
        shift = 14
        ts_near = ts_reference.replace(day = ts_reference.day + shift)
        closest_cpi = self.history.cpi(ts_near)
        self.assertEqual(shift, (ts_near - closest_cpi.date).days)

    def test_plot(self):
        self.history.timeseries.plot()
        # plt.show()
