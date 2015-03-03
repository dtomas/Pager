import rox
from rox import g, processes
import os, wnck, gobject
import pixbuf_helper

def load_icons(icon_theme):
	global dir_icon, home_icon
	for icon_name in ['mime-inode:directory', 'folder', 'gnome-fs-directory']:
		try:
			dir_icon = icon_theme.load_icon(icon_name, 32, 0)
			break
		except:
			pass
	for icon_name in ['user-home', 'gnome-fs-home']:
		try:
			home_icon = icon_theme.load_icon(icon_name, 32, 0)
			break
		except:
			pass

screen = wnck.screen_get_default()
icon_theme = g.icon_theme_get_default()
icon_theme.connect("changed", load_icons)
dir_icon = None
load_icons(icon_theme)

def _kill(menu_item, pids, name):
	if rox.confirm(_("Really force %s to quit?") % name, 
								g.STOCK_QUIT, _("Force quit")):
		for pid in pids:
			rox.processes.PipeThroughCommand(('kill', pid), None, None).start()

def _winaction(menu_item, window, func):
	func(window)
	
def _winaction2(menu_item, window, func):
	func(window, g.get_current_event_time())

def _move_to_workspace(menu_item, window, workspace):
	window.move_to_workspace(workspace)
	
def _minimize(menu_item, window):
	window.unshade()
	window.minimize()

def create_window_action_menu(window, has_kill = False, 
							menu_item = None, parent = None):
	menu = g.Menu()
	
	item = g.ImageMenuItem(_("Activate"))
	item.get_image().set_from_stock(g.STOCK_YES, g.ICON_SIZE_MENU)
	item.connect("activate", _winaction2, window, wnck.Window.activate)
	menu.append(item)
	
	menu.append(g.SeparatorMenuItem())
	
	if window.is_maximized():
		item = g.ImageMenuItem(_("Unmaximize"))
		item.get_image().set_from_stock(g.STOCK_ZOOM_OUT, g.ICON_SIZE_MENU)
		item.connect("activate", _winaction, window, wnck.Window.unmaximize)
	else:
		item = g.ImageMenuItem(_("Maximize"))
		item.get_image().set_from_stock(g.STOCK_ZOOM_100, g.ICON_SIZE_MENU)
		item.connect("activate", _winaction, window, wnck.Window.maximize)
	menu.append(item)

	if window.is_minimized():
		item = g.ImageMenuItem(_("Show"))
		item.get_image().set_from_stock(g.STOCK_REDO, g.ICON_SIZE_MENU)
		item.connect("activate", _winaction2, window, wnck.Window.unminimize)
	else:
		item = g.ImageMenuItem(_("Hide"))
		item.get_image().set_from_stock(g.STOCK_UNDO, g.ICON_SIZE_MENU)
		item.connect("activate", _minimize, window)
	menu.append(item)
	
	if window.is_shaded():
		item = g.ImageMenuItem(_("Unshade"))
		item.get_image().set_from_stock(g.STOCK_GOTO_BOTTOM, g.ICON_SIZE_MENU)
		item.connect("activate", _winaction, window, wnck.Window.unshade)
	else:
		item = g.ImageMenuItem(_("Shade"))
		item.get_image().set_from_stock(g.STOCK_GOTO_TOP, g.ICON_SIZE_MENU)
		item.connect("activate", _winaction, window, wnck.Window.shade)
	menu.append(item)

	menu.append(g.SeparatorMenuItem())
	
	if window.is_pinned() or window.is_sticky():
		item = g.ImageMenuItem(_("Only on this workspace"))
		item.get_image().set_from_stock(g.STOCK_REMOVE, g.ICON_SIZE_MENU)
		item.connect("activate", _winaction, window, wnck.Window.unstick)
		item.connect("activate", _winaction, window, wnck.Window.unpin)
	else:
		item = g.ImageMenuItem(_("Always on visible workspace"))
		item.get_image().set_from_stock(g.STOCK_ADD, g.ICON_SIZE_MENU)
		item.connect("activate", _winaction, window, wnck.Window.stick)
		item.connect("activate", _winaction, window, wnck.Window.pin)
	menu.append(item)

	if screen.get_workspace_count() > 1:
		item = g.ImageMenuItem(_("Move to workspace"))
		item.get_image().set_from_stock(g.STOCK_JUMP_TO, g.ICON_SIZE_MENU)
		menu.append(item)
		submenu = g.Menu()
		item.set_submenu(submenu)
		for i in range(0, screen.get_workspace_count()):
			workspace = screen.get_workspace(i)
			item = g.MenuItem(workspace.get_name())
			if workspace != window.get_workspace():
				item.connect("activate", _move_to_workspace, window, workspace)
			else:
				item.set_sensitive(False)
			submenu.append(item)
			
	if has_kill:
		menu.append(g.SeparatorMenuItem())

		pid = window.get_application().get_pid()
		item = g.ImageMenuItem(_("Force quit"))
		item.get_image().set_from_stock(g.STOCK_QUIT, g.ICON_SIZE_MENU)
		menu.append(item)	
		item.connect("activate", _kill, [pid], window.get_application().get_name())

	menu.append(g.SeparatorMenuItem())

	if menu_item and parent and menu_item.path:
		item = g.ImageMenuItem(_("Close subdirectories"))
		item.get_image().set_from_stock(g.STOCK_CLOSE, g.ICON_SIZE_MENU)
		item.connect("activate", parent._close_subdirs, menu_item.path)
		menu.append(item)

	item = g.ImageMenuItem(g.STOCK_CLOSE)
	item.connect("activate", _winaction2, window, wnck.Window.close)
	menu.append(item)

	return menu

