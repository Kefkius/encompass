from datetime import datetime
import inspect
import requests
import sys
from threading import Thread
import time
import traceback
import csv
from decimal import Decimal
from collections import defaultdict

from encompass.bitcoin import COIN
from encompass.plugins import BasePlugin, hook
from encompass.i18n import _
from encompass.util import PrintError, ThreadJob
from encompass.util import format_satoshis

from exchange_base import *
import coin_exchanges

default_exchanges = {
    'BTC': 'BitcoinAverage',
    'LTC': 'BTCe',
}

def dictinvert(d):
    inv = {}
    for k, vlist in d.iteritems():
        for v in vlist:
            keys = inv.setdefault(v, [])
            keys.append(k)
    return inv

def get_exchanges(module):
    """Returns a dict of {name: class} for exchanges in module."""
    is_exchange = lambda obj: (inspect.isclass(obj)
                               and issubclass(obj, ExchangeBase)
                               and obj != ExchangeBase)
    return dict(inspect.getmembers(sys.modules[module.__name__], is_exchange))

class FxPlugin(BasePlugin, ThreadJob):

    def __init__(self, parent, config, name):
        BasePlugin.__init__(self, parent, config, name)
        self.ccy = self.get_currency()
        self.history_used_spot = False
        self.ccy_combo = None
        self.hist_checkbox = None
        # {chaincode: exchange, ...}
        self.exchange = {}
        self.exchanges = defaultdict(dict)
        
        exchanges = get_exchanges(coin_exchanges)
        for name, obj in exchanges.items():
            for chaincode in obj.chaincodes:
                self.exchanges[chaincode][name] = obj
        for chaincode in self.exchanges.keys():
            self.set_exchange(chaincode, self.config_exchange(chaincode))

    def ccy_amount_str(self, amount, commas):
        prec = CCY_PRECISIONS.get(self.ccy)
        # 8 digit precision for cryptocurrencies.
        prec = 8 if prec is None and self.ccy in self.exchanges.keys() else 2
        fmt_str = "{:%s.%df}" % ("," if commas else "", max(0, prec))
        return fmt_str.format(round(amount, prec))

    def thread_jobs(self):
        return [self]

    def run(self):
        # This runs from the plugins thread which catches exceptions
        if self.timeout <= time.time():
            self.timeout = time.time() + 150
            updated = []
            for exchange in self.exchange.values():
                if exchange.name() in updated:
                    continue
                exchange.update(self.ccy)
                updated.append(exchange.name())

    def get_currency(self):
        '''Use when dynamic fetching is needed'''
        return self.config.get_above_chain("currency", "USD")

    def config_exchange(self, chaincode):
        default = default_exchanges.get(chaincode)
        if not default:
            default = self.exchanges[chaincode].keys()[0]
        return self.config.get_for_chain(chaincode, 'use_exchange', default)

    def show_history(self, chaincode):
        return self.ccy in self.exchange[chaincode].history_ccys()

    def set_currency(self, ccy):
        self.ccy = ccy
        self.config.set_key_above_chain('currency', ccy, True)
        self.get_historical_rates() # Because self.ccy changes
        self.on_quotes()

    def instantiate_exchange(self, class_):
        """Instantiate an exchange or retrieve an existing instance."""
        for exchange in self.exchange.values():
            if isinstance(exchange, class_):
                return exchange
        return class_(self.on_quotes, self.on_history)

    def set_exchange(self, chaincode, name):
        class_ = self.exchanges[chaincode].get(name) or self.exchanges[chaincode].values()[0]
        name = class_.__name__
        self.print_error("using exchange", name, "for", chaincode)
        if self.config_exchange(chaincode) != name:
            self.config.set_key_for_chain(chaincode, 'use_exchange', name, True)

        self.exchange[chaincode] = self.instantiate_exchange(class_)
        # A new exchange means new fx quotes, initially empty.  Force
        # a quote refresh
        self.timeout = 0
        self.get_historical_rates(chaincode)

    def on_quotes(self):
        pass

    def on_history(self):
        pass

    @hook
    def exchange_rate(self, chaincode):
        '''Returns None, or the exchange rate as a Decimal'''
        if not self.exchange.get(chaincode):
            return
        rate = self.exchange[chaincode].quotes.get(chaincode, {}).get(self.ccy)
        if rate:
            return Decimal(rate)

    @hook
    def format_amount_and_units(self, chaincode, coin_balance):
        rate = self.exchange_rate(chaincode)
        return '' if rate is None else "%s %s" % (self.value_str(coin_balance, rate), self.ccy)

    @hook
    def get_fiat_status_text(self, chaincode, coin_balance):
        rate = self.exchange_rate(chaincode)
        return _("  (No FX rate available)") if rate is None else "  1 %s~%s %s" % (chaincode, self.value_str(COIN, rate), self.ccy)

    def get_historical_rates(self, chaincode=None):
        if chaincode:
            chaincodes = [chaincode]
        else:
            chaincodes = self.exchange.keys()

        updated = []
        for code in chaincodes:
            if self.show_history(code):
                exchange = self.exchange[code]
                if exchange.name() in updated:
                    continue
                exchange.get_historical_rates(self.ccy)
                updated.append(exchange.name())

    def requires_settings(self):
        return True

    @hook
    def value_str(self, satoshis, rate):
        if satoshis is None:  # Can happen with incomplete history
            return _("Unknown")
        if rate:
            value = Decimal(satoshis) / COIN * Decimal(rate)
            return "%s" % (self.ccy_amount_str(value, True))
        return _("No data")

    @hook
    def history_rate(self, chaincode, d_t):
        rate = self.exchange[chaincode].historical_rate(self.ccy, d_t)
        # Frequently there is no rate for today, until tomorrow :)
        # Use spot quotes in that case
        if rate is None and (datetime.today().date() - d_t.date()).days <= 2:
            rate = self.exchange[chaincode].quotes.get(chaincode, {}).get(self.ccy)
            self.history_used_spot = True
        return rate

    @hook
    def historical_value_str(self, chaincode, satoshis, d_t):
        rate = self.history_rate(chaincode, d_t)
        return self.value_str(satoshis, rate)
