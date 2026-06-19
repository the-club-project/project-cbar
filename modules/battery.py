import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from core.cmodule import CModule

class BatteryMod(CModule):
    def __init__(self, root):
        super().__init__(root, module_name = "battery", css_class = "battery-mod")
        self.percent_registry = {0:"󰂎", 1:"󰁺", 2:"󰁻", 3:"󰁼", 4:"󰁽", 5:"󰁾", 6:"󰁿", 7:"󰂀", 8:"󰂁", 9:"󰂂", 10:"󰁹"}
        self.status_registry = {"F":"Full", "C":"Charging", "D":"Discharging", "N":"AC Powered", "L": "Low Battery"}
        self.battery_data = {}
        self.battery_health = 0
        self.watts = 0
        self.icon = None

        self.popup_icon = Gtk.Label()
        self.popup_icon.get_style_context().add_class('battery-icon')

        self.popup_percent = Gtk.Label()
        self.popup_percent.get_style_context().add_class('battery-percent')

        self.popup_status = Gtk.Label()
        self.popup_status.get_style_context().add_class('battery-stats')

        self.popup_watts = Gtk.Label()
        self.popup_watts.get_style_context().add_class('battery-watts')

        self.popup_battery_health = Gtk.Label()
        self.popup_battery_health.get_style_context().add_class('battery-health')
    
        self.popup_time = Gtk.Label()
        self.popup_time.get_style_context().add_class('battery-time')

        self.update_label("󰂃 ?%")

    def compute_battery_health(self, full, design):
        health = (int(full) * 100) / int(design)
        return health
    
    def compute_time(self, power, energy_full, energy_now, state):
        watts = int(power) / 1_000_000
        energyWH = int(energy_now) / 1_000_000
        energyFWH = int(energy_full) / 1_000_000

        if state in ["D", "L"] and watts > 0:
            time_hour = energyWH / watts
            hour = int(time_hour)
            minute = int((time_hour - hour) * 60)
            return f"Time Left: {hour}h {minute}m"
        elif state == "C" and watts > 0:
            time_hour = (energyFWH - energyWH) / watts
            hour = int(time_hour)
            minute = int((time_hour - hour) * 60)
            return f"Time to Full: {hour}h {minute}m"
        elif state == "F":
            return "Battery Fully Charged"
        else:
            return "Plugged In"

    def update_from_clio(self, data):
        self.battery_data = data['battery']
        bat_percent = self.battery_data['percent']
        bat_status = self.battery_data['stats']
        self.battery_health  = self.compute_battery_health(self.battery_data['energy_full'], self.battery_data['energy_full_design'])
        self.watts = int(self.battery_data['power_now']) / 1_000_000
        self.icon = "󰂄" if bat_status == "C" else self.percent_registry[int(bat_percent / 10)]
        self.update_label(f"{self.icon} {bat_percent}%")

        context = self.get_style_context()
        context_icon = self.popup_icon.get_style_context()
        context_percent = self.popup_percent.get_style_context()
        states = {"F":"state-full", "C":"state-charging", "D":"state-dis", "N":"state-ac", "L":"state-low"}

        for cls in states.values():
            context.remove_class(cls)
            context_icon.remove_class(cls)
            context_percent.remove_class(cls)

        if bat_status == "D" and int(bat_percent) <= 20:
            bat_status = "L"

        active_cls = states[bat_status]
        if active_cls:
            context.add_class(active_cls)
            context_percent.add_class(active_cls)
            context_icon.add_class(active_cls)
        
        self.popup_icon.set_text(f"{self.icon}")
        self.popup_percent.set_text(f"{bat_percent}%")
        self.popup_status.set_text(f"Status: {self.status_registry[bat_status]}")
        self.popup_battery_health.set_text(f"Battery Health: {self.battery_health:.2f} %")
        self.popup_watts.set_text(f"Power Rate: {self.watts:.2f} W")
        self.popup_time.set_text(self.compute_time(power=self.battery_data['power_now'], energy_full=self.battery_data['energy_full_design'], 
                                                   energy_now=self.battery_data['energy_now'], state=bat_status))
        return False
    
    def build_popup(self):
        popup_w, popup_h = 225, -1
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        content.get_style_context().add_class("popup-box")
        content.set_size_request(popup_w, popup_h)
        
        top_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing= 5)
        top_content.set_halign(Gtk.Align.CENTER)
        content.pack_start(top_content, False, False, 0)

        self.popup_icon.set_text(f"{self.icon}")
        top_content.pack_start(self.popup_icon, False, False, 0)

        self.popup_percent.set_text(f"{self.battery_data['percent']}%")
        top_content.pack_start(self.popup_percent, False, False, 0)

        popup_info = Gtk.Label(label=" Battery Information")
        popup_info.get_style_context().add_class('battery-info')
        content.pack_start(popup_info, False, False, 0)

        self.popup_status.set_text(f"Status: {self.status_registry[self.battery_data["stats"]]}")
        content.pack_start(self.popup_status, False, False, 0)

        self.popup_watts.set_text(f"Power Rate: {self.watts:.2f} W")
        content.pack_start(self.popup_watts, False, False, 0)

        self.popup_battery_health.set_text(f"Battery Health: {self.battery_health:.2f} %")
        content.pack_start(self.popup_battery_health, False, False, 0)

        self.popup_time.set_text(self.compute_time(self.battery_data['power_now'], self.battery_data['energy_full_design'], self.battery_data['energy_now'], self.battery_data['stats']))
        content.pack_start(self.popup_time, False, False, 0)

        return content