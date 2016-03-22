#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2015 Thomas Voegtlin
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import ast
import os
import sys
import time

import jsonrpclib
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer, SimpleJSONRPCRequestHandler

from network import Network, NetworkController
from util import json_decode, DaemonThread
from util import print_msg, print_error, print_stderr
from wallet import WalletStorage, Wallet
from commands import known_commands, Commands
from simple_config import SimpleConfig


def get_lockfile(config):
    return os.path.join(config.path, 'daemon')

def remove_lockfile(lockfile):
    os.unlink(lockfile)

def get_fd_or_server(config):
    '''Tries to create the lockfile, using O_EXCL to
    prevent races.  If it succeeds it returns the FD.
    Otherwise try and connect to the server specified in the lockfile.
    If this succeeds, the server is returned.  Otherwise remove the
    lockfile and try again.'''
    lockfile = get_lockfile(config)
    while True:
        try:
            return os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY), None
        except OSError:
            pass
        server = get_server(config)
        if server is not None:
            return None, server
        # Couldn't connect; remove lockfile and try again.
        remove_lockfile(lockfile)

def get_server(config):
    lockfile = get_lockfile(config)
    while True:
        create_time = None
        try:
            with open(lockfile) as f:
                (host, port), create_time = ast.literal_eval(f.read())
                server = jsonrpclib.Server('http://%s:%d' % (host, port))
            # Test daemon is running
            server.ping()
            return server
        except:
            pass
        if not create_time or create_time < time.time() - 1.0:
            return None
        # Sleep a bit and try again; it might have just been started
        time.sleep(1.0)



class RequestHandler(SimpleJSONRPCRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Headers",
                         "Origin, X-Requested-With, Content-Type, Accept")
        self.send_header("Access-Control-Allow-Origin", "*")
        SimpleJSONRPCRequestHandler.end_headers(self)


class Daemon(DaemonThread):

    def __init__(self, config, fd):

        DaemonThread.__init__(self)
        self.config = config
        if config.get('offline'):
            self.network_controller = None
        else:
            self.network_controller = NetworkController(config)
        self.gui = None
        self.wallets = {}
        # Setup server
        cmd_runner = Commands(self.config, None, self.network_controller)
        host = config.get_above_chain('rpchost', 'localhost')
        port = config.get_above_chain('rpcport', 0)
        server = SimpleJSONRPCServer((host, port), logRequests=False,
                                     requestHandler=RequestHandler)
        os.write(fd, repr((server.socket.getsockname(), time.time())))
        os.close(fd)
        server.timeout = 0.1
        for cmdname in known_commands:
            server.register_function(getattr(cmd_runner, cmdname), cmdname)
        server.register_function(self.run_cmdline, 'run_cmdline')
        server.register_function(self.ping, 'ping')
        server.register_function(self.run_daemon, 'daemon')
        server.register_function(self.run_gui, 'gui')
        self.server = server

    def ping(self):
        return True

    def run_daemon(self, config):
        sub = config.get('subcommand')
        assert sub in ['start', 'stop', 'status']
        if sub == 'start':
            response = "Daemon already running"
        elif sub == 'status':
            if self.network_controller:
                def fill_network_info(chaincode):
                    d = {}
                    network = self.network_controller.get_network(chaincode)
                    params = network.get_parameters()
                    d['server'] = params[0]
                    d['blockchain_height'] = network.get_local_height()
                    d['server_height'] = network.get_server_height()
                    d['nodes'] = network.get_interfaces()
                    d['connected'] = network.is_connected()
                    d['auto_connect'] = params[4]
                    return d

                # Get info on each network
                network_keys = self.network_controller.get_network_keys()
                chains = {}
                for i in network_keys:
                    chain_info = fill_network_info(i)
                    chains[i] = chain_info
                response = {
                    'path': self.network_controller.config.path,
                    'networks': chains,
                }
            else:
                response = "Daemon offline"
        elif sub == 'stop':
            self.stop()
            response = "Daemon stopped"
        return response

    def run_gui(self, config_options):
        config = SimpleConfig(config_options)
        if self.gui:
            if hasattr(self.gui, 'new_window'):
                path = config.get_wallet_path()
                self.gui.new_window(path, config.get('url'))
                response = "ok"
            else:
                response = "error: current GUI does not support multiple windows"
        else:
            response = "Error: Electrum is running in daemon mode. Please stop the daemon first."
        return response

    def load_wallet(self, path, get_wizard=None, active_chain=None):
        wallet = None
        # Return existing wallet if it has the same chain.
        existing_wallet = self.wallets.get(path)
        if existing_wallet:
            if not active_chain or active_chain == existing_wallet.storage.active_chain:
                wallet = existing_wallet

        if not wallet:
            storage = WalletStorage(path, active_chain)
            network = self.network_controller.get_network(storage.active_chain.code)
            if get_wizard:
                if storage.file_exists:
                    wallet = Wallet(storage)
                    action = wallet.get_action()
                else:
                    action = 'new'
                if action:
                    wizard = get_wizard()
                    wallet = wizard.run(network, storage)
                else:
                    wallet.start_threads(network)
            else:
                wallet = Wallet(storage)
                wallet.start_threads(network)
            if wallet:
                self.wallets[path] = wallet
        return wallet

    def run_cmdline(self, config_options):
        config = SimpleConfig(config_options)
        cmdname = config.get('cmd')
        cmd = known_commands[cmdname]
        path = config.get_wallet_path()
        wallet = self.load_wallet(path) if cmd.requires_wallet else None
        # arguments passed to function
        args = map(lambda x: config.get(x), cmd.params)
        # decode json arguments
        args = map(json_decode, args)
        # options
        args += map(lambda x: config.get(x), cmd.options)
        cmd_runner = Commands(config, wallet, self.network_controller,
                              password=config_options.get('password'),
                              new_password=config_options.get('new_password'))
        func = getattr(cmd_runner, cmd.name)
        result = func(*args)
        return result

    def run(self):
        while self.is_running():
            self.server.handle_request()
        for k, wallet in self.wallets.items():
            wallet.stop_threads()
        if self.network_controller:
            self.print_error("shutting down network controller")
            self.network_controller.stop()
            self.network_controller.join()

    def stop(self):
        self.print_error("stopping, removing lockfile")
        remove_lockfile(get_lockfile(self.config))
        DaemonThread.stop(self)

    def init_gui(self, config, plugins):
        gui_name = config.get('gui', 'qt')
        if gui_name in ['lite', 'classic']:
            gui_name = 'qt'
        gui = __import__('encompass_gui.' + gui_name, fromlist=['encompass_gui'])
        self.gui = gui.ElectrumGui(config, self, plugins)
        self.gui.main()
