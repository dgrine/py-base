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
import numpy as np
import collections

Installment = collections.namedtuple('Installment', 'idx interest capital payment debt')

class Loan(object):
    def __init__(self, principal, annual_interest_rate, term_in_years):
        super(Loan, self).__init__()
        self.principal = principal
        self.annual_interest_rate = annual_interest_rate
        self.term = term_in_years
        self.nr_months = self.term * 12

    @property
    def monthly_interest_rate(self):
        return (1. + self.annual_interest_rate)**(1./12) - 1.

    @property
    def monthly_payment(self):
        return self.principal * self.monthly_interest_rate/(1.-(1.+self.monthly_interest_rate)**(-1.*self.nr_months))

    @property
    def monthly_installments(self):
        data = [Installment(idx = 0, interest = 0, capital = 0, payment = 0, debt = self.principal)]

        for month in range(1, self.nr_months + 1):
            capital = (1.+self.monthly_interest_rate)**(month - 1)*(self.monthly_payment - self.monthly_interest_rate*self.principal)
            interest = self.monthly_payment - capital
            payment = capital + interest
            debt = data[-1].debt - capital
            installment = Installment(idx = month, interest = interest, capital = capital, payment = payment, debt = debt)
            data.append(installment)
        return data

    @property
    def yearly_installments(self):
        def chunks(l, n):
            for i in range(0, len(l), n): yield l[i:i + n]

        data = [self.monthly_installments[0]]

        for year, monthly_installments in enumerate(chunks(self.monthly_installments[1:], 12)):
            capital = np.sum([installment.capital for installment in monthly_installments])
            # Alternative way, but less precise if I'm not mistaken
            # interest = self.annual_interest_rate * data[-1].debt
            interest = np.sum([installment.interest for installment in monthly_installments])
            payment = capital + interest
            debt = monthly_installments[-1].debt
            installment = Installment(idx = year + 1, interest = interest, capital = capital, payment = payment, debt = debt)
            data.append(installment)
        return data

    def summary(self, term = 'month'):
        feed_name = '{}ly_installments'.format(term)
        feed = getattr(self, feed_name) 
        for n, installment in enumerate(feed):
            line = "{}: {}, Interest: {}, Capital: {}, Payment: {}, Debt: {}".format(term, installment.idx, installment.interest, installment.capital, installment.payment, installment.debt)
            print(line)