def get_filer_window_path(window):
	name = window.get_name()
	if (window.get_class_group().get_name() != 'ROX-Filer'
		or not (name.startswith('/') or name.startswith('~'))):
		return ''
	for i in range(1-len(name), 0):
		if name[-i] == '(' or name[-i] == '+':
			name = name[:-(i+1)]
			break
	return name

class WindowMenuItem(g.ImageMenuItem):
	"""A menu item representing a window."""
	
	def __init__(self, window, icon, root = None, root_icon = None):
		"""Creates a new WindowMenuItem."""
		pixbuf = None
		self.path = get_filer_window_path(window)
		if self.path:
			name = self.path
			if root:
				root_dirname = os.path.dirname(root)
				if root_dirname == '/':
					l = 1
				else:
					l = len(root_dirname) + 1
				if name != '/':
					name = os.path.expanduser(name)[l:]
					name = name.replace(os.path.expanduser('~'), '~')
		else:
			name = window.get_name()
		size = 22
		if window.is_minimized():
		#	size = 16
			name = "[ " + name + " ]"
		if window.is_shaded():
		#	size = 22
			name = "= " + name + " ="
		if window.needs_attention():
			name = "!!! " + name + " !!!"
		if window == screen.get_active_window():
			size = 32
		g.ImageMenuItem.__init__(self, name.replace('_', '__'))
		if self.path:
			icon_path = os.path.expanduser(os.path.join(self.path, '.DirIcon'))
			if os.access(icon_path, os.F_OK):
				pixbuf = g.gdk.pixbuf_new_from_file(icon_path)
			elif self.path != root:
				if os.path.expanduser(self.path) == os.path.expanduser('~'):
					pixbuf = home_icon
				else:
					pixbuf = dir_icon
			elif self.path == root and root_icon:
				pixbuf = root_icon
		if not pixbuf:
			if icon:
				pixbuf = icon
			else:
				pixbuf = window.get_icon()
		pixbuf = pixbuf_helper.scale_pixbuf_to_size(pixbuf, size)
		self.get_image().set_from_pixbuf(pixbuf)

# the type of a WindowMenu from which windows can be selected
TYPE_SELECT = 0

# the type of a WindowMenu which shows options for each window in a submenu
TYPE_OPTIONS = 1

