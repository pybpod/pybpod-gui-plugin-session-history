# !/usr/bin/python3
# -*- coding: utf-8 -*-

__version__ = "1.3.0beta"

from pysettings import conf

conf += 'pybpodgui_plugin_session_history.settings'
conf += 'pybpodgui_plugin_session_history.resources'


import loggingbootstrap

# setup different loggers but output to single file
loggingbootstrap.create_double_logger("pybpodgui_plugin_session_history", conf.BPODGUI_LOG_HANDLER_CONSOLE_LEVEL,
									  conf.APP_LOG_FILENAME,
									  conf.BPODGUI_LOG_HANDLER_FILE_LEVEL)