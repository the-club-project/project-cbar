import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from core.cmodule import CModule

class BatteryMod(CModule):
    def __init__(self, root):
        super().__init__(root, module_name = "battery", css_class = "battery-mod")
        self.percent_registry = {0:"󰂎", 1:"󰁺", 2:"󰁻", 3:"󰁼", 4:"󰁽", 5:"󰁾", 6:"󰁿", 7:"󰂀", 8:"󰂁", 9:"󰂂", 10:"󰁹"}
        self.status_registry = {"F":"Full", "C":"Charging", "D":"Discharging", "N":"AC POWERED!"}
        self.battery_data = {}
        self.battery_health = 0
        self.watts = 0
        self.icon = None

        self.popup_icon = None
        self.popup_percent = None
        self.popup_status = None
        self.popup_watts = None 
        self.popup_battery_health = None

        self.update_label("󰂃 0%")

    def compute_battery_health(self, full, design):
        health = (int(full) * 100) / int(design)
        return health

    def update_from_clio(self, data):
        self.battery_data = data['battery']
        bat_percent = self.battery_data['percent']
        bat_status = self.battery_data['stats']
        self.battery_health  = self.compute_battery_health(self.battery_data['energy_full'], self.battery_data['energy_full_design'])
        self.watts = int(self.battery_data['power_now']) / 1_000_000
        self.icon = "󰂄" if bat_status == "C" else self.percent_registry[int(bat_percent / 10)]
        self.update_label(f"{self.icon} {bat_percent}%")

        if self.popup_icon and self.popup_percent and self.popup_status and self.popup_battery_health and self.popup_watts:
            self.popup_icon.set_text(f"{self.icon}")
            self.popup_percent.set_text(f"{bat_percent}%")
            self.popup_status.set_text(f"Status: {self.status_registry[bat_status]}")
            self.popup_battery_health.set_text(f"Battery Health: {self.battery_health:.2f} %")
            self.popup_watts.set_text(f"Power Rate: {self.watts:.2f} W")
        return False
    
    def build_popup(self):
        popup_w, popup_h = 225, -1
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        content.get_style_context().add_class("popup-box")
        content.set_size_request(popup_w, popup_h)
        
        top_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing= 5)
        top_content.set_halign(Gtk.Align.CENTER)
        content.pack_start(top_content, False, False, 0)

        self.popup_icon = Gtk.Label(label=f"{self.icon}")
        self.popup_icon.get_style_context().add_class('battery-icon')
        top_content.pack_start(self.popup_icon, False, False, 0)

        self.popup_percent = Gtk.Label(label=f"{self.battery_data['percent']}%")
        self.popup_percent.get_style_context().add_class('battery-percent')
        top_content.pack_start(self.popup_percent, False, False, 0)

        popup_info = Gtk.Label(label=" Battery Information")
        popup_info.get_style_context().add_class('battery-info')
        content.pack_start(popup_info, False, False, 0)

        self.popup_status = Gtk.Label(label=f"Status: {self.status_registry[self.battery_data["stats"]]}")
        self.popup_status.get_style_context().add_class('battery-stats')
        content.pack_start(self.popup_status, False, False, 0)

        self.popup_watts = Gtk.Label(label=f"Power Rate: {self.watts:.2f} W")
        self.popup_watts.get_style_context().add_class('battery-watts')
        content.pack_start(self.popup_watts, False, False, 0)

        self.popup_battery_health = Gtk.Label(label=f"Battery Health: {self.battery_health:.2f} %")
        self.popup_battery_health.get_style_context().add_class('battery-health')
        content.pack_start(self.popup_battery_health, False, False, 0)

        return content