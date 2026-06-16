import gi
import os

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")

from gi.repository import Gtk, Gdk, GLib, GtkLayerShell as GLS
from core.cmodule import CModule
from modules.clock import ClockMod



class Cbar(Gtk.Window):
    def __init__(self):
        super().__init__(title='cbar')
        
        GLS.init_for_window(self)
        GLS.set_layer(self, GLS.Layer.TOP)
        for edge in [GLS.Edge.TOP, GLS.Edge.LEFT, GLS.Edge.RIGHT]:
            GLS.set_anchor(self, edge, True)
        GLS.auto_exclusive_zone_enable(self)
        self.set_app_paintable(True)
        self.load_css()

        self.active_popup = None
        self.active_module = None

        self.phantom_box = Gtk.Box()
        self.phantom_box.get_style_context().add_class('phantom')
        self.add(self.phantom_box)

        self.overlay = Gtk.Overlay()
        self.phantom_box.pack_start(self.overlay, True, True, 0)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.main_box.set_homogeneous(True)
        self.main_box.get_style_context().add_class('cbar')
        self.overlay.add(self.main_box)

        self.drag_layer = Gtk.Fixed()
        self.overlay.add_overlay(self.drag_layer)
        self.overlay.set_overlay_pass_through(self.drag_layer, True)

        self.left_box = Gtk.Box(halign=Gtk.Align.START, spacing=10)
        self.left_box.get_style_context().add_class("left-box")
        self.center_box = Gtk.Box(halign=Gtk.Align.CENTER, spacing=10)
        self.center_box.get_style_context().add_class("center-box")
        self.right_box = Gtk.Box(halign=Gtk.Align.END, spacing=10)
        self.right_box.get_style_context().add_class("right-box")

        for box in [self.left_box, self.center_box, self.right_box]:
            box.get_style_context().add_class("boxes")
            self.main_box.pack_start(box, True, True, 10)

        self.test1 = ClockMod(self)
        self.right_box.pack_start(self.test1, False, False, 0)

        self.test2 = CModule(self)
        self.test2.update_label(label='battery')
        self.right_box.pack_start(self.test2, False, False, 0)

        self.test = CModule(self)
        self.test.update_label(label='cbar')
        self.right_box.pack_start(self.test, False, False, 0)

        self.test3 = CModule(self)
        self.test3.update_label(label='hyprland')
        self.center_box.pack_start(self.test3, False, False, 0)

        self.test4 = CModule(self)
        self.test4.update_label(label='user')
        self.left_box.pack_start(self.test4, False, False, 0)

        self.show_all()

    def load_css(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.css")
        if os.path.exists(path):
            provider = Gtk.CssProvider()
            provider.load_from_path(path)
            Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        else:
            print(f"No {path} exists")

    def close_popup(self):
        if self.active_popup:
            self.active_popup.slide_in()
            self.active_popup = None
            self.active_module = None

if __name__ == "__main__":
    win = Cbar()
    Gtk.main()