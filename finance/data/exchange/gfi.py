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


