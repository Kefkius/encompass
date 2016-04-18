from datetime import datetime
from decimal import Decimal

from encompass.i18n import _

from exchange_base import *

class Bittrex(ExchangeBase):
    chaincodes = ('BLK', 'BTC', 'CLAM', 'DASH', 'DOGE', 'FTC', 'GRS', 'LTC', 'MAZA', 'PPC', 'START', 'VIA')
    def get_rates(self, ccy):
        result = {}
        for code in self.chaincodes:
            # Special cases.
            real_code = code
            if code == 'BTC':
                continue
            elif code == 'MAZA':
                code = 'MZC'
            json = self.get_json('bittrex.com', '/api/v1.1/public/getticker?market=BTC-%s' % code)
            result[real_code] = {'BTC': Decimal(json['result']['Last'])}
        return result

class Poloniex(ExchangeBase):
    chaincodes = ('BLK', 'BTC', 'CLAM', 'DASH', 'DOGE', 'GRS', 'LTC', 'NMC', 'PPC', 'VIA')
    def get_rates(self, ccy):
        result = {}
        json = self.get_json('poloniex.com', '/public?command=returnTicker')
        for code in self.chaincodes:
            rates = {}
            if json.get('BTC_%s' % code):
                rates['BTC'] = Decimal(json['BTC_%s' % code]['last'])
            if json.get('USDT_%s' % code):
                rates['USD'] = Decimal(json['USDT_%s' % code]['last'])
            if json.get('XMR_%s' % code):
                rates['XMR'] = Decimal(json['XMR_%s' % code]['last'])

            result[code] = rates
        return result

class YoBit(ExchangeBase):
    chaincodes = ('BTC', 'CLAM', 'DASH', 'DOGE', 'LTC', 'NMC', 'PPC', 'START', 'VIA')
    def get_rates(self, ccy):
        result = {}
        for code in self.chaincodes:
            s = '%s_btc' % code.lower()
            json = self.get_json('yobit.net', '/api/3/ticker/%s' % s)
            if not json.get(s):
                continue
            result[code] = {'BTC': Decimal(json[s]['last'])}
        return result

