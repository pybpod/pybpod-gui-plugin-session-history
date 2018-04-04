# !/usr/bin/python3
# -*- coding: utf-8 -*-

""" session_window.py

"""

import logging

from pyforms import conf

from AnyQt.QtGui import QColor, QBrush
from AnyQt.QtCore import QTimer, QEventLoop, QAbstractTableModel, Qt, QSize, QVariant, pyqtSignal

from pyforms import conf

from pyforms import BaseWidget
from pyforms.controls import ControlProgress
from pyforms.controls import ControlButton
from pyforms.controls import ControlCheckBox
from pyforms.controls import ControlTableView
from pyforms.controls import ControlBoundingSlider
from AnyQt.QtWidgets import QApplication

#######################################################################
##### MESSAGES TYPES ##################################################
#######################################################################
from pybranch.com.messaging.error   import ErrorMessage
from pybranch.com.messaging.debug   import DebugMessage
from pybranch.com.messaging.stderr  import StderrMessage
from pybranch.com.messaging.stdout  import StdoutMessage
from pybranch.com.messaging.parser  import MessageParser
from pybpodapi.com.messaging.warning import WarningMessage

from pybpodapi.com.messaging.trial                  import Trial
from pybpodapi.com.messaging.event_occurrence       import EventOccurrence
from pybpodapi.com.messaging.state_occurrence       import StateOccurrence
from pybpodapi.com.messaging.softcode_occurrence    import SoftcodeOccurrence
from pybpodapi.com.messaging.event_resume           import EventResume
from pybpodapi.com.messaging.session_info           import SessionInfo
#######################################################################
#######################################################################
logger = logging.getLogger(__name__)


class PandasModel(QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe
    """
    COLOR_MSG                = QBrush( QColor(200,200,200) )
    COLOR_DEBUG              = QBrush( QColor(200,200,200) )
    COLOR_TRIAL              = QBrush( QColor(0,100,200) )
    COLOR_ERROR              = QBrush( QColor(240,0,0) )
    COLOR_INFO               = QBrush( QColor(150,150,255) )
    COLOR_SOFTCODE_OCCURENCE = QBrush( QColor(40,30,30) )
    COLOR_STATE_OCCURENCE    = QBrush( QColor(0,100,0) )
    COLOR_STDERR             = QBrush( QColor(255,0,0) )
    COLOR_STDOUT             = QBrush( QColor(150,150,150) )
    COLOR_TRIAL              = QBrush( QColor(0,0,255) )
    COLOR_WARNING            = QBrush( QColor(255,100,0) )
    
    COLUMNS_WIDTHS = [QSize(100,30), QSize(400,30), QSize(200,30), QSize(200,30), QSize(200,30), QSize(200,30)]

    def __init__(self, data, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.ForegroundRole:
                dtype = self._data.values[index.row()][0]

                if dtype=='debug':
                    return self.COLOR_DEBUG
                elif dtype=='END-TRIAL':
                    return self.COLOR_TRIAL
                elif dtype=='error':
                    return self.COLOR_ERROR
                elif dtype=='INFO':
                    return self.COLOR_INFO
                elif dtype=='SOFTCODE':
                    return self.COLOR_SOFTCODE_OCCURENCE
                elif dtype=='STATE':
                    return self.COLOR_STATE_OCCURENCE
                elif dtype=='stderr':
                    return self.COLOR_STDERR
                elif dtype=='stdout':
                    return self.COLOR_STDOUT
                elif dtype=='TRIAL':
                    return self.COLOR_TRIAL
                elif dtype=='warning':
                    return self.COLOR_WARNING
                else:
                    return self.COLOR_MSG

            elif role == Qt.DisplayRole:
                return str(self._data.values[index.row()][index.column()])

            
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        #elif orientation == Qt.Horizontal and role == Qt.SizeHintRole:
        #    return QVariant(self.COLUMNS_WIDTHS[col])

    def flags(self, index):
        return Qt.ItemIsEnabled


class SessionHistory(BaseWidget):
    """ Plugin main window """

    def __init__(self, session):
        BaseWidget.__init__(self, session.name)
        
        self.set_margin(5)

        self._progress    = ControlProgress('Progress', visible=False)
        self._reload      = ControlButton('Reload everything', default=self.__reload_evt)
        self._autoscroll  = ControlCheckBox('Auto-scroll', default=True,  changed_event=self.__auto_scroll_evt)
        self._log         = ControlTableView(select_entire_row=True)

        self._formset = [
            ('_autoscroll',' ',' ','_reload',),
            '_log',
            '_progress'
        ]

        self.session = session
        self._colors = {}

        self._progress.hide()

        self._timer = QTimer()

        self._log.value = self.model = PandasModel(session.data)
        self._timer.timeout.connect(self.__update_table_view)

    def __update_table_view(self):
        self._log.value = None
        self._log.value = self.model
        if self._autoscroll.value:
            self._log.scrollToBottom()

    def __reload_evt(self):
        self._history_index = 0
        #self._log.clear()
        self._stop = False # flag used to close the gui in the middle of a loading
        self.read_message_queue(True)

    def __auto_scroll_evt(self):
        #self._log.autoscroll = self._autoscroll.value
        pass
    
    def show(self, detached=False):
        if self.session.is_running and self.session.setup.detached:
            return

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

        #in case the session is still running load the latest 200 messages
        if self.session.is_running:
            self._history_index = len(self.session.messages_history)-200 if len(self.session.messages_history)>200 else 0
            self._reload.enabled = False
        else:
            self._history_index  = 0
            self._reload.enabled = True

        self._stop = False # flag used to close the gui in the middle of a loading
        self.read_message_queue(True)
        if not self._stop and self.session.is_running:
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

        # check if the session is running. If not stops the timer
        if not self.session.is_running: self._timer.stop()

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

            self._log.form.setUpdatesEnabled(True)

        
            
        except Exception as err:
            if hasattr(self, '_timer'):
                self._timer.stop()
            logger.error(str(err), exc_info=True)
            self.alert("Unexpected error while loading session history. Pleas see log for more details.", "Error")

        if update_gui:
            self._progress.hide()

        if not self.session.is_running:
            self._reload.enabled = True

    @property
    def mainwindow(self):
        return self.session.mainwindow

    @property
    def title(self):
        return BaseWidget.title.fget(self)

    @title.setter
    def title(self, value):
        BaseWidget.title.fset(self, 'Session History: {0}'.format(value))
