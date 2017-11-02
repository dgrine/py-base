################################################################################
# base.finance.data.exchange.gfi
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
from bs4 import BeautifulSoup
import urllib2
import collections

Price = collections.namedtuple('Price', 'denomination purchase sale purchase_premium sale_premium')

class GFI(object):
    def __init__(self):
        self.prices = self._get_prices()

    @property
    def denominations(self):
        return [price.denomination for price in self.prices]

    def price(self, denomination):
        try:
            return next(price for price in self.prices if price.denomination == denomination)
        except StopIteration:
            # Denominations that were historically available, but are no longer offered by GFI
            if "Britannia" == denomination: return self.price("Maple Leaf")
            else:
                raise ValueError("'{}' is not an available denomination".format(denomination))

    def _get_prices(self):
        page = urllib2.urlopen('https://www.goldforex.be//servlet/javaparser_rtbf?pgm=echo_or_uk')
        soup = BeautifulSoup(page, 'html.parser')
        rows = soup.findAll('tr')
        assert len(rows) >= 4, "Unexpected page layout"
        prices = []
        for row in rows[3:]:
            columns = row.findAll('td')
            if len(columns) != 7: break
            data = [column.text for column in columns[1:-1]]
            price = Price(
                    denomination = data[0],
                    purchase = float(data[1]),
                    sale = float(data[2]),
                    purchase_premium = float(data[3]),
                    sale_premium = float(data[4]),)
            prices.append(price)
        return prices