class WindowMenu(g.Menu):
	"""The menu for a list of windows."""

	def __init__(self, windows, type, icon, group_name, 
					root = None, root_icon = None, has_kill = False):
		"""Creates a new WindowMenu. type must be TYPE_SELECT or TYPE_OPTIONS.
		""" 
		g.Menu.__init__(self)
		self.group_name = group_name
		self.type = type
		self.windows = windows
		windows.sort(key=wnck.Window.get_name)
		time = g.get_current_event_time()
		self.active_window = screen.get_active_window()
		has_minimized_windows = False
		has_unminimized_windows = False
		same_app = True
		self.pids = []
		for window in windows:
			pid = window.get_application().get_pid()
			if pid in self.pids:
				continue 
			self.pids.append(pid)
		for window in windows:
			if window.is_minimized():
				has_minimized_windows = True
			else:
				has_unminimized_windows = True 
			item = WindowMenuItem(window, icon, root, root_icon)
			if type == TYPE_OPTIONS:
				item.set_submenu(create_window_action_menu(window, 
											has_kill and len(self.pids) > 1, 
											item, self))
			else:
				item.connect("scroll-event", self._scroll, window)
				item.connect("activate", self._window_selected, window, time)
			self.append(item)
		if self.type == TYPE_OPTIONS:
			self.append(g.SeparatorMenuItem())
			item = g.ImageMenuItem(_("Show all"))
			item.get_image().set_from_stock(g.STOCK_REDO, g.ICON_SIZE_MENU)
			item.connect("activate", self._restore_all)
			item.set_sensitive(has_minimized_windows)
			self.append(item)
			item = g.ImageMenuItem(_("Hide all"))
			item.get_image().set_from_stock(g.STOCK_UNDO, g.ICON_SIZE_MENU)
			item.connect("activate", self._minimize_all)
			item.set_sensitive(has_unminimized_windows)
			self.append(item)
			if has_kill:
				self.append(g.SeparatorMenuItem())
				item = g.ImageMenuItem(_("Force quit"))
				item.get_image().set_from_stock(g.STOCK_QUIT, g.ICON_SIZE_MENU)
				item.connect("activate", _kill, self.pids, group_name)
				self.append(item)
			self.append(g.SeparatorMenuItem())
			item = g.ImageMenuItem(_("Close all"))
			item.get_image().set_from_stock(g.STOCK_CLOSE, g.ICON_SIZE_MENU)
			item.connect("activate", self._close_all)
			self.append(item)

	def _minimize_all(self, menu_item):
		for window in self.windows:
			window.minimize()

	def _restore_all(self, menu_item):
		for window in self.windows:
			if window.is_minimized():
				window.unminimize(g.get_current_event_time())

	def _close_all(self, menu_item):
		n_windows = len(self.windows)
		if n_windows == 0:
			rox.info(_("%s hasn't got any open windows anymore.") 
					% self.group_name)
			return
		if not rox.confirm(_("Close all %d windows of %s?") 
							% (n_windows, self.group_name), 
				g.STOCK_CLOSE, _("Close all")):
			return
		for window in self.windows:
			window.close(g.get_current_event_time())

	def _window_selected(self, menu_item, window, time):
		window.activate(time)

	def _scroll(self, menu_item, event, window):
		if event.direction == g.gdk.SCROLL_UP:
			if window == screen.get_active_window():
				window.shade()
			else:
				window.activate(event.time)
		elif event.direction == g.gdk.SCROLL_DOWN:
			if window.is_shaded():
				window.unshade()
				window.activate(event.time)
			else:
				window.minimize()

	def _close_subdirs(self, menu_item, path):
		assert path
		path2 = os.path.expanduser(path) + '/'
		windows = []
		for window in self.windows:
			window_path = os.path.expanduser(get_filer_window_path(window))
			if window_path and window_path.startswith(path2):
				windows.append(window)
		if not windows:
			rox.info(_("There are no windows showing subdirectories of %s") % path)
		n_windows = len(windows)
		if n_windows > 1:
			if not rox.confirm(_("Close all %d subdirectories of %s?") 
							% (n_windows, path), g.STOCK_CLOSE):
				return
		for window in windows:
			window.close(g.get_current_event_time())

