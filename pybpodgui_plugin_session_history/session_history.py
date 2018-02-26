# !/usr/bin/python3
# -*- coding: utf-8 -*-

""" session_window.py

"""

import logging

from pyforms import conf

from AnyQt.QtGui import QColor
from AnyQt.QtCore import QTimer, QEventLoop

from pyforms import conf

from pyforms import BaseWidget
from pyforms.controls import ControlProgress
from pyforms.controls import ControlButton
from pyforms.controls import ControlCheckBox
from pyforms.controls import ControlList
from pyforms.controls import ControlBoundingSlider
from AnyQt.QtWidgets import QApplication

#######################################################################
##### MESSAGES TYPES ##################################################
#######################################################################
from pybranch.com.messaging.error   import ErrorMessage
from pybranch.com.messaging.debug   import DebugMessage
from pybranch.com.messaging.stderr  import StderrMessage
from pybranch.com.messaging.stdout  import StdoutMessage
from pybranch.com.messaging.warning import WarningMessage
from pybranch.com.messaging.parser  import MessageParser

from pybpodapi.com.messaging.trial                  import Trial
from pybpodapi.com.messaging.event_occurrence       import EventOccurrence
from pybpodapi.com.messaging.state_occurrence       import StateOccurrence
from pybpodapi.com.messaging.softcode_occurrence    import SoftcodeOccurrence
from pybpodapi.com.messaging.event_resume           import EventResume
from pybpodapi.com.messaging.session_info           import SessionInfo
#######################################################################
#######################################################################




logger = logging.getLogger(__name__)


class SessionHistory(BaseWidget):
    """ Plugin main window """

    def __init__(self, session):
        BaseWidget.__init__(self, session.name)
        
        self.set_margin(5)

        self._progress    = ControlProgress('Progress', visible=False)
        self._lastentries = ControlCheckBox('Show only the last entries', default=True, changed_event=self.__lastentries_changed_evt)
        self._range       = ControlBoundingSlider('Entries to load', 0, 0, 100)
        self._autoscroll  = ControlCheckBox('Auto-scroll', default=True,  changed_event=self.__auto_scroll_evt)
        self._log         = ControlList(
            readonly=True, autoscroll=True, resizecolumns=False,
            horizontal_headers = ['#', 'Type', 'Name', 'Channel Id', 'Start', 'End', 'PC timestamp']
        )

        self._formset = [
            ('_lastentries', '_autoscroll'),
            '_range',
            '_log',
            '_progress'
        ]

        self.session        = session
        self._history_index = (len(session.messages_history)-200) if len(session.messages_history)>200 else 0
        self._range.max     = len(session.messages_history)
        self._range.value   = [self._history_index, len(session.messages_history)]
        self._colors        = {}

        self._progress.hide()

        self._timer = QTimer()
        self._timer.timeout.connect(self.read_message_queue)


    def __lastentries_changed_evt(self):
        QApplication.processEvents()

        self._log.clear()
        self._stop = False
            
        if self._lastentries.value:
            self._history_index = len(self.session.messages_history)-200
        else:
            self._history_index = 0

        self.read_message_queue(True)



    def __auto_scroll_evt(self):
        self._log.autoscroll = self._autoscroll.value

    
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
            
        self._stop = False # flag used to close the gui in the middle of a loading
        self.read_message_queue(True)
        if not self._stop and self.session.status==self.session.STATUS_SESSION_RUNNING: 
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
        recent_history   = messages_history[self._history_index:]

        if update_gui:
            self._progress.show()
            self._progress.value = 0
            self._progress.max   = len(recent_history)
        try:

            self._log.form.setUpdatesEnabled(False)

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
                    
                    if update_gui:  self._progress += 1


        
                QApplication.processEvents()
                self._history_index += 1

            self._range.max   = self._history_index
            self._range.value = [self._range.value[0], self._history_index]
            self._log.form.setUpdatesEnabled(True)

        
            
        except Exception as err:
            if hasattr(self, '_timer'):
                self._timer.stop()
            logger.error(str(err), exc_info=True)
            self.alert("Unexpected error while loading session history. Pleas see log for more details.", "Error")

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
