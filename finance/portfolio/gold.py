################################################################################
# base.finance.portfolio.gold
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
import collections
import numpy as np
import matplotlib.pyplot as plt
from base.finance.data.exchange.gfi import GFI
from base.finance.data.history.gold import GoldHistory
from base.finance.data.history.inflation import InflationHistory
from base.utilities.texttable import Texttable, bcolors, get_color_string
from base.utilities.csv import read_csv
from datetime import datetime

class Transaction(object):
    def __init__(self, exchange, history, record):
        super(Transaction, self).__init__()
        self.exchange = exchange
        self.history = history
        self.record = record

    @property
    def date(self): return self.record.date

    @property
    def denomination(self): return self.record.denomination

    @property
    def fraction(self): return self.record.fraction

    @property
    def quantity(self): return self.record.quantity

    @property
    def bpu(self): return self.record.bpu

    @property
    def description(self): return self.record.description

    @property
    def date(self): return self.record.date

    # Troy oz
    @property
    def weight(self): return self.record.weight

    @property
    def cost(self): return self.quantity * self.bpu * self.fraction

    @property
    def value(self): return self.quantity * self.fraction * self.exchange.price(self.denomination).purchase
    
    def value_at_date(self, date): return self.quantity * self.fraction * self.history.price(date).value * self.weight

    @property
    def gain(self): return self.value - self.cost

class Portfolio(object):
    def __init__(self, csv_file):
        super(Portfolio, self).__init__()
        self.exchange = GFI()
        self.history = GoldHistory()
        with open('data.csv') as f:
            self.transactions = read_csv(f, transformer = self._create_transaction)

    @property
    def investment(self):
        return int(np.sum([t.cost for t in self.transactions]))

    @property
    def gain(self):
        return int(np.sum([t.gain for t in self.transactions]))

    @property
    def value(self):
        return int(self.investment + self.gain)

    @property
    def nr_coins(self):
        return np.sum([transaction.quantity for transaction in self.transactions])

    @property
    def coins(self):
        return collections.Counter([transaction.denomination for transaction in self.transactions])

    @property
    def distribution(self):
        d = {}
        for transaction in self.transactions:
            if not transaction.denomination in d: d[transaction.denomination] = 0
            d[transaction.denomination] += transaction.value/self.value
        return d

    def summary(self):
        def format_gain(gain):
            if gain < 0: return get_color_string(bcolors.RED, gain)
            return gain

        if 0 == len(self.transactions): return ""
        header = [["Date", "Denomination", "Fraction", "Quantity", "BPU", "Cost", "Value", "Gain"]]
        data = [
            [
                transaction.date.strftime("%Y-%m-%d"), 
                transaction.denomination,
                transaction.fraction,
                transaction.quantity,
                transaction.bpu,
                transaction.cost,
                transaction.value,
                format_gain(transaction.gain)
                ]
            for transaction in self.transactions
        ]
        table = Texttable()
        rows = header + data
        table.set_cols_dtype(['t', 't', 'f', 'i', 'f', 'f', 'f', 's'])
        table.set_precision(2)
        table.add_rows(rows)
        report = table.draw()
        report += "\nCurrent price: {} EUR/oz".format(self.exchange.price("Krugerrand").purchase)
        report += "\nInvestment:   {} EUR".format(self.investment)
        report += "\nGain:         {} EUR".format(self.gain)
        report += "\nValue:        {} EUR".format(self.value)
        return report

    def plot(self):
        self._plot_distribution()
        self._plot_roi()
        self._plot_timeline()
        self.history.timeseries.plot()
        self._plot_on_history()
        self._plot_inflation()

    def _plot_distribution(self):
        fig = plt.figure()
        ax = plt.subplot()
        denominations = self.distribution.keys()
        shares = [pct for pct in self.distribution.values()]
        ax.pie(shares, labels = denominations, autopct = '%1.1f%%', shadow = False)
        ax.axis('equal')
        plt.title('Coin distribution')

    def _plot_roi(self):
        fig = plt.figure()
        ax = plt.subplot(211)
        data = {transaction.date.year: [] for transaction in self.transactions}
        for transaction in self.transactions: data[transaction.date.year].append(transaction)
        years = data.keys()
        investment = [np.sum([t.cost for t in data[year]]) for year in years]
        gain = [np.sum([t.gain for t in data[year]]) for year in years]
        width = 0.75
        ax.bar(years, investment, width, label = 'Investment')
        ax.bar(years, gain, width, label = 'Gain', bottom = investment)
        plt.xlabel('Year')
        plt.ylabel('EUR')
        plt.title('Annual ROI')
        plt.legend()

        ax = plt.subplot(212)
        data = {transaction.date.year: [] for transaction in self.transactions}
        for transaction in self.transactions: data[transaction.date.year].append(transaction)
        years = data.keys()
        investment = np.cumsum([np.sum([t.cost for t in data[year]]) for year in years])
        gain = np.cumsum([np.sum([t.gain for t in data[year]]) for year in years])
        width = 0.75
        ax.bar(years, investment, width, label = 'Investment')
        ax.bar(years, gain, width, label = 'Gain', bottom = investment)
        plt.xlabel('Year')
        plt.ylabel('EUR')
        plt.title('Cumulative ROI')
        plt.legend()

    def _plot_timeline(self):
        fig = plt.figure()
        dates = [t.date for t in self.transactions] + [datetime.today()]
        investment = np.cumsum([t.cost for t in self.transactions] + [0])
        plt.plot(dates, investment, label = 'Investment')
        historic_value = [np.sum([t.value_at_date(date) for t in self.transactions if t.date <= date]) for date in dates]
        plt.plot(dates, historic_value, label = 'Net worth')
        plt.xlabel('Time')
        plt.ylabel('EUR')
        plt.title('Historic investment and worst-case net worth') # worst-case: no premium for coins
        plt.legend()

    def _plot_on_history(self):
        dates = [t.date for t in self.transactions]
        prices = [self.history.price(date) for date in dates]
        current_price = self.history.price(datetime.today()).value
        good_prices = [p for p in prices if p.value < current_price]
        bad_prices = [p for p in prices if p.value >= current_price]
        plt.scatter([p.date for p in good_prices], [p.value for p in good_prices], color = 'green')
        plt.scatter([p.date for p in bad_prices], [p.value for p in bad_prices], color = 'red')

    def _plot_inflation(self):
        inflation_history = InflationHistory()
        inflation_history.timeseries.plot()

    def _create_transaction(self, record):
        return Transaction(self.exchange, self.history, record)
