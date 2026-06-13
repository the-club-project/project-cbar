import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, GLib, GtkLayerShell as GLS


class CPopup(Gtk.Window):
    def __init__(self, builder, anchor, margin=0):
        super().__init__()
        GLS.init_for_window(self)

        GLS.set_layer(self, GLS.Layer.TOP)

        GLS.set_anchor(self, GLS.Edge.TOP, True)
        GLS.set_margin(self, GLS.Edge.TOP, -2)
        
        if anchor == "center":
            GLS.set_anchor(self, GLS.Edge.LEFT, True)
            GLS.set_margin(self, GLS.Edge.LEFT, margin)
        elif anchor == "right":
            GLS.set_anchor(self, GLS.Edge.RIGHT, True)
            GLS.set_margin(self, GLS.Edge.RIGHT, margin) 
        else:
            GLS.set_anchor(self, GLS.Edge.LEFT, True)
            GLS.set_margin(self, GLS.Edge.LEFT, margin)

        self.set_app_paintable(True)
        
        self.popup_box = Gtk.Box()
        self.popup_box.set_size_request(150,1)
        self.add(self.popup_box)

        self.revealer = Gtk.Revealer()
        self.revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.revealer.set_transition_duration(200)
        self.popup_box.add(self.revealer)
        content = builder()
        self.revealer.add(content)
        self.show_all()
        GLib.timeout_add(50, self.slide_out)

    def slide_out(self):
        self.revealer.set_reveal_child(True)
        return False

    def slide_in(self):
        self.revealer.set_reveal_child(False)
        GLib.timeout_add(200, self.destroy) 