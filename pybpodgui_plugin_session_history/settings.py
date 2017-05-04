#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os

SETTINGS_PRIORITY = 80

# THESE SETTINGS ARE NEEDED FOR PYSETTINGS
PYFORMS_USE_QT5 = True

SESSIONLOG_PLUGIN_ICON = os.path.join(os.path.dirname(__file__), 'resources', 'history.png')

SESSIONLOG_PLUGIN_WINDOW_SIZE 	= 300, 500
SESSIONLOG_PLUGIN_REFRESH_RATE 	= 1000
