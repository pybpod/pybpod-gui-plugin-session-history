# !/usr/bin/python3
# -*- coding: utf-8 -*-

""" session_window.py

"""

import logging

from confapp import conf

from AnyQt.QtGui import QColor, QBrush
from AnyQt.QtCore import QTimer, QEventLoop, QAbstractTableModel, Qt, QSize, QVariant, pyqtSignal

from confapp import conf
from pyforms.basewidget import BaseWidget
from pyforms.controls import ControlCheckBox
from pyforms.controls import ControlTableView

from pybpodapi.session import Session

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
    COLOR_STATE_OCCURENCE    = QBrush( QColor(70,180,70) )
    COLOR_STATE_TRANSITION   = QBrush( QColor(0,100,0) )
    COLOR_STDERR             = QBrush( QColor(255,0,0) )
    COLOR_STDOUT             = QBrush( QColor(150,150,150) )
    COLOR_TRIAL              = QBrush( QColor(0,0,255) )
    COLOR_WARNING            = QBrush( QColor(255,100,0) )
    
    COLUMNS_WIDTHS = [QSize(100,30), QSize(400,30), QSize(200,30), QSize(200,30), QSize(200,30), QSize(200,30)]

    def __init__(self, data, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data.values) if self._data is not None else 0

    def columnCount(self, parent=None):
        return self._data.columns.size if self._data is not None else 0

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.ForegroundRole:
                dtype = self._data.values[index.row()][0]

                if   dtype==Session.MSGTYPE_DEBUG:      return self.COLOR_DEBUG
                elif dtype==Session.MSGTYPE_ENDTRIAL:   return self.COLOR_TRIAL
                elif dtype==Session.MSGTYPE_ERROR:      return self.COLOR_ERROR
                elif dtype==Session.MSGTYPE_INFO:       return self.COLOR_INFO
                elif dtype==Session.MSGTYPE_SOFTCODE:   return self.COLOR_SOFTCODE_OCCURENCE
                elif dtype==Session.MSGTYPE_STATE:      return self.COLOR_STATE_OCCURENCE
                elif dtype==Session.MSGTYPE_TRANSITION: return self.COLOR_STATE_TRANSITION
                elif dtype==Session.MSGTYPE_STDERR:     return self.COLOR_STDERR
                elif dtype==Session.MSGTYPE_STDOUT:     return self.COLOR_STDOUT
                elif dtype==Session.MSGTYPE_TRIAL:      return self.COLOR_TRIAL
                elif dtype==Session.MSGTYPE_WARNING:    return self.COLOR_WARNING
                else:                                   return self.COLOR_MSG

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

        self._autoscroll  = ControlCheckBox('Auto-scroll', default=True)
        self._log         = ControlTableView(select_entire_row=True)

        self._formset = [
            ('_autoscroll',' ',' ',' ',),
            '_log'
        ]

        self.session    = session
        self._log.value = self.model = PandasModel(session.data)
        
        self._timer = QTimer()
        self._timer.timeout.connect(self.__update_table_view)

    def __update_table_view(self):
        # check if the session is running. If not stops the timer
        if not self.session.is_running: self._timer.stop()

        self._log.value = None
        self._log.value = self.model
        if self._autoscroll.value: self._log.scrollToBottom()

    
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

        
        self._stop = False # flag used to close the gui in the middle of a loading
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

    @property
    def mainwindow(self): return self.session.mainwindow

    @property
    def title(self): return BaseWidget.title.fget(self)
    @title.setter
    def title(self, value):  BaseWidget.title.fset(self, 'Session History: {0}'.format(value))
