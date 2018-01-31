# !/usr/bin/python3
# -*- coding: utf-8 -*-

""" session_window.py

"""

import logging

from pysettings import conf

if conf.PYFORMS_USE_QT5:
	from PyQt5.QtWidgets import QMessageBox
	from PyQt5.QtGui import QColor
	from PyQt5.QtCore import QTimer, QEventLoop
else:
	from PyQt4.QtGui import QMessageBox, QColor
	from PyQt4.QtCore import QTimer, QEventLoop

from pysettings import conf

from pyforms import BaseWidget
from pyforms.controls import ControlProgress
from pyforms.controls import ControlCheckBox
from pyforms.controls import ControlList

#######################################################################
##### MESSAGES TYPES ##################################################
#######################################################################
from pybranch.com.messaging.error 	import ErrorMessage
from pybranch.com.messaging.debug 	import DebugMessage
from pybranch.com.messaging.stderr 	import StderrMessage
from pybranch.com.messaging.stdout 	import StdoutMessage
from pybranch.com.messaging.warning import WarningMessage
from pybranch.com.messaging.parser  import MessageParser

from pybpodapi.com.messaging.trial					import Trial
from pybpodapi.com.messaging.event_occurrence 		import EventOccurrence
from pybpodapi.com.messaging.state_occurrence 		import StateOccurrence
from pybpodapi.com.messaging.softcode_occurrence 	import SoftcodeOccurrence
from pybpodapi.com.messaging.event_resume 			import EventResume
from pybpodapi.com.messaging.session_info 			import SessionInfo
#######################################################################
#######################################################################




logger = logging.getLogger(__name__)


class SessionHistory(BaseWidget):
	""" Plugin main window """

	def __init__(self, session):
		BaseWidget.__init__(self, session.name)
		
		self.set_margin(5)

		self._progress = ControlProgress('Progress', visible=False)
		self._autoscroll_checkbox = ControlCheckBox('Auto-scroll', True)
		self._autoscroll_checkbox.changed_event = self.__auto_scroll_evt

		self._log 		= ControlList()

		self._formset = [
			(' ', '_autoscroll_checkbox'),
			'_log',
			'_progress'
		]

		self.session 					= session
		self._history_index 			= 0
		self._log.readonly 				= True
		self._log.horizontal_headers 	= ['#', 'Type', 'Name', 'Channel Id', 'Start', 'End', 'PC timestamp']
		self._log.set_sorting_enabled(True)
		self._log.autoscroll 			= True

		self._colors = {}

		self._progress.hide()


		self._timer = QTimer()
		self._timer.timeout.connect(self.read_message_queue)

	def __auto_scroll_evt(self):
		self._log.autoscroll = self._autoscroll_checkbox.value

	
	def show(self, detached=False):
		# Prevent the call to be recursive because of the mdi_area
		if not detached:
			if hasattr(self, '_show_called'):
				BaseWidget.show(self)
				return
			self._show_called = True
			self.mainwindow.mdi_area += self
			del self._show_called
		else:
			BaseWidget.show(self)
			
		self._stop  = False # flag used to close the gui in the middle of a loading
		self.read_message_queue(True)
		if not self._stop: 
			self._timer.start(conf.SESSIONLOG_PLUGIN_REFRESH_RATE)

	def hide(self):
		self._timer.stop()
		self._stop = True
		
	def before_close_event(self):		
		self._timer.stop()
		self._stop = True
		self.session.sessionhistory_action.setEnabled(True)
		self.session.sessionhistory_detached_action.setEnabled(True)

	def read_message_queue(self, update_gui=False):
		""" Update board queue and retrieve most recent messages """
		messages_history = self.session.messages_history
		recent_history = messages_history[self._history_index:]

		if update_gui:
			self._progress.show()
			self._progress.value = 0
			self._progress.max = len(recent_history)
		try:

			for msg in recent_history:
				if self._stop: return
				row = None


				if issubclass( type(msg), StderrMessage):
					row = [
						self._history_index, 
						msg.MESSAGE_TYPE_ALIAS, 
						str(msg.content) + ' | ' + str(msg.traceback),
						'-',
						str(msg.host_timestamp) if msg.host_timestamp else '-',
						'-', 
						str(msg.pc_timestamp)
					]

				elif issubclass(type(msg), StateOccurrence):
					row = [
						self._history_index, 
						msg.MESSAGE_TYPE_ALIAS, 
						msg.content,
						'-',
						str(msg.start_timestamp),
						str(msg.end_timestamp), 
						str(msg.pc_timestamp)
					]

				elif issubclass(type(msg), SessionInfo):
					row = [
						self._history_index, 
						msg.MESSAGE_TYPE_ALIAS, 
						"{0}={1}".format(msg.infoname,msg.infovalue) if msg.infovalue else msg.infoname,
						'-',
						'-',
						'-', 
						str(msg.pc_timestamp)
					]
				elif issubclass(type(msg), (EventOccurrence, EventResume)):
					row = [
						self._history_index, 
						msg.MESSAGE_TYPE_ALIAS, 
						msg.event_name,
						msg.event_id,
						str(msg.host_timestamp) if msg.host_timestamp is not None else '-',
						'-', 
						str(msg.pc_timestamp)
					]					
				else:
					row = [
						self._history_index, 
						msg.MESSAGE_TYPE_ALIAS, 
						str(msg.content),
						'-',
						str(msg.host_timestamp) if msg.host_timestamp else '-',
						'-', 
						str(msg.pc_timestamp)
					]


				if row:
					self._log += row

					
					if msg.MESSAGE_COLOR:

						if msg.MESSAGE_COLOR not in self._colors:
							color = self._colors[msg.MESSAGE_COLOR] = QColor(*msg.MESSAGE_COLOR)
						else:
							color = self._colors[msg.MESSAGE_COLOR]

						for i in range(len(row)):
							self._log.get_cell(i, len(self._log)-1 ).setForeground(color)
					
					

					if update_gui:
						self._progress += 1
						#if self._progress.value >= 99: self._progress.value = 0


				QEventLoop()
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
