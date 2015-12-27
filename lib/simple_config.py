import ast
import json
import threading
import os

from copy import deepcopy
from util import user_dir, print_error, print_msg, print_stderr
import chainparams

SYSTEM_CONFIG_PATH = "/etc/encompass.conf"

config = None


def get_config():
    global config
    return config


def set_config(c):
    global config
    config = c


class SimpleConfig(object):
    """
    The SimpleConfig class is responsible for handling operations involving
    configuration files.

    There are 3 different sources of possible configuration values:
        1. Command line options.
        2. User configuration (in the user's config directory)
        3. System configuration (in /etc/)
    They are taken in order (1. overrides config options set in 2., that
    override config set in 3.)
    """
    def __init__(self, options={}, read_system_config_function=None,
                 read_user_config_function=None, read_user_dir_function=None):

        # This lock needs to be acquired for updating and reading the config in
        # a thread-safe way.
        self.lock = threading.RLock()

        # The following two functions are there for dependency injection when
        # testing.
        if read_system_config_function is None:
            read_system_config_function = read_system_config
        if read_user_config_function is None:
            read_user_config_function = read_user_config
        if read_user_dir_function is None:
            self.user_dir = user_dir
        else:
            self.user_dir = read_user_dir_function

        # The command line options
        self.cmdline_options = deepcopy(options)

        # Portable wallets don't use a system config
        if self.cmdline_options.get('portable', False):
            self.system_config = {}
        else:
            self.system_config = read_system_config_function()

        # Set self.path and read the user config
        self.user_config = {}  # for self.get in encompass_path()
        self.path = self.encompass_path()
        self.user_config = read_user_config_function(self.path)
        # Upgrade obsolete keys
        self.fixup_keys({'auto_cycle': 'auto_connect'})

        chaincode = self.get_active_chain_code(default='BTC')
        if self.get_above_chain(chaincode, None) is None:
            self.set_key_above_chain(chaincode, {})
        # Make a singleton instance of 'self'
        set_config(self)

    def encompass_path(self):
        # Read encompass_path from command line / system configuration
        # Otherwise use the user's default data directory.
        path = self.get('encompass_path')
        if path is None:
            path = self.user_dir()

        # Make directory if it does not yet exist.
        if not os.path.exists(path):
            os.mkdir(path)

        print_error("encompass directory", path)
        return path

    def fixup_config_keys(self, config, keypairs):
        updated = False
        for old_key, new_key in keypairs.iteritems():
            if old_key in config:
                if not new_key in config:
                    config[new_key] = config[old_key]
                del config[old_key]
                updated = True
        return updated

    def fixup_keys(self, keypairs):
        '''Migrate old key names to new ones'''
        self.fixup_config_keys(self.cmdline_options, keypairs)
        self.fixup_config_keys(self.system_config, keypairs)
        if self.fixup_config_keys(self.user_config, keypairs):
            self.save_user_config()

    def set_active_chain_code(self, chaincode, save = True):
        if not chainparams.is_known_chain(chaincode):
            return False
        if self.get_above_chain(chaincode, None) is None:
            self.set_key_above_chain(chaincode, {})
        self.set_key_above_chain('active_chain', chaincode, save)
        chainparams.set_active_chain(chaincode)

    def get_active_chain_code(self, default=None):
        return self.get_above_chain('active_chain', default)

    def set_key_above_chain(self, key, value, save = True):
        if not self.is_modifiable(key):
            print_stderr("Warning: not changing config key '%s' set on the command line" % key)
            return

        with self.lock:
            self.user_config[key] = value
            if save:
                self.save_user_config()
        return

    def get_above_chain(self, key, default=None):
        with self.lock:
            out = self.cmdline_options.get(key)
            if out is None:
                out = self.user_config.get(key)
                if out is None:
                    out = self.system_config.get(key, default)
        return out

    def set_key(self, key, value, save = True):
        if not self.is_modifiable(key):
            print_stderr("Warning: not changing config key '%s' set on the command line" % key)
            return
        chaincode = self.get_active_chain_code()
        self.set_key_for_chain(chaincode, key, value, save)

    def get(self, key, default=None):
        chaincode = self.get_active_chain_code()
        with self.lock:
            out = self.cmdline_options.get(key)
            if out is None:
                out = self.user_config.get(chaincode, {}).get(key, default)
        return out

    def set_key_for_chain(self, chaincode, key, value, save = True):
        """Set a key for a specific chain."""
        if not self.is_modifiable(key):
            print_stderr("Warning: not changing config key '%s' set on the command line" % key)
            return
        chain_config = self.get_above_chain(chaincode, {})
        chain_config[key] = value
        self.set_key_above_chain(chaincode, chain_config, save)

    def get_for_chain(self, chaincode, key, default=None):
        chain_config = self.get_above_chain(chaincode, {})
        return chain_config.get(key, default)

    def is_modifiable(self, key):
        return not key in self.cmdline_options

    def save_user_config(self):
        if not self.path:
            return
        path = os.path.join(self.path, "config")
        s = json.dumps(self.user_config, indent=4, sort_keys=True)
        f = open(path, "w")
        f.write(s)
        f.close()
        if self.get('gui') != 'android':
            import stat
            os.chmod(path, stat.S_IREAD | stat.S_IWRITE)

    def get_wallet_path(self):
        """Set the path of the wallet."""

        # command line -w option
        path = self.get('wallet_path')
        if path:
            return path

        # path in config file
        path = self.get('default_wallet_path')
        if path and os.path.exists(path):
            return path

        # default path
        dirpath = os.path.join(self.path, "wallets")
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)

        new_path = os.path.join(self.path, "wallets", "default_wallet")

        # default path in pre 1.9 versions
        old_path = os.path.join(self.path, "encompass.dat")
        if os.path.exists(old_path) and not os.path.exists(new_path):
            os.rename(old_path, new_path)

        return new_path



def read_system_config(path=SYSTEM_CONFIG_PATH):
    """Parse and return the system config settings in /etc/encompass.conf."""
    result = {}
    if os.path.exists(path):
        try:
            import ConfigParser
        except ImportError:
            print "cannot parse encompass.conf. please install ConfigParser"
            return

        p = ConfigParser.ConfigParser()
        try:
            p.read(path)
            for k, v in p.items('client'):
                result[k] = v
        except (ConfigParser.NoSectionError, ConfigParser.MissingSectionHeaderError):
            pass

    return result

def read_user_config(path):
    """Parse and store the user config settings in encompass.conf into user_config[]."""
    if not path:
        return {}
    config_path = os.path.join(path, "config")
    try:
        with open(config_path, "r") as f:
            data = f.read()
    except IOError:
        print_msg("Error: Cannot read config file.", path)
        return {}
    try:
        result = json.loads(data)
    except:
        try:
            result = ast.literal_eval(data)
        except:
            print_msg("Error: Cannot read config file.")
            return {}
    if not type(result) is dict:
        return {}
    return result
