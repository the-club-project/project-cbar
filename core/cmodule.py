import gi
import math

gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')

from gi.repository import Gtk, Gdk, GLib, GtkLayerShell as GLS
from core.cpopup import CPopup

class CModule(Gtk.EventBox):
    def __init__(self, root = "", module_name = "", css_class = ""):
        super().__init__()
        self.cbar = root
        self.module_name = module_name
        self.get_style_context().add_class('cmodule')
        self.get_style_context().add_class(css_class)
        self.afterimage = None
        self.drag_threshold = 5
        self.label = Gtk.Label()
        self.add(self.label)
        self.builder = self.build_popup

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

    def build_popup(self):
        popup_w, popup_h = 250, -1
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        content.get_style_context().add_class("popup-box")
        content.set_size_request(popup_w, popup_h)
        title = Gtk.Label(label=f"Settings")
        content.pack_start(title, False, False, 0)
        for label in ["Action 1", "Close"]:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", lambda w: self.cbar.close_popup())
            content.pack_start(btn, False, False, 0)
        return content

    def update_label(self, label):
        self.label.set_text(label)

    def on_button_press(self, widget, event):
        if event.button == 1:
            self.is_pressed = True
            self.start_x = event.x
            self.start_y = event.y
        return True

    def on_motion_notify(self, widget, event):
        if not self.is_pressed: return False
        if not self.is_dragged:
            distance = math.hypot(event.x - self.start_x, event.y - self.start_y)
            if distance > self.drag_threshold:
                self.is_dragged = True
                self.set_opacity(0)
                self.cbar.close_popup()
                for box in [self.cbar.left_box, self.cbar.center_box, self.cbar.right_box]:
                    box.get_style_context().add_class('module-highlight')
                self.afterimage = Gtk.EventBox()
                self.afterimage_text = Gtk.Label(f'{self.label.get_label()}')
                self.afterimage.add(self.afterimage_text)
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
        if event.button != 1 or not self.is_pressed: return False
        self.is_pressed = False
        self.set_opacity(1.0)
        if not self.is_dragged:
            if self.cbar.active_module == self:
                self.cbar.close_popup()
            else:
                self.cbar.close_popup()
                coordinates = self.translate_coordinates(self.cbar, 0, 0)
                abs_x = coordinates[0] if coordinates else 0
                mod_w = self.get_allocated_width()
                win_w = self.cbar.get_allocated_width()
                popup_w = 250
                if self.get_parent() == self.cbar.center_box:
                    anchor = "center"
                    margin = abs_x + (mod_w / 2) - (popup_w / 2)
                elif (abs_x + popup_w) <= win_w:
                    anchor = "left"
                    margin = abs_x
                else:
                    anchor = "right"
                    margin = (win_w - (abs_x + mod_w))

                new_popup = CPopup(builder=self.builder, anchor=anchor, margin=margin)

                self.cbar.active_popup = new_popup
                self.cbar.active_module = self
            return True

        self.is_dragged = False
        for box in [self.cbar.left_box, self.cbar.center_box, self.cbar.right_box]:
            box.get_style_context().remove_class('module-highlight')
        if self.afterimage:
            self.afterimage.destroy()
            self.afterimage = None
        coordinates = self.translate_coordinates(self.cbar.phantom_box, event.x, event.y)
        if not coordinates: return True
        win_x, _ = coordinates
        win_w = self.cbar.get_allocated_width()
        third = win_w / 3
        if win_x < third:
            target = self.cbar.left_box
        elif win_x > (third * 2):
            target = self.cbar.right_box
        else:
            target = self.cbar.center_box
        children = target.get_children()
        new_idx = len(children)
        for i, child in enumerate(children):
            if child == self:
                continue
            child_mid = child.translate_coordinates(self.cbar.phantom_box, 0, 0)[0] + (child.get_allocated_width() / 2)
            if win_x < child_mid:
                new_idx = i
                break
        if target != self.get_parent():
            self.get_parent().remove(self)
            target.pack_start(self, False, 0, 0)
            target.reorder_child(self, new_idx)
        else:
            target.reorder_child(self, new_idx)
        self.show_all()
        return True