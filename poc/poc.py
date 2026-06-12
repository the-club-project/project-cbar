import gi
import os
import math
import subprocess
import json
import lupa
from lupa import LuaRuntime

gi.require_version('Gtk', "3.0")
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell as GLS, Gio

# Global reference tracker to allow the GIO socket listener to refresh the active layout panel smoothly
active_layout_panel = None

# Initialize the standalone Lua runtime engine inside your Python context
lua = LuaRuntime(unpack_returned_tuples=False)

# Compile the workspace switching layout string safely inside Lua
lua.execute('''
    function make_workspace_cmd(ws_id)
        return "hl.dsp.focus({ workspace = " .. ws_id .. " })"
    end
''')

# Map Lua globals back to native Python function pointers
lua_workspace_formatter = lua.globals().make_workspace_cmd


# --- Workspace Layout Panel Widget ---
class WorkspaceLayoutWidget(Gtk.Box):
    def __init__(self, cbar_root):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.cbar_root = cbar_root
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.refresh_layout()

    def refresh_layout(self):
        for child in self.get_children():
            self.remove(child)
        
        # Loop through workspaces limited strictly up to W5
        for i in range(1, 6):
            card = Gtk.EventBox()
            card.get_style_context().add_class("workspace-card")
            card.set_size_request(110, 80)
            
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            
            screen_container = Gtk.EventBox()
            screen_area = Gtk.Fixed()
            screen_area.set_size_request(90, 50)
            screen_area.get_style_context().add_class("mini-screen")
            screen_container.add(screen_area)
            
            clients = self.cbar_root.get_workspace_layout(i)
            scale = 0.045
            
            for win in clients:
                # Static client bounding box representations (No Dragging)
                rect = Gtk.EventBox()
                rect.get_style_context().add_class("mini-window")
                
                w = max(16, int(win['size'][0] * scale))
                h = max(16, int(win['size'][1] * scale))
                rect.set_size_request(w, h)
                
                icon = Gtk.Image.new_from_icon_name(win['class'].lower(), Gtk.IconSize.MENU)
                rect.add(icon)
                
                x = max(0, int(win['at'][0] * scale))
                y = max(0, int(win['at'][1] * scale))
                screen_area.put(rect, x, y)
            
            label = Gtk.Label(label=f"W{i}")
            label.get_style_context().add_class("workspace-label")
            
            vbox.pack_start(screen_container, True, True, 0)
            vbox.pack_start(label, False, False, 0)
            
            card.add(vbox)
            
            # Left-clicks run workspace shift path cleanly
            card.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            card.connect("button-press-event", lambda w, ev, id=i: self.on_card_clicked(ev, id))
            screen_container.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            screen_container.connect("button-press-event", lambda w, ev, id=i: self.on_card_clicked(ev, id))
            
            self.pack_start(card, False, False, 0)
            
        self.show_all()

    def on_card_clicked(self, event, ws_id):
        if event.button == 1:
            self.cbar_root.switch_workspace(ws_id)
            return True
        return False


# --- ModulePopup ---
class ModulePopup(Gtk.Window):
    def __init__(self, content_widget, anchor_type="left", x_margin=0):
        super().__init__()
        GLS.init_for_window(self)
        GLS.set_layer(self, GLS.Layer.TOP)
        if anchor_type != "absolute_center":
            GLS.set_anchor(self, GLS.Edge.TOP, True)
            GLS.set_margin(self, GLS.Edge.TOP, -10)
            if anchor_type == "right":
                GLS.set_anchor(self, GLS.Edge.RIGHT, True)
                GLS.set_margin(self, GLS.Edge.RIGHT, x_margin)
            else:
                GLS.set_anchor(self, GLS.Edge.LEFT, True)
                GLS.set_margin(self, GLS.Edge.LEFT, x_margin)
        self.set_app_paintable(True)
        self.set_name("popup-window")
        self.popup_box = Gtk.Box()
        self.popup_box.set_size_request(150, 1)
        self.add(self.popup_box)
        self.revealer = Gtk.Revealer()
        self.revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.revealer.set_transition_duration(200)
        self.popup_box.add(self.revealer)
        self.revealer.add(content_widget)
        self.show_all()
        GLib.timeout_add(50, self.slide_out)

    def slide_out(self):
        self.revealer.set_reveal_child(True)
        return False

    def slide_in(self):
        global active_layout_panel
        active_layout_panel = None  
        self.revealer.set_reveal_child(False)
        GLib.timeout_add(200, self.destroy)


