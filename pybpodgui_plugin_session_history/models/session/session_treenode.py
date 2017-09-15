# !/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from pysettings import conf

if conf.PYFORMS_USE_QT5:
	from PyQt5.QtGui import QIcon
else:
	from PyQt4.QtGui import QIcon

from pybpodgui_plugin_session_history.session_history import SessionHistory

logger = logging.getLogger(__name__)


class SessionTreeNode(object):
	def create_treenode(self, tree):
		"""
		
		:param tree: 
		:return: 
		"""
		node = super(SessionTreeNode, self).create_treenode(tree)

		tree.add_popup_menu_option(
			'History', 
			self.open_session_history_plugin,
			item=self.node,
			icon=QIcon(conf.SESSIONLOG_PLUGIN_ICON)
		)

		tree.add_popup_menu_option(
			'History (detached)', 
			self.open_session_history_plugin_detached,
			item=self.node,
			icon=QIcon(conf.SESSIONLOG_PLUGIN_ICON)
		)

		return node

	def node_double_clicked_event(self):
		super(SessionTreeNode, self).node_double_clicked_event()
		self.open_session_history_plugin()

	def open_session_history_plugin(self):
		if not hasattr(self, 'session_history_plugin'):
			self.session_history_plugin = SessionHistory(self)
			self.session_history_plugin.show()
			self.session_history_plugin.subwindow.resize(*conf.SESSIONLOG_PLUGIN_WINDOW_SIZE)
		else:
			self.session_history_plugin.show()

	def open_session_history_plugin_detached(self):
		if not hasattr(self, 'session_history_plugin_detached'):
			self.session_history_plugin_detached = SessionHistory(self)
			self.session_history_plugin_detached.show(True)
			self.session_history_plugin_detached.resize(*conf.SESSIONLOG_PLUGIN_WINDOW_SIZE)
		else:
			self.session_history_plugin_detached.show(True)
	

	def remove(self):
		if hasattr(self, 'session_history_plugin'): self.mainwindow.mdi_area -= self.session_history_plugin
		super(SessionTreeNode, self).remove()

	@property
	def name(self):
		return super(SessionTreeNode, self.__class__).name.fget(self)

	@name.setter
	def name(self, value):
		super(SessionTreeNode, self.__class__).name.fset(self, value)
		if hasattr(self, 'session_history_plugin'): self.session_history_plugin.title = value
