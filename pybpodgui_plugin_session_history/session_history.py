# !/usr/bin/python3
# -*- coding: utf-8 -*-

""" session_window.py

"""

import logging

from pysettings import conf

if conf.PYFORMS_USE_QT5:
	from PyQt5.QtWidgets import QMessageBox
	from PyQt5.QtCore import QTimer, QEventLoop
else:
	from PyQt4.QtGui import QMessageBox
	from PyQt4.QtCore import QTimer, QEventLoop

from pysettings import conf

from pyforms import BaseWidget
from pyforms.Controls import ControlProgress
from pyforms.Controls import ControlList

from pyforms_generic_editor.com.messaging.history_message import HistoryMessage
from pyforms_generic_editor.com.messaging.board_message import BoardMessage
from pybpodgui_plugin.com.messaging import ErrorMessage
from pybpodgui_plugin.com.messaging import PrintStatement
from pybpodgui_plugin.com.messaging import StateChange
from pybpodgui_plugin.com.messaging import StateEntry
from pybpodgui_plugin.com.messaging import EventOccurrence

logger = logging.getLogger(__name__)


class SessionHistory(BaseWidget):
	""" Plugin main window """

	def __init__(self, session):
		BaseWidget.__init__(self, session.name)
		self.layout().setContentsMargins(5, 5, 5, 5)

		self.session = session

		self._log = ControlList()
		self._progress = ControlProgress('Loading', 0, 1, 100)

		self._formset = [
			'_log',
			'_progress'
		]

		self._history_index = 0
		self._log.readonly = True
		self._log.horizontal_headers = ['#', 'Type', 'Name', 'Channel Id', 'Start', 'End', 'PC timestamp']
		self._log.tableWidget.setSortingEnabled(True)

		self._progress.hide()

		self._timer = QTimer()
		self._timer.timeout.connect(self.read_message_queue)

	def show(self):
		# Prevent the call to be recursive because of the mdi_area
		if hasattr(self, '_show_called'):
			BaseWidget.show(self)
			return
		self._show_called = True
		self.mainwindow.mdi_area += self
		del self._show_called

		self.read_message_queue(True)
		self._timer.start(conf.SESSIONLOG_PLUGIN_REFRESH_RATE)

	def hide(self):
		self._timer.stop()

	def beforeClose(self):
		self._timer.stop()
		return False

	def read_message_queue(self, update_gui=False):
		""" Update board queue and retrieve most recent messages """
		messages_history = self.session.messages_history
		recent_history = messages_history[self._history_index:]

		if update_gui:
			self._progress.show()
			self._progress.value = 0
		try:
			for message in recent_history:

				table_line = None
				if issubclass(type(message), StateChange):
					table_line = (self._history_index, message.MESSAGE_TYPE_ALIAS, message.event_name,
					              '', message.board_timestamp, message.board_timestamp, message.pc_timestamp)

				if issubclass(type(message), StateEntry):
					table_line = (self._history_index, message.MESSAGE_TYPE_ALIAS, message.state_name,
					              '', message.start_timestamp, message.end_timestamp, message.pc_timestamp)

				if issubclass(type(message), EventOccurrence):
					table_line = (self._history_index, message.MESSAGE_TYPE_ALIAS, message.event_name,
					              message.event_id, '', '', message.pc_timestamp)

				if table_line:
					self._log += table_line
					QEventLoop()

					if update_gui:
						self._progress += 1
						if self._progress.value >= 99: self._progress.value = 0

				self._history_index += 1

		except Exception as err:
			if hasattr(self, '_timer'):
				self._timer.stop()
			logger.error(str(err), exc_info=True)
			QMessageBox.critical(self, "Error",
			                     "Unexpected error while loading session history. Pleas see log for more details.")

		if update_gui:
			self._progress.hide()

	@property
	def mainwindow(self):
		return self.session.mainwindow

	@property
	def title(self):
		return BaseWidget.title.fget(self)

	@title.setter
	def title(self, value):
		BaseWidget.title.fset(self, 'Session History: {0}'.format(value))
