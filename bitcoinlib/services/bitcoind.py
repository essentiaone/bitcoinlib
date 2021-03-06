# -*- coding: utf-8 -*-
#
#    BitcoinLib - Python Cryptocurrency Library
#    bitcoind deamon
#    © 2017 June - 1200 Web Development <http://1200wd.com/>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from bitcoinlib.main import *
from bitcoinlib.services.authproxy import AuthServiceProxy
from bitcoinlib.services.baseclient import BaseClient


PROVIDERNAME = 'bitcoind'

_logger = logging.getLogger(__name__)


class ConfigError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
        _logger.warning(msg)

    def __str__(self):
        return self.msg

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class BitcoindClient(BaseClient):

    @staticmethod
    def from_config(configfile=None, network='bitcoin'):
        config = configparser.ConfigParser()
        if not configfile:
            cfn = os.path.join(os.path.expanduser("~"), '.bitcoin/bitcoin.conf')
            if not os.path.isfile(cfn):
                cfn = os.path.join(os.path.expanduser("~"), '.bitcoinlib/config/bitcoin.conf')
            if not os.path.isfile(cfn):
                raise ConfigError("Please install bitcoin client and specify a path to config file if path is not "
                                  "default. Or place a config file in .bitcoinlib/config/bitcoin.conf to reference to "
                                  "an external server.")
        else:
            cfn = os.path.join(DEFAULT_SETTINGSDIR, configfile)
            if not os.path.isfile(cfn):
                raise ConfigError("Config file %s not found" % cfn)
        with open(cfn, 'r') as f:
            config_string = '[rpc]\n' + f.read()
        config.read_string(config_string)
        if config.get('rpc', 'rpcpassword') == 'specify_rpc_password':
            raise ConfigError("Please update config settings in %s" % cfn)
        if network == 'bitcoin':
            port = 8332
        elif network == 'testnet':
            port = 18332
        else:
            raise ConfigError("Network %s not supported by BitcoindClient" % network)
        try:
            server = config.get('rpc', 'server')
        except:
            server = '127.0.0.1'
        url = "http://%s:%s@%s:%s" % (config.get('rpc', 'rpcuser'), config.get('rpc', 'rpcpassword'), server, port)
        return url

    def __init__(self, network='bitcoin', base_url='', denominator=100000000, api_key=''):
        if not base_url:
            base_url = self.from_config('', network)
        if len(base_url.split(':')) != 4:
            raise ConfigError("Bitcoind connection URL must be of format 'http(s)://user:password@host:port,"
                              "current format is %s. Please set url in providers.json file" % base_url)
        if 'password' in base_url:
            raise ConfigError("Invalid password 'password' in bitcoind provider settings. "
                              "Please set password and url in providers.json file")
        _logger.info("Connect to bitcoind on %s" % base_url)
        self.proxy = AuthServiceProxy(base_url)
        super(self.__class__, self).__init__(network, PROVIDERNAME, base_url, denominator, api_key)

    def getrawtransaction(self, txid):
        res = self.proxy.getrawtransaction(txid)
        return res

    def sendrawtransaction(self, rawtx):
        return self.proxy.sendrawtransaction(rawtx)
    
    def estimatefee(self, blocks):
        res = self.proxy.estimatesmartfee(blocks)['feerate']
        return int(res * self.units)


if __name__ == '__main__':
    #
    # SOME EXAMPLES
    #

    from pprint import pprint

    bdc = BitcoindClient()

    print("\n=== SERVERINFO ===")
    pprint(bdc.proxy.getinfo())

    print("\n=== Best Block ===")
    blockhash = bdc.proxy.getbestblockhash()
    bestblock = bdc.proxy.getblock(blockhash)
    bestblock['tx'] = '...' + str(len(bestblock['tx'])) + ' transactions...'
    pprint(bestblock)

    print("\n=== Mempool ===")
    rmp = bdc.proxy.getrawmempool()
    pprint(rmp[:25])
    print('... truncated ...')
    print("Mempool Size %d" % len(rmp))

    print("\n=== Raw Transaction by txid ===")
    t = bdc.getrawtransaction('7eb5332699644b753cd3f5afba9562e67612ea71ef119af1ac46559adb69ea0d')
    pprint(t)

    print("\n=== Current network fees ===")
    t = bdc.estimatefee(5)
    pprint(t)
