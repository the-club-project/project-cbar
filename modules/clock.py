import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib
from core.cmodule import CModule
from datetime import datetime

class ClockMod(CModule):
    def __init__(self, root):
        super().__init__(root=root, module_name='clock', css_class='clock-mod')
        self.tick()
        GLib.timeout_add(1000, self.tick)

    def tick(self):
        curr = datetime.now()
        self.update_label(f" {curr.strftime('%I:%M %p')}")
        return True

    def build_popup(self):
        popup_w, popup_h = 250, -1
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        content.get_style_context().add_class("popup-box")
        content.set_size_request(popup_w, popup_h)

        now = datetime.now()
        calendar_month = Gtk.Label(label=f"{now.strftime('%B %Y')}")
        calendar_month.set_halign(Gtk.Align.START)
        calendar_month.get_style_context().add_class('calendar-header')
        content.pack_start(calendar_month, False, False, 0)

        calendar = Gtk.Calendar()
        calendar.set_property("show-heading", False)
        calendar.get_style_context().add_class('calendar')
        content.pack_start(calendar, True, True, 0)


        return content



