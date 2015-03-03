import os, sys, wnck, rox
from rox import g, options, applet
from rox.OptionsBox import OptionsBox

icon_theme = g.icon_theme_get_default()

class Pager(applet.Applet):
    def __init__(self, xid):
        applet.Applet.__init__(self, xid)
        rox.setup_app_options("Pager", 'Options.xml', "rox4debian.berlios.de")
        self.n_rows = options.Option("n_rows", 1)
        self.n_workspaces = options.Option("n_workspaces", 4)
        self.size = options.Option("size", 12)
        self.screen = wnck.screen_get_default()
        self.screen.force_update()
        frame = g.Frame()
        frame.set_shadow_type(g.SHADOW_IN)
        self.add(frame)
        self.pager = wnck.Pager(self.screen)
        frame.add(self.pager)
        self.pager.connect("button-press-event", self.show_menu)
        g.gdk.screen_get_default().connect("size-changed", self.options_changed)
        rox.app_options.add_notify(self.options_changed)
        rox.app_options.notify()
        self.show_all()
        
    def options_changed(self, data = None):
        if self.n_rows.has_changed:
            self.pager.set_n_rows(self.n_rows.int_value)
            
        n_screens = self.n_workspaces.int_value
        if self.n_workspaces.has_changed:
            self.screen.change_workspace_count(n_screens)
            
        screen_width = g.gdk.screen_width()
        screen_height = g.gdk.screen_height()
        
        if self.is_vertical_panel():
            self.pager.set_orientation(g.ORIENTATION_VERTICAL)
            aspect = float(screen_width) / (float(screen_height) 
                    * (float(n_screens) / float(self.n_rows.int_value) / float(self.n_rows.int_value)))
            height = (self.size.int_value*screen_height)/100
            width = int(float(height) * aspect)
        else:
            self.pager.set_orientation(g.ORIENTATION_HORIZONTAL)
            aspect = float(screen_height) / (float(screen_width) 
                    * (float(n_screens) / float(self.n_rows.int_value) / float(self.n_rows.int_value)))
            width = (self.size.int_value*screen_width)/100
            height = int(float(width) * aspect)
            
        self.set_size_request(width, height)
        rox.app_options.save()
        
    def options_show(self, data):
        rox.edit_options()
    
    def show_menu(self, widget, event):
        if event.button != 3:
            return
        menu = g.Menu()
        if self.screen.get_showing_desktop():
            item = g.ImageMenuItem(_("Show Windows"))
            item.get_image().set_from_file(os.path.join(rox.app_dir, "show_windows.png"))
        else:
            item = g.ImageMenuItem(_("Show Desktop"))
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
                pixbuf = g.gdk.pixbuf_new_from_file(os.path.join(rox.app_dir, 
                                                "show_desktop.png"))
            assert pixbuf
            item.get_image().set_from_pixbuf(pixbuf)
        item.connect("activate", self.show_desktop)
        menu.append(item)
        item = g.SeparatorMenuItem()
        menu.append(item)
        item = g.ImageMenuItem(g.STOCK_PREFERENCES)
        item.connect("activate", self.options_show)
        menu.append(item)
        item = g.ImageMenuItem(g.STOCK_QUIT)
        item.connect("activate", self.quit)
        menu.append(item)
        menu.show_all()
        menu.popup(None, None, self.position_menu, event.button, event.time)
    
    def show_desktop(self, item):
        showing_desktop = self.screen.get_showing_desktop()
        self.screen.toggle_showing_desktop(not showing_desktop)
    
    def show_window(self, item, window):
        window.activate(1)

    def quit(self, item):
        if rox.confirm(_("Are you sure you want to remove the Pager?"), g.STOCK_QUIT):
            self.destroy()
            
    
