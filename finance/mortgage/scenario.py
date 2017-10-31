################################################################################
# base.finance.mortgage.scenario
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
from base.finance.mortgage.loan import Installment, Loan
from base.utilities.texttable import Texttable, bcolors, get_color_string
import matplotlib.pyplot as plt
import numpy as np

class Scenario(object):
    def __init__(self, initial_loan, description):
        super(Scenario, self).__init__()
        self.principal = initial_loan.principal
        self.loan = initial_loan
        self.description = description
        self.current_month = 1
        self._installments = [self.loan.monthly_installments[0]]
        self._reset_idx()
        self._marked_months = []

    @property
    def current_total_interest(self):
        return self._installments[-1].total_interest

    @property
    def current_total_capital(self):
        return self._installments[-1].total_capital

    @property
    def current_total_paid(self):
        return self._installments[-1].total_paid

    @property
    def current_debt(self):
        return self._installments[-1].debt

    @property
    def installments(self):
        return self._installments

    def run(self, nr_months):
        for idx, installment in enumerate(self.loan.monthly_installments[self._idx:self._idx+nr_months]):
            dp = Installment(
                    idx = self.current_month + idx,
                    interest = installment.interest,
                    capital = installment.capital,
                    payment = installment.payment,
                    total_interest = installment.interest + self._installments[-1].total_interest,
                    total_capital = installment.capital + self._installments[-1].total_capital,
                    total_paid = installment.payment + self._installments[-1].total_paid,
                    debt = self._installments[-1].debt - installment.capital
                    )
            self._installments.append(dp)
        self._idx += nr_months
        self.current_month += nr_months

    def adjust_loan(self, annual_interest_rate, term_in_months):
        self.loan = Loan(self.current_debt, annual_interest_rate, term_in_months)
        self._reset_idx()
        self._mark_month()

    def payoff(self, amount):
        self._installments[-1] = self._installments[-1]._replace(debt = self.current_debt - amount)
        self._installments[-1] = self._installments[-1]._replace(total_capital = self.current_total_capital + amount)
        self._installments[-1] = self._installments[-1]._replace(total_paid = self.current_total_paid + amount)
        self.loan = Loan(self.current_debt, self.loan.annual_interest_rate, self.loan.nr_months - self._idx)
        self._reset_idx()
        self._mark_month()

    def finish(self):
        self.run(self.loan.nr_months - self._idx + 1)

    def summary(self):
        def format(type, row):
            return [get_color_string(type, cell) for cell in row]
        table = Texttable(max_width = 240)
        header = format(bcolors.BOLD, ['Month', 'Interest', 'Capital', 'Payment', 'Tot. Interest', 'Tot. Capital', 'Tot. Paid', 'Debt'])
        data = [
                    [dp.idx, dp.interest, dp.capital, dp.payment, dp.total_interest, dp.total_capital, dp.total_paid, dp.debt]
                    for dp in self.installments
                ]
        for idx in self._marked_months:
            data[idx] = format(bcolors.BLUE, data[idx])
        rows = [header]
        rows.extend(data)
        table.set_cols_dtype(['i'] * len(rows[0]))
        table.add_rows(rows)
        report = get_color_string(bcolors.BOLD, self.description)
        report += "\n" + table.draw()
        report += "\nTotal interest: {} EUR".format(int(self.current_total_interest))
        report += "\nTotal cost:     {} EUR".format(int(self.current_total_paid))
        return report

    def plot(self):
        fig = plt.figure(facecolor = 'white')
        fig.canvas.set_window_title(self.description)
        self._plot_interest_vs_capital()
        self._plot_total_interest_vs_total_capital()
        self._plot_debt_vs_total_paid()
        self._plot_interest_vs_capital_shares()

    def _plot_interest_vs_capital(self):
        ax = plt.subplot(221)
        width = 0.75
        data_interest = [x for n, x in enumerate(self._data('interest')) if n % 12 == 0]
        ind = np.arange(len(data_interest))
        p1 = ax.bar(ind, data_interest, width, color = self._color_bad, label = "Interest")
        data_capital = [x for n, x in enumerate(self._data('capital')) if n % 12 == 0]
        p2 = ax.bar(ind, data_capital, width, color = self._color_good, bottom = data_interest, label = "Capital")
        ax.legend()
        ax.set_ylabel('EUR')
        ax.set_xlabel('Year')

    def _plot_total_interest_vs_total_capital(self):
        ax = plt.subplot(222)
        data = self._data('total_interest')
        ax.plot(data, label = 'Total Interest', color = self._color_bad)
        ax.annotate("{} EUR".format(int(data[-1])), [0.75*len(data), 1.25*data[-1]])
        data = self._data('total_capital')
        ax.plot(data, label = 'Total Capital', color = self._color_good)
        ax.legend()
        ax.grid(True)
        ax.set_ylabel('EUR')
        ax.set_xlabel('Month')

    def _plot_debt_vs_total_paid(self):
        ax = plt.subplot(223)
        data = self._data('debt')
        ax.plot(data, label = 'Debt', color = self._color_bad)
        data = self._data('total_paid')
        ax.plot(data, label = 'Cost', color = self._color_good)
        ax.legend()
        ax.grid(True)
        ax.set_ylabel('EUR')
        ax.set_xlabel('Month')

    def _plot_interest_vs_capital_shares(self):
        ax = plt.subplot(224)
        labels = ['Interest', 'Capital']
        shares = np.array([self.current_total_interest, self.current_total_capital]) / self.principal
        ax.pie(shares, labels = labels, autopct = '%1.1f%%', shadow = False, colors = (self._color_bad, self._color_good))
        ax.axis('equal') 

    def _reset_idx(self):
        self._idx = 1

    def _mark_month(self):
        self._marked_months.append(self.current_month)

    def _data(self, name):
        return [getattr(installment, name) for installment in self.installments]
    
    @property
    def _color_good(self): return (0.2588, 0.4433, 1.0)

    @property
    def _color_bad(self): return (1.0, 0.5, 0.62)

