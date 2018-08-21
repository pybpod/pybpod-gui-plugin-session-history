# !/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from confapp import conf

from AnyQt.QtGui import QIcon
from pybpodgui_plugin_session_history.session_history import SessionHistory

logger = logging.getLogger(__name__)


class SessionTreeNode(object):
    def create_treenode(self, tree):
        """
        
        :param tree: 
        :return: 
        """
        node = super(SessionTreeNode, self).create_treenode(tree)

        self.sessionhistory_action = tree.add_popup_menu_option(
            'History', 
            self.open_sessionhistory_win,
            item=self.node,
            icon=QIcon(conf.SESSIONLOG_PLUGIN_ICON)
        )

        self.sessionhistory_detached_action = tree.add_popup_menu_option(
            'History (detached)', 
            self.open_sessionhistory_win_detached,
            item=self.node,
            icon=QIcon(conf.SESSIONLOG_PLUGIN_ICON)
        )

        return node

    def node_double_clicked_event(self):
        super(SessionTreeNode, self).node_double_clicked_event()

        
        self.open_sessionhistory_win()

    def open_sessionhistory_win(self):
        if self.is_running and self.setup.detached:
            return

        self.load_contents()

        #does not show the window if the detached window is visible
        if hasattr(self, 'sessionhistory_win_detached') and self.sessionhistory_win_detached.visible: return 

        if not hasattr(self, 'sessionhistory_win'):
            self.sessionhistory_win = SessionHistory(self)
            self.sessionhistory_win.show()
            self.sessionhistory_win.subwindow.resize(*conf.SESSIONLOG_PLUGIN_WINDOW_SIZE)
        else:
            self.sessionhistory_win.show()

        self.sessionhistory_action.setEnabled(False)
        self.sessionhistory_detached_action.setEnabled(False)

    def open_sessionhistory_win_detached(self):
        if self.is_running and self.setup.detached:
            return

        self.load_contents()
        
        #does not show the window if the attached window is visible
        if hasattr(self, 'sessionhistory_win') and self.sessionhistory_win.visible: return 

        if not hasattr(self, 'sessionhistory_win_detached'):
            self.sessionhistory_win_detached = SessionHistory(self)
            self.sessionhistory_win_detached.show(True)
            self.sessionhistory_win_detached.resize(*conf.SESSIONLOG_PLUGIN_WINDOW_SIZE)
        else:
            self.sessionhistory_win_detached.show(True)

        self.sessionhistory_action.setEnabled(False)
        self.sessionhistory_detached_action.setEnabled(False)



    def remove(self):
        if hasattr(self, 'sessionhistory_win'): self.mainwindow.mdi_area -= self.sessionhistory_win
        super(SessionTreeNode, self).remove()

    @property
    def name(self):
        return super(SessionTreeNode, self.__class__).name.fget(self)

    @name.setter
    def name(self, value):
        super(SessionTreeNode, self.__class__).name.fset(self, value)
        if hasattr(self, 'sessionhistory_win'): self.sessionhistory_win.title = value
