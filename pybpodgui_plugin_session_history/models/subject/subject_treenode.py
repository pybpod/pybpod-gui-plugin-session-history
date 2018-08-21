import logging

from confapp import conf

from AnyQt.QtGui import QIcon
from pybpodgui_plugin_session_history.session_history import SessionHistory

logger = logging.getLogger(__name__)


class SubjectTreeNode(object):

    def create_sessiontreenode(self, session):
        """
        :param session: 
        :return: 
        """
        node = super(SubjectTreeNode, self).create_sessiontreenode(session)

        self.sessionhistory_action = self.tree.add_popup_menu_option(
            'History', 
            session.open_sessionhistory_win,
            item=node,
            icon=QIcon(conf.SESSIONLOG_PLUGIN_ICON)
        )

        self.sessionhistory_detached_action = self.tree.add_popup_menu_option(
            'History (detached)', 
            session.open_sessionhistory_win_detached,
            item=node,
            icon=QIcon(conf.SESSIONLOG_PLUGIN_ICON)
        )

        return node

    def node_double_clicked_event(self):
        super(SubjectTreeNode, self).node_double_clicked_event()

        self.open_sessionhistory_win()

    def remove(self):
        if hasattr(self, 'sessionhistory_win'): self.mainwindow.mdi_area -= self.sessionhistory_win
        super(SubjectTreeNode, self).remove()

    @property
    def name(self):
        return super(SubjectTreeNode, self.__class__).name.fget(self)

    @name.setter
    def name(self, value):
        super(SubjectTreeNode, self.__class__).name.fset(self, value)
        if hasattr(self, 'sessionhistory_win'): self.sessionhistory_win.title = value

