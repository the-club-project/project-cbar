import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from core.cmodule import CModule


class BluetoothMod(CModule):
    def __init__(self, root):
        super().__init__(root=root, module_name='bluetooth', css_class='bluetooth-mod')

    def build_popup(self):
        popup_w, popup_h = 225, -1
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        content.get_style_context().add_class("popup-box")
        content.set_size_request(popup_w, popup_h)
        
        return content