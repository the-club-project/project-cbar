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
        self.true_year = now.year
        self.true_month = now.month - 1
        self.last_valid_day = now.day
        
        self.is_rolling_back = False

        self.calendar_month = Gtk.Label(label=f"{now.strftime('%B %Y')}")
        self.calendar_month.set_halign(Gtk.Align.START)
        self.calendar_month.get_style_context().add_class('calendar-header')
        content.pack_start(self.calendar_month, False, False, 0)

        calendar = Gtk.Calendar()
        calendar.set_property("show-heading", False)
        calendar.get_style_context().add_class('calendar')
        
        calendar.connect("day-selected", self.on_day_selected)
        content.pack_start(calendar, True, True, 0)

        notes_today = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing = 2)
        notes_today.get_style_context().add_class('notes-box')
        content.pack_start(notes_today, True, True, 0)

        notes_title = Gtk.Label(label="Notes for Today:")
        notes_title.get_style_context().add_class('notes-header')
        notes_title.set_halign(Gtk.Align.START)
        notes_today.pack_start(notes_title, True, True, 0)

        notes = Gtk.Label(label="Aut inveniam viam aut faciam!")
        notes.get_style_context().add_class('notes')
        notes_today.pack_start(notes, True, True, 0)

        return content

    def on_day_selected(self, calendar):
        if self.is_rolling_back:
            return

        year, month, day = calendar.get_date()
        
        if year != self.true_year or month != self.true_month:
            self.is_rolling_back = True
            calendar.select_month(self.true_month, self.true_year)
            calendar.select_day(self.last_valid_day)
            self.is_rolling_back = False
        else:
            self.last_valid_day = day



