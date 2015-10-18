#!/usr/bin/env python2

# python setup.py sdist --format=zip,gztar

from setuptools import setup
import os
import sys
import platform
import imp

version = imp.load_source('version', 'lib/version.py')

if sys.version_info[:3] < (2, 7, 0):
    sys.exit("Error: Encompass requires Python version >= 2.7.0...")

data_files = []

if platform.system() in ['Linux', 'FreeBSD', 'DragonFly']:
    usr_share = os.path.join(sys.prefix, "share")
    data_files += [
        (os.path.join(usr_share, 'applications/'), ['encompass.desktop']),
        (os.path.join(usr_share, 'pixmaps/'), ['icons/encompass.png'])
    ]

setup(
    name="Encompass",
    version=version.ELECTRUM_VERSION,
    install_requires=[
        'slowaes>=0.1a1',
        'ecdsa>=0.9',
        'pbkdf2',
        'requests',
        'qrcode',
        'protobuf',
        'dnspython',
    ],
    package_dir={
        'encompass': 'lib',
        'encompass_gui': 'gui',
        'encompass_plugins': 'plugins',
    },
    packages=['encompass','encompass_gui','encompass_gui.qt','encompass_plugins'],
    package_data={
        'encompass': [
            'www/index.html',
            'wordlist/*.txt',
            'locale/*/LC_MESSAGES/electrum.mo',
        ]
    },
    scripts=['encompass'],
    data_files=data_files,
    description="Lightweight Multi-Coin Wallet",
    author="Tyler Willis, Rob Nelson, mazaclub",
    author_email="encompass-security@maza.club",
    license="GNU GPLv3",
    url="https://maza.club/encompass",
    long_description="""Lightweight Multi-Coin Wallet for Electrum-supported coins."""
)
