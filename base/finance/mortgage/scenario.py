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
from base.utilities.texttable import Texttable
import matplotlib.pyplot as plt
import numpy as np

class Scenario(object):
    def __init__(self, initial_loan, description):
        super(Scenario, self).__init__()
        self.loan = initial_loan
        self.description = description
        self.current_month = 1
        self._installments = [self.loan.monthly_installments[0]]
        self._reset_idx()
        # self._marked_months = []

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
        # self._mark_moth()

    def payoff(self, amount):
        self._installments[-1] = self._installments[-1]._replace(debt = self.current_debt - amount)
        self._installments[-1] = self._installments[-1]._replace(total_capital = self.current_total_capital + amount)
        self._installments[-1] = self._installments[-1]._replace(total_paid = self.current_total_paid + amount)
        self.loan = Loan(self.current_debt, self.loan.annual_interest_rate, self.loan.nr_months - self._idx)
        self._reset_idx()
        # self._mark_month()

    def finish(self):
        self.run(self.loan.nr_months - self._idx + 1)

    def summary(self):
        table = Texttable(max_width = 240)
        header = ['Month', 'Interest', 'Capital', 'Payment', 'Tot. Interest', 'Tot. Capital', 'Tot. Paid', 'Debt']
        data = [
                    [dp.idx, dp.interest, dp.capital, dp.payment, dp.total_interest, dp.total_capital, dp.total_paid, dp.debt]
                    for dp in self.installments
                ]
        rows = [header]
        rows.extend(data)
        table.set_cols_dtype(['i'] * len(rows[0]))
        table.add_rows(rows)
        return self.description + "\n" + table.draw()

    def plot(self):
        fig = plt.figure(facecolor = 'white')
        fig.canvas.set_window_title(self.description)
        ax = plt.subplot(131)
        width = 0.75
        _interest = [x for n, x in enumerate(self._data('interest')) if n % 12 == 0]
        _capital = [x for n, x in enumerate(self._data('capital')) if n % 12 == 0]
        ind = np.arange(len(_interest))
        p1 = ax.bar(ind, _interest, width, color=(0.2588,0.4433,1.0), label = "Interest")
        p2 = ax.bar(ind, _capital, width, color=(1.0,0.5,0.62), bottom = _interest, label = "Capital")
        ax.legend()
        ax.set_ylabel('EUR')
        ax.set_xlabel('Year')

        ax = plt.subplot(132)
        ax.plot(self._data('total_interest'), label = 'Total Interest')
        ax.plot(self._data('total_capital'), label = 'Total Capital')
        ax.legend()
        ax.set_ylabel('EUR')
        ax.set_xlabel('Month')

        ax = plt.subplot(133)
        ax.plot(self._data('total_paid'), label = 'Cost')
        ax.plot(self._data('debt'), label = 'Debt')
        ax.legend()
        ax.set_ylabel('EUR')
        ax.set_xlabel('Month')

    def _reset_idx(self):
        self._idx = 1

    # def _mark_month(self):
        # self._marked_months.append(self.current_month)

    def _data(self, name):
        return [getattr(installment, name) for installment in self.installments]