# --- CbarModule ---
class CbarModule(Gtk.EventBox):
    def __init__(self, text, css_class, cbar_root):
        super().__init__()
        self.text = text
        self.css_class = css_class
        self.cbar_root = cbar_root
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.BUTTON1_MOTION_MASK)
        self.label = Gtk.Label(label=f" {text} ")
        self.add(self.label)
        style_context = self.get_style_context()
        style_context.add_class("cbar-module")
        style_context.add_class(css_class)
        self.is_pressed = False
        self.is_dragging = False
        self.press_x = 0
        self.press_y = 0
        self.ghost = None
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion_notify)

    def on_button_press(self, widget, event):
        if event.button == 1:
            self.is_pressed = True
            self.press_x = event.x
            self.press_y = event.y
            self.set_opacity(0.8)
        return True

    def on_motion_notify(self, widget, event):
        if not self.is_pressed: return False
        if not self.is_dragging:
            distance = math.hypot(event.x - self.press_x, event.y - self.press_y)
            if distance > 5:
                self.is_dragging = True
                self.set_opacity(0.0)
                self.cbar_root.close_active_popup()
                for box in [self.cbar_root.left_bar, self.cbar_root.center_bar, self.cbar_root.right_bar]:
                    box.get_style_context().add_class("highlight")
                self.ghost = Gtk.EventBox()
                self.ghost.add(Gtk.Label(label=f" {self.text} "))
                ctx = self.ghost.get_style_context()
                ctx.add_class("cbar-module")
                ctx.add_class(self.css_class)
                ctx.add_class("ghost-module")
                coords = self.translate_coordinates(self.cbar_root.bg_box, 0, 0)
                if coords:
                    mod_x, mod_y = coords
                    self.cbar_root.drag_layer.put(self.ghost, mod_x, mod_y)
                    self.ghost.show_all()
            return True
        if self.ghost:
            coords = self.translate_coordinates(self.cbar_root.bg_box, event.x, event.y)
            if coords:
                win_x, win_y = coords
                new_x = win_x - self.press_x
                mod_coords = self.translate_coordinates(self.cbar_root.bg_box, 0, 0)
                if mod_coords:
                    _, mod_y = mod_coords
                    self.cbar_root.drag_layer.move(self.ghost, new_x, mod_y)
        return True

    def on_button_release(self, widget, event):
        global active_layout_panel
        if event.button != 1 or not self.is_pressed: return False
        self.is_pressed = False
        self.set_opacity(1.0)
        if not self.is_dragging:
            if self.cbar_root.active_popup_module == self:
                self.cbar_root.close_active_popup()
            else:
                self.cbar_root.close_active_popup()
                coords = self.translate_coordinates(self.cbar_root, 0, 0)
                abs_x = coords[0] if coords else 0
                mod_w = self.get_allocated_width()
                win_w = self.cbar_root.get_allocated_width()
                
                if "mod-workspace" in self.css_class:
                    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                    content.set_size_request(620, 160)
                    content.get_style_context().add_class("workspace-popup-content")
                    
                    ws_layout = WorkspaceLayoutWidget(self.cbar_root)
                    content.pack_start(ws_layout, True, True, 0)
                    
                    active_layout_panel = ws_layout
                    
                    close_btn = Gtk.Button(label="Close")
                    close_btn.get_style_context().add_class("small-close-button")
                    close_btn.connect("clicked", lambda w: self.cbar_root.close_active_popup())
                    
                    align_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                    align_box.set_center_widget(close_btn)
                    content.pack_end(align_box, False, False, 5)
                    
                    new_popup = ModulePopup(content, "absolute_center", 0)
                else:
                    popup_w, popup_h = 250, -1
                    anchor = "left" if (abs_x + popup_w) <= win_w else "right"
                    margin = abs_x if anchor == "left" else (win_w - (abs_x + mod_w))
                    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                    content.set_size_request(popup_w, popup_h)
                    content.get_style_context().add_class("popup-content")
                    title = Gtk.Label(label=f"Settings: {self.text.strip()}")
                    title.get_style_context().add_class("popup-title")
                    content.pack_start(title, False, False, 0)
                    for label in ["Action 1", "Close"]:
                        btn = Gtk.Button(label=label)
                        btn.connect("clicked", lambda w: self.cbar_root.close_active_popup())
                        content.pack_start(btn, False, False, 0)
                    new_popup = ModulePopup(content, anchor, margin)
                
                self.cbar_root.active_popup_window = new_popup
                self.cbar_root.active_popup_module = self
            return True
            
        self.is_dragging = False
        for box in [self.cbar_root.left_bar, self.cbar_root.center_bar, self.cbar_root.right_bar]:
            box.get_style_context().remove_class("highlight")
        if self.ghost:
            self.ghost.destroy()
            self.ghost = None
        coords = self.translate_coordinates(self.cbar_root.bg_box, event.x, event.y)
        if not coords: return True
        win_x, _ = coords
        win_w = self.cbar_root.get_allocated_width()
        third = win_w / 3
        if win_x < third: target = self.cbar_root.left_bar
        elif win_x > (third * 2): target = self.cbar_root.right_bar
        else: target = self.cbar_root.center_bar
        children = target.get_children()
        new_idx = len(children)
        for i, child in enumerate(children):
            if child == self: continue
            child_mid = child.translate_coordinates(self.cbar_root.bg_box, 0, 0)[0] + (child.get_allocated_width() / 2)
            if win_x < child_mid:
                new_idx = i
                break
        if target != self.get_parent():
            self.get_parent().remove(self)
            target.pack_start(self, False, False, 0)
            target.reorder_child(self, new_idx)
        else:
            target.reorder_child(self, new_idx)
        self.show_all()
        return True


