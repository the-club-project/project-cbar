import gi
import math

gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')

from gi.repository import Gtk, Gdk, GLib, GtkLayerShell as GLS


class CModule(Gtk.EventBox):
    def __init__(self, root):
        super().__init__()
        self.cbar = root
        self.afterimage = None
        self.drag_threshold = 5
        self.label = None

        # States
        self.is_pressed = False
        self.is_dragged = False

        # Dragging Calculations
        self.start_x = 0
        self.start_y = 0

        # Events
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.BUTTON1_MOTION_MASK )
        self.connect('button-press-event', self.on_button_press)
        self.connect('button-release-event', self.on_button_release)
        self.connect('motion-notify-event', self.on_motion_notify)

    def on_button_press(self, widget, event):
        print('button is Pressed')
        if event.button == 1:
            self.is_pressed = True
            self.start_x = event.x
            self.start_y = event.y
        return True

    def on_motion_notify(self, widget, event):
        print('button is Dragged')
        if not self.is_pressed: return False
        if not self.is_dragged:
            distance = math.hypot(event.x - self.start_x, event.y - self.start_y)
            if distance > self.drag_threshold:
                self.is_dragged = True
                self.afterimage = Gtk.EventBox()
                coordinates = self.translate_coordinates(self.cbar.phantom_box, 0, 0)
                if coordinates:
                    mod_x, mod_y = coordinates
                    self.cbar.drag_layer.put(self.afterimage, mod_x, mod_y)
                    self.afterimage.show_all()
            return True
        if self.afterimage:
            coordinates = self.translate_coordinates(self.cbar.phantom_box, event.x, event.y)
            if coordinates:
                win_x, win_y = coordinates
                new_x = win_x - self.start_x
                mod_coordinates = self.translate_coordinates(self.cbar.phantom_box, 0, 0)
                if mod_coordinates:
                    _, mod_y = mod_coordinates
                    self.cbar.drag_layer.move(self.afterimage, new_x, mod_y)
        return True

    def on_button_release(self, widget, event):
        pass