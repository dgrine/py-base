################################################################################
# base._unittests.tests.finance.data.history.gold_tests
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
from base.finance.data.history.gold import GoldHistory
from testing import TestCase 
from datetime import datetime
import matplotlib.pyplot as plt

def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month

class Test_GoldHistory(TestCase):
    def setUp(self):
        self.history = GoldHistory()

    def test_up_to_date(self):
        prices = self.history.prices
        self.assertNotEqual(0, len(prices))
        expected_nr_months = diff_month(datetime.today(), prices[0].date)
        self.assertEqual(expected_nr_months, len(prices))

    def test_price_fit(self):
        ts_reference = self.history.prices[len(self.history.prices)/2].date
        shift = 14
        ts_near = ts_reference.replace(day = ts_reference.day + shift)
        closest_price = self.history.price(ts_near)
        self.assertEqual(shift, (ts_near - closest_price.date).days)

    def test_plot(self):
        self.history.timeseries.plot()
        # plt.show()