class BitcoinAverage(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        json = self.get_json('api.bitcoinaverage.com', '/ticker/global/all')
        return dict([(r, Decimal(json[r]['last']))
                     for r in json if r != 'timestamp'])

    def history_ccys(self):
        return ['AUD', 'BRL', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'IDR', 'ILS',
                'MXN', 'NOK', 'NZD', 'PLN', 'RON', 'RUB', 'SEK', 'SGD', 'USD',
                'ZAR']

    def historical_rates(self, ccy):
        history = self.get_csv('api.bitcoinaverage.com',
                               "/history/%s/per_day_all_time_history.csv" % ccy)
        return dict([(h['datetime'][:10], h['average'])
                     for h in history])

class BitcoinVenezuela(ExchangeBase):
    chaincodes = ('BTC', 'LTC')
    def get_rates(self, ccy):
        json = self.get_json('api.bitcoinvenezuela.com', '/')
        result = {}
        for chaincode in self.chaincodes:
            rates = [(r, json[chaincode][r]) for r in json[chaincode]
                     if json[chaincode][r] is not None]
            result[chaincode] = dict(rates)
        return result

    def protocol(self):
        return "http"

    def history_ccys(self):
        return ['ARS', 'EUR', 'USD', 'VEF']

    def historical_rates(self, ccy):
        return self.get_json('api.bitcoinvenezuela.com',
                             "/historical/index.php?coin=BTC")[ccy +'_BTC']

class BTCParalelo(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        json = self.get_json('btcparalelo.com', '/api/price')
        return {'VEF': Decimal(json['price'])}

    def protocol(self):
        return "http"

class Bitso(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        json = self.get_json('api.bitso.com', '/v2/ticker')
        return {'MXN': Decimal(json['last'])}

    def protocol(self):
        return "http"

class Bitcurex(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        json = self.get_json('pln.bitcurex.com', '/data/ticker.json')
        pln_price = json['last']
        return {'PLN': Decimal(pln_price)}

class Bitmarket(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        json = self.get_json('www.bitmarket.pl', '/json/BTCPLN/ticker.json')
        return {'PLN': Decimal(json['last'])}

class BitPay(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        json = self.get_json('bitpay.com', '/api/rates')
        return dict([(r['code'], Decimal(r['rate'])) for r in json])

class BitStamp(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        json = self.get_json('www.bitstamp.net', '/api/ticker/')
        return {'USD': Decimal(json['last'])}

class BlockchainInfo(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        json = self.get_json('blockchain.info', '/ticker')
        return dict([(r, Decimal(json[r]['15m'])) for r in json])

    def name(self):
        return "Blockchain"

class BTCChina(ExchangeBase):
    chaincodes = ('BTC', 'LTC')
    def get_rates(self, ccy):
        result = {}
        for chaincode in self.chaincodes:
            json = self.get_json('data.btcchina.com', '/data/ticker?market=%scny' % chaincode)
            result[chaincode] = {'CNY': Decimal(json['ticker']['last'])}
        return result

class CaVirtEx(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        json = self.get_json('www.cavirtex.com', '/api/CAD/ticker.json')
        return {'CAD': Decimal(json['last'])}

class Coinbase(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        json = self.get_json('coinbase.com',
                             '/api/v1/currencies/exchange_rates')
        return dict([(r[7:].upper(), Decimal(json[r]))
                     for r in json if r.startswith('btc_to_')])

class CoinDesk(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        dicts = self.get_json('api.coindesk.com',
                              '/v1/bpi/supported-currencies.json')
        json = self.get_json('api.coindesk.com',
                             '/v1/bpi/currentprice/%s.json' % ccy)
        ccys = [d['currency'] for d in dicts]
        result = dict.fromkeys(ccys)
        result[ccy] = Decimal(json['bpi'][ccy]['rate_float'])
        return result

    def history_starts(self):
        return { 'USD': '2012-11-30' }

    def history_ccys(self):
        return self.history_starts().keys()

    def historical_rates(self, ccy):
        start = self.history_starts()[ccy]
        end = datetime.today().strftime('%Y-%m-%d')
        # Note ?currency and ?index don't work as documented.  Sigh.
        query = ('/v1/bpi/historical/close.json?start=%s&end=%s'
                 % (start, end))
        json = self.get_json('api.coindesk.com', query)
        return json['bpi']

class Coinsecure(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        json = self.get_json('api.coinsecure.in', '/v0/noauth/newticker')
        return {'INR': Decimal(json['lastprice'] / 100.0 )}

class Unocoin(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        json = self.get_json('www.unocoin.com', 'trade?buy')
        return {'INR': Decimal(json)}

class itBit(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        ccys = ['USD', 'EUR', 'SGD']
        json = self.get_json('api.itbit.com', '/v1/markets/XBT%s/ticker' % ccy)
        result = dict.fromkeys(ccys)
        if ccy in ccys:
            result[ccy] = Decimal(json['lastPrice'])
        return result

class Kraken(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        ccys = ['EUR', 'USD', 'CAD', 'GBP', 'JPY']
        pairs = ['XBT%s' % c for c in ccys]
        json = self.get_json('api.kraken.com',
                             '/0/public/Ticker?pair=%s' % ','.join(pairs))
        return dict((k[-3:], Decimal(float(v['c'][0])))
                     for k, v in json['result'].items())

class LocalBitcoins(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        json = self.get_json('localbitcoins.com',
                             '/bitcoinaverage/ticker-all-currencies/')
        return dict([(r, Decimal(json[r]['rates']['last'])) for r in json])

class Winkdex(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self, ccy):
        json = self.get_json('winkdex.com', '/api/v0/price')
        return {'USD': Decimal(json['price'] / 100.0)}

    def history_ccys(self):
        return ['USD']

    def historical_rates(self, ccy):
        json = self.get_json('winkdex.com',
                             "/api/v0/series?start_time=1342915200")
        history = json['series'][0]['results']
        return dict([(h['timestamp'][:10], h['price'] / 100.0)
                     for h in history])

class MercadoBitcoin(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self,ccy):
        json = self.get_json('mercadobitcoin.net',
                                "/api/ticker/ticker_bitcoin")
        return {'BRL': Decimal(json['ticker']['last'])}
    
    def history_ccys(self):
        return ['BRL']

class Bitcointoyou(ExchangeBase):
    @single_chain('BTC')
    def get_rates(self,ccy):
        json = self.get_json('bitcointoyou.com',
                                "/API/ticker.aspx")
        return {'BRL': Decimal(json['ticker']['last'])}

    def history_ccys(self):
        return ['BRL']
