################################################################################
# base.finance.mortgage.loan
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
from base.utilities.texttable import Texttable
import numpy as np
import collections

Installment = collections.namedtuple('Installment', 'idx interest capital payment total_interest total_capital total_paid debt')

class Loan(object):

    def __init__(self, principal, annual_interest_rate, term_in_months):
        super(Loan, self).__init__()
        self.principal = principal
        self.annual_interest_rate = annual_interest_rate
        self.nr_months = term_in_months

    @property
    def total_cost(self):
        return self.principal + self.total_interest

    @property
    def total_interest(self):
        return self.yearly_installments[-1].total_interest

    @property
    def monthly_interest_rate(self):
        return (1. + self.annual_interest_rate)**(1./12) - 1.

    @property
    def monthly_payment(self):
        return self.principal * self.monthly_interest_rate/(1.-(1.+self.monthly_interest_rate)**(-1.*self.nr_months))

    @property
    def monthly_installments(self):
        if not hasattr(self, '_monthly_installments'):
            self._monthly_installments = self._compute_monthly_installments()
        return self._monthly_installments

    @property
    def yearly_installments(self):
        if not hasattr(self, '_yearly_installments'):
            self._yearly_installments = self._compute_yearly_installments()
        return self._yearly_installments

    def summary(self, term = 'month'):
        table = Texttable()
        rows = [[term.capitalize(), 'Interest', 'Capital', 'Payment', 'Total Interest', 'Total Capital', 'Total Paid', 'Debt']]
        installments = getattr(self, '{}ly_installments'.format(term))
        rows.extend([[dp.idx, dp.interest, dp.capital, dp.payment, dp.total_interest, dp.total_capital, dp.debt] for dp in installments])
        table.add_rows(rows)
        return table.draw()

    def _compute_monthly_installments(self):
        data = [Installment(idx = 0, interest = 0, capital = 0, payment = 0, total_interest = 0, total_capital = 0, total_paid = 0, debt = self.principal)]
        for month in range(1, self.nr_months + 1):
            capital = (1.+self.monthly_interest_rate)**(month - 1)*(self.monthly_payment - self.monthly_interest_rate*self.principal)
            interest = self.monthly_payment - capital
            payment = capital + interest
            total_interest = data[-1].total_interest + interest
            total_capital = data[-1].total_capital + capital
            total_paid = data[-1].total_paid + payment
            debt = data[-1].debt - capital
            installment = Installment(
                    idx = month, 
                    interest = interest,
                    capital = capital,
                    payment = payment, 
                    total_interest = total_interest, 
                    total_paid = total_paid,
                    total_capital = total_capital, 
                    debt = debt)
            data.append(installment)
        return data

    def _compute_yearly_installments(self):
        def chunks(l, n):
            for i in range(0, len(l), n): yield l[i:i + n]
        data = [self.monthly_installments[0]]
        for year, monthly_installments in enumerate(chunks(self.monthly_installments[1:], 12)):
            capital = np.sum([installment.capital for installment in monthly_installments])
            # Alternative way, but less precise if I'm not mistaken
            # interest = self.annual_interest_rate * data[-1].debt
            interest = np.sum([installment.interest for installment in monthly_installments])
            payment = capital + interest
            total_interest = data[-1].total_interest + interest
            total_capital = data[-1].total_capital + capital
            total_paid = data[-1].total_paid + payment
            debt = monthly_installments[-1].debt
            installment = Installment(
                    idx = year + 1, 
                    interest = interest, 
                    capital = capital, 
                    total_interest = total_interest, 
                    total_paid = total_paid,
                    total_capital = total_capital, 
                    payment = payment, 
                    debt = debt)
            data.append(installment)
        return data

