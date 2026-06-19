import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
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

        title = Gtk.Label(label="Bluetooth", halign=Gtk.Align.START)
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
        self.button.connect("clicked", self.send_command)
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
        print(self.bluetooth_data)
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

    def send_command(self, _):
        print("Button is clicked")
        reply = send_cmd({"msg":"ILOVEYOUUU BABII"})
        print(reply)