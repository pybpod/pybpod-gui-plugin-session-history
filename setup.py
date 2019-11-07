#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import re

version = ''
with open('pybpodgui_plugin_session_history/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

setup(
    name='pybpod-gui-plugin-session-history',
    version=version,
    description="""PyBpod GUI session log plugin""",
    author='Carlos Mão de Ferro, Ricardo Jorge Vieira Ribeiro, Luís Teixeira',
    author_email='cajomferro@gmail.com, ricardojvr@gmail.com, micboucinha@gmail.com',
    license='MIT',
    url='https://github.com/pybpod/pybpod-gui-plugin-session-history',

    include_package_data=True,
    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'examples', 'deploy', 'reports']),

    package_data={'pybpodgui_plugin_session_history': [
        'resources/*.*',
    ]
    },
)
