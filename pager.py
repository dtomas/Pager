import os

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gtk, Gdk, GdkPixbuf

import rox
from rox import options, applet

icon_theme = Gtk.IconTheme.get_default()


class WnckPager(Wnck.Pager):
    width = 1
    height = 1

    def do_get_preferred_width(self):
        return 1, self.width

    def do_get_preferred_height(self):
        return 1, self.height


class Pager:
    def __init__(self):
        rox.setup_app_options("Pager", 'Options.xml', "dtomas")
        self.n_rows = options.Option("n_rows", 1)
        self.n_workspaces = options.Option("n_workspaces", 4)
        self.size = options.Option("size", 12)
        self.screen = Wnck.Screen.get_default()
        self.screen.force_update()
        self.pager = WnckPager()
        self.pager.set_size_request(1, 1)
        self.add(self.pager)
        self.pager.connect("button-press-event", self.show_menu)
        Gdk.Screen.get_default().connect("size-changed", self.options_changed)
        rox.app_options.add_notify(self.options_changed)
        rox.app_options.notify()
        self.show_all()

    def options_changed(self, data=None):
        if self.n_rows.has_changed:
            self.pager.set_n_rows(self.n_rows.int_value)

        n_screens = self.n_workspaces.int_value
        if self.n_workspaces.has_changed:
            self.screen.change_workspace_count(n_screens)

        screen_width = Gdk.Screen.width()
        screen_height = Gdk.Screen.height()

        if self.is_vertical_panel():
            self.pager.set_orientation(Gtk.Orientation.VERTICAL)
            aspect = float(screen_width) / (
                float(screen_height) * (
                    float(n_screens) / float(self.n_rows.int_value) / float(self.n_rows.int_value)
                )
            )
            height = (self.size.int_value * screen_height) // 100
            width = int(float(height) * aspect)
            self.pager.height = height
            self.pager.width = width
        else:
            self.pager.set_orientation(Gtk.Orientation.HORIZONTAL)
            aspect = float(screen_height) / (
                float(screen_width) * (
                    float(n_screens) / float(self.n_rows.int_value) / float(self.n_rows.int_value)
                )
            )
            width = (self.size.int_value * screen_width) // 100
            height = int(float(width) * aspect)
            self.pager.width = width
            self.pager.height = height

        self.pager.set_size_request(width, height)
        self.set_size_request(width, height)
        rox.app_options.save()

    def options_show(self, data):
        rox.edit_options()

    def show_menu(self, widget, event):
        if event.button != 3:
            return
        self.menu = Gtk.Menu.new()
        if self.screen.get_showing_desktop():
            item = Gtk.ImageMenuItem(_("Show Windows"))
            item.set_image(
                Gtk.Image.new_from_file(
                    os.path.join(rox.app_dir, "show_windows.png")
                )
            )
        else:
            item = Gtk.ImageMenuItem(_("Show Desktop"))
            pixbuf = None
            try:
                pixbuf = icon_theme.load_icon("desktop", 16)
            except:
                pass
            if not pixbuf:
                try:
                    pixbuf = icon_theme.load_icon("gnome-fs-desktop", 16)
                except:
                    pass
            if not pixbuf:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(
                    os.path.join(rox.app_dir, "show_desktop.png")
                )
            assert pixbuf
            item.set_image(Gtk.Image.new_from_pixbuf(pixbuf))
        item.connect("activate", self.show_desktop)
        self.menu.append(item)
        item = Gtk.SeparatorMenuItem()
        self.menu.append(item)
        item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_PREFERENCES, None)
        item.connect("activate", self.options_show)
        self.menu.append(item)
        item = Gtk.ImageMenuItem.new_from_stock(Gtk.STOCK_QUIT, None)
        item.connect("activate", self.quit)
        self.menu.append(item)
        self.menu.show_all()
        self.menu.popup(None, None, self.position_menu, None, event.button, event.time)

    def show_desktop(self, item):
        showing_desktop = self.screen.get_showing_desktop()
        self.screen.toggle_showing_desktop(not showing_desktop)

    def show_window(self, item, window):
        window.activate(1)

    def quit(self, item):
        if rox.confirm(_("Are you sure you want to remove the Pager?"), Gtk.STOCK_QUIT):
            self.destroy()


class PagerApplet(applet.Applet, Pager):

    def __init__(self, xid):
        applet.Applet.__init__(self, xid)
        Pager.__init__(self)
        orientation, __ = self.get_panel_menu_pos()
        self.__vertical = orientation in ('Left', 'Right')
        if self.__vertical:
            self.set_size_request(8, -1)
        else:
            self.set_size_request(-1, 8)


class PagerWindow(rox.Window, Pager):

    def __init__(self):
        rox.Window.__init__(self)
        Pager.__init__(self)
        self.set_size_request(-1, -1)

    def is_vertical_panel(self):
        return False

    def position_menu(self, menu, x, y, data):
        return x, y, False
