import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib, Gdk
from core.cmodule import CModule
from core.clio import send_cmd


class BluetoothMod(CModule):
    def __init__(self, root):
        super().__init__(root=root, module_name='bluetooth', css_class='bluetooth-mod')
        self.bluetooth_data = {}
        self.states = ["on-bt", "off-bt", "connected-bt"]
        self.update_label("󰂯")
        self.device_list = None
        self.scroll_area = None
        self.button = None
        self.note = None
        self.powered = False

    def build_popup(self):
        popup_w, popup_h = 250, -1
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        content.get_style_context().add_class("popup-box")
        content.set_size_request(popup_w, popup_h)

        title = Gtk.Label(label="󰂯 Bluetooth", halign=Gtk.Align.START)
        title.get_style_context().add_class("title")

        switch = Gtk.Switch()
        switch.set_active(self.bluetooth_data['powered'])
        switch.get_style_context().add_class("switch")
        switch.connect("notify::active", self.switch_flipped)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        header.pack_start(title, True, True, 0)
        header.pack_start(switch, False, False, 0)
        content.pack_start(header, False, False, 0)

        self.note = Gtk.Label(label="Turn On Bluetooth for devices", halign=Gtk.Align.CENTER)
        self.note.get_style_context().add_class("note")
        content.pack_start(self.note, False, False, 0)

        self.device_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.scroll_area = Gtk.ScrolledWindow()
        self.scroll_area.set_size_request(-1, 180)
        self.scroll_area.add(self.device_list)

        self.button = Gtk.Button(label="Scan", halign=Gtk.Align.CENTER)
        self.button.connect("clicked", self.scan_devices)
        self.button.get_style_context().add_class("scan-button")


        content.pack_start(self.scroll_area, True, True, 0)
        content.pack_start(self.button, False, False, 0)
        
        self.popup_show_n_hide(False)
        return content
    
    def switch_flipped(self, switch, _):
        is_active = switch.get_active()
        if is_active:
            reply = send_cmd({"sender":self.module_name, "action":"power", "value":"on"})
        else:
            reply = send_cmd({"sender":self.module_name, "action":"power", "value":"off"})
    
    def update_from_clio(self, data):
        cls = ""
        out = ""
        self.bluetooth_data = data['bluetooth']
        self.powered = self.bluetooth_data['powered']
        if self.bluetooth_data['powered'] and not self.bluetooth_data['connected']:
            cls = "on-bt"
            out = "On"
        elif self.bluetooth_data['powered'] and self.bluetooth_data['connected']:
            cls = "connected-bt"
            out = self.bluetooth_data['device_name']
        else:
            cls = "off-bt"
            out = "Off"
        context = self.label.get_style_context()
        for cs in self.states:
            context.remove_class(cs)
        
        if cls:
            context.add_class(cls)
        
        self.update_label(f"󰂯 {out}")
        self.popup_show_n_hide(True)

        if self.device_list is not None:
            scan_device = self.bluetooth_data['scan_results']
            current = self.device_list.get_children()
            num_devices = len(scan_device) if self.powered else 0

            for id, item in enumerate(scan_device):
                if item['name'] == self.bluetooth_data['device_name']:
                    connected = scan_device.pop(id)
                    scan_device.insert(0, connected)

            for i in range(max(len(current), num_devices)):
                if i < num_devices:
                    device = scan_device[i]
                    dev_name = device["name"]
                    dev_mac = device["mac"]
                    dev_connected = device["is_connected"]

                    if i < len(current):
                        btn = current[i]
                        btn.disconnect_by_func(self.pop_menu)

                        btn.connect("button-press-event", self.pop_menu, dev_name, dev_mac, dev_connected)
                        box = btn.get_child()
                        label = box.get_children()

                        label[0].set_text(dev_name)
                        if dev_connected:
                            label[1].set_text(f"Connected")
                            label[0].get_style_context().add_class("device-connected")
                            label[1].get_style_context().add_class("device-connected")
                        else:
                            label[1].set_text(f"MAC: {dev_mac}")
                            label[0].get_style_context().remove_class("device-connected")
                            label[1].get_style_context().remove_class("device-connected")
                        btn.show()
                    else:
                        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                        dev = Gtk.Label(label=f"{device["name"]}", halign=Gtk.Align.START)
                        dev.get_style_context().add_class("device-name")
                        if dev_connected:
                            mac = Gtk.Label(label=f"Connected", halign=Gtk.Align.START)
                            mac.get_style_context().add_class("device-mac")
                            dev.get_style_context().add_class("device-connected")
                            mac.get_style_context().add_class("device-connected")
                        else:
                            mac = Gtk.Label(label=f"MAC: {device["mac"]}", halign=Gtk.Align.START)
                            mac.get_style_context().add_class("device-mac")
                            dev.get_style_context().remove_class("device-connected")
                            mac.get_style_context().remove_class("device-connected")
                        box.pack_start(dev, False, False, 0)
                        box.pack_start(mac, False, False, 0)

                        button = Gtk.Button()
                        button.add(box)
                        button.get_style_context().add_class("device-button")
                        button.connect("button-press-event", self.pop_menu, dev_name, dev_mac, dev_connected)

                        self.device_list.pack_start(button, False, False, 0)
                        button.show_all()
                else:
                    if i < len(current):
                        current[i].hide()
        
        return False
    
    def popup_show_n_hide(self, conf):
        if self.scroll_area and self.button and self.note:
            if self.powered and not conf:
                self.scroll_area.hide()
                self.button.hide()
                self.note.hide()
            elif self.powered and conf:
                self.scroll_area.show()
                self.button.show()
                self.note.hide()
            else:
                self.scroll_area.hide()
                self.button.hide()
                self.note.show()

    def scan_devices(self, button):
        button.set_sensitive(False)
        button.set_label("Scanning...")
        button.get_style_context().add_class("active-button")
        reply = send_cmd({"sender":self.module_name, "action":"scan"})
        GLib.timeout_add_seconds(10, self.default_scan, button)

    def connect_devices(self, _):
        reply = send_cmd({"sender":self.module_name, "action":"connect"})


    def default_scan(self, button):
        button.set_sensitive(True)
        button.set_label("Scan")
        button.get_style_context().remove_class("active-button")
        return False

    def pop_menu(self, button, event, name , mac, connected):
        if event.button == 3:
            width = button.get_allocated_width()
            context_menu = self.create_pop_menu(name, mac, connected)
            context_menu.set_size_request(width/2, -1)
            context_menu.popup_at_widget(button, Gdk.Gravity.SOUTH_EAST, Gdk.Gravity.NORTH_EAST, event)
            return True
        return False

    def create_pop_menu(self, name, mac, connected):
        menu = Gtk.Menu()
        if connected:
            connect = Gtk.MenuItem(label="Disconnect")
            connect.connect('activate', lambda _: send_cmd({"sender":self.module_name, "action":"disconnect", "mac": mac}))
        else:
            connect = Gtk.MenuItem(label="Connect")
            connect.connect('activate', lambda _: send_cmd({"sender":self.module_name, "action":"connect", "mac": mac}))
        menu.append(connect)

        forget = Gtk.MenuItem(label="Forget")
        forget.connect('activate', lambda _: send_cmd({"sender":self.module_name, "action":"forget", "mac": mac}))
        menu.append(forget)

        menu.show_all()
        return menu