# --- Main Cbar Window Class ---
class Cbar(Gtk.Window):
    def __init__(self):
        super().__init__(title="cbar")
        GLS.init_for_window(self)
        GLS.set_layer(self, GLS.Layer.TOP)
        for edge in [GLS.Edge.TOP, GLS.Edge.LEFT, GLS.Edge.RIGHT]:
            GLS.set_anchor(self, edge, True)
        GLS.auto_exclusive_zone_enable(self)
        self.set_app_paintable(True)
        self.set_name("cbar-window")
        self.load_external_css()
        self.active_popup_window = None
        self.active_popup_module = None
        self.bg_box = Gtk.Box()
        self.bg_box.get_style_context().add_class("cbar-bg")
        self.bg_box.set_margin_start(6); self.bg_box.set_margin_end(6)
        self.bg_box.set_margin_top(6); self.bg_box.set_margin_bottom(6)
        self.add(self.bg_box)
        self.overlay = Gtk.Overlay()
        self.bg_box.pack_start(self.overlay, True, True, 0)
        self.main_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.main_bar.set_homogeneous(True)
        self.overlay.add(self.main_bar)
        
        self.drag_layer = Gtk.Fixed()
        self.overlay.add_overlay(self.drag_layer)
        self.overlay.set_overlay_pass_through(self.drag_layer, True)
        
        self.left_bar = Gtk.Box(spacing=10, halign=Gtk.Align.START)
        self.center_bar = Gtk.Box(spacing=10, halign=Gtk.Align.CENTER)
        self.right_bar = Gtk.Box(spacing=10, halign=Gtk.Align.END)
        for box in [self.left_bar, self.center_bar, self.right_bar]:
            box.get_style_context().add_class("drop-zone")
            self.main_bar.pack_start(box, True, True, 10)
        self.workspace_module = CbarModule("Workspace 1", "mod-workspace", self)
        self.modules = [self.workspace_module, CbarModule("🕒 Clock", "mod-clock", self), 
                        CbarModule("📊 CPU: 12%", "mod-cpu", self), CbarModule("🔋 Battery", "mod-battery", self)]
        self.left_bar.pack_start(self.modules[0], False, False, 0)
        self.center_bar.pack_start(self.modules[1], False, False, 0)
        self.right_bar.pack_start(self.modules[2], False, False, 0)
        self.right_bar.pack_start(self.modules[3], False, False, 0)
        
        # Bring GIO Socket listener environment mechanics back online
        self.setup_gio_listener()
        self.show_all()

    def setup_gio_listener(self):
        self.update_initial_workspace()
        sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        xdg = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
        path = f"{xdg}/hypr/{sig}/.socket2.sock"
        if not os.path.exists(path): path = f"/tmp/hypr/{sig}/.socket2.sock"
        client = Gio.SocketClient()
        address = Gio.UnixSocketAddress.new(path)
        client.connect_async(address, None, lambda c, r, d: self.on_socket_connected(c, r), None)

    def on_socket_connected(self, client, result):
        try:
            conn = client.connect_finish(result)
            stream = Gio.DataInputStream.new(conn.get_input_stream())
            def read_next():
                stream.read_line_async(GLib.PRIORITY_DEFAULT, None, lambda s, res: self.on_line(s, res, read_next))
            read_next()
        except: pass

    def on_line(self, stream, result, next_callback):
        global active_layout_panel
        try:
            line, _ = stream.read_line_finish(result)
            if line:
                line_str = line.decode('utf-8', errors='ignore')
                
                # Instantly catch active viewport movements from socket channel stream strings
                if "workspace>>" in line_str:
                    self.update_initial_workspace()
                
                # Clean event triggers catch window environment changes to update preview panels safely
                if active_layout_panel and any(ev in line_str for ev in ["openwindow>>", "closewindow>>", "movewindow>>", "focusedmon>>"]):
                    GLib.idle_add(active_layout_panel.refresh_layout)
                    
            next_callback()
        except: pass

    def get_workspace_layout(self, ws_id):
        try:
            result = subprocess.check_output(['hyprctl', 'clients', '-j'], text=True)
            clients = json.loads(result)
            return [c for c in clients if c['workspace']['id'] == ws_id]
        except: return []

    def update_initial_workspace(self):
        try:
            result = subprocess.check_output(['hyprctl', 'activeworkspace', '-j'], text=True)
            data = json.loads(result)
            GLib.idle_add(self.update_workspace_label, data.get("name"))
        except: pass

    def update_workspace_label(self, ws_name):
        self.workspace_module.label.set_text(f" 💻 Workspace {ws_name} ")

    def switch_workspace(self, id):
        # Utilizing Lua formatter generation explicitly matching your lookup syntax layout configuration
        cmd = lua_workspace_formatter(id)
        subprocess.run(["hyprctl", "dispatch", cmd])

    def close_active_popup(self):
        if self.active_popup_window:
            self.active_popup_window.slide_in()
            self.active_popup_window = None
            self.active_popup_module = None

    def load_external_css(self):
        css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
        if os.path.exists(css_file):
            provider = Gtk.CssProvider()
            provider.load_from_path(css_file)
            Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

if __name__ == "__main__":
    win = Cbar()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()