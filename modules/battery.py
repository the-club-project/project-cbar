import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from core.cmodule import CModule

class BatteryMod(CModule):
    def __init__(self, root):
        super().__init__(root, module_name = "battery", css_class = "battery-mod")
        self.percent_registry = {0:"󰂎", 1:"󰁺", 2:"󰁻", 3:"󰁼", 4:"󰁽", 5:"󰁾", 6:"󰁿", 7:"󰂀", 8:"󰂁", 9:"󰂂", 10:"󰁹"}
        self.battery_data = {}
        self.icon = None
        self.popup_icon = None
        self.popup_percent = None
        self.popup_status = None
        self.update_label("󰂃 0%")

    def update_from_clio(self, data):
        self.battery_data = data['battery']
        bat_percent = self.battery_data['percent']
        bat_status = self.battery_data['stats']
        self.icon = "󰂄" if bat_status == "C" else self.percent_registry[int(bat_percent / 10)]
        self.update_label(f"{self.icon} {bat_percent}%")

        if self.popup_icon and self.popup_percent and self.popup_status:
            self.popup_icon.set_text(f"{self.icon}")
            self.popup_percent.set_text(f"{bat_percent}%")
            self.popup_status.set_text(f"{"Charging" if bat_status == 'C' else "Discharging"}")
        return False
    
    def build_popup(self):
        popup_w, popup_h = 250, -1
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        content.get_style_context().add_class("popup-box")
        content.set_size_request(popup_w, popup_h)
        
        top_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing= 5)
        content.pack_start(top_content, True, True, 0)

        self.popup_icon = Gtk.Label(label=f"{self.icon}")
        self.popup_icon.get_style_context().add_class('battery-icon')
        top_content.pack_start(self.popup_icon, False, False, 0)

        self.popup_percent = Gtk.Label(label=f"{self.battery_data['percent']}%")
        top_content.pack_start(self.popup_percent, False, False, 0)

        self.popup_status = Gtk.Label(label=f"{"Charging" if self.battery_data['stats'] == 'C' else "Discharging"}")
        top_content.pack_start(self.popup_status, False, False, 0)

        return content
