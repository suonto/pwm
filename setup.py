#!/usr/bin/env python
# coding: utf-8
̈́'''
suonto.com password manager
'''

# sudo apt-get install python-qt4

import sys
from setuptools import setup

install_requires = [
    'Twisted',
    'requests',
    'pyOpenSSL',
    'pycrypto',
    'simplejson',
]

# Works at least on python 2.7.*

setup(
    name='suonto.com password manager',
    version='1.0',
    author='Markus Suonto',
    author_email='markus.suonto@aalto.fi',
    url='https://github.com/suonto/pwm',
    description="A single computer access, knowledgeless server storage system.",
    py_modules=['http_server.py, gui.py'],
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'server = http_server:main',
            'gui = gui:main',
        ]
    },
    classifiers=[
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
         'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        # 'Intended Audience :: Customer Service',
        'Intended Audience :: Developers',
        # 'Intended Audience :: Education',
        'Intended Audience :: End Users/Desktop',
        # 'Intended Audience :: Financial and Insurance Industry',
        # 'Intended Audience :: Healthcare Industry',
        # 'Intended Audience :: Information Technology',
        # 'Intended Audience :: Legal Industry',
        # 'Intended Audience :: Manufacturing',
        # 'Intended Audience :: Other Audience',
        # 'Intended Audience :: Religion',
        # 'Intended Audience :: Science/Research',
        # 'Intended Audience :: System Administrators',
        # 'Intended Audience :: Telecommunications Industry',
         'License :: OSI Approved :: MIT License',
        # 'Programming Language :: Python :: 2.6',
         'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
        # 'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        # 'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        # 'Topic :: Security',
    ],

)



