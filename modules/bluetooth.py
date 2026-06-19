import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from core.cmodule import CModule
from core.clio import send_cmd


class BluetoothMod(CModule):
    def __init__(self, root):
        super().__init__(root=root, module_name='bluetooth', css_class='bluetooth-mod')
        self.update_label('Bluetooth')

    def build_popup(self):
        popup_w, popup_h = 225, -1
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        content.get_style_context().add_class("popup-box")
        content.set_size_request(popup_w, popup_h)

        button = Gtk.Button(label="Send")
        button.connect("clicked", self.send_command)
        content.pack_start(button, False, False, 0)
        return content
    

    def send_command(self, _):
        print("Button is clicked")
        reply = send_cmd({"msg":"ILOVEYOUUU BABII"})
        print(reply)