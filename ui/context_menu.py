"""
WiFi Meter - Context Menu Module

Provides the right-click context menu for the main widget, including
theme selection, network interface switching, lock/on-top toggles,
data stats access, pause/resume, and application exit.
"""

import tkinter as tk
import logging
import psutil
from theme import Theme

logger = logging.getLogger(__name__)


class ContextMenuManager:
    """
    Manages the right-click context menu for the NetworkMonitor widget.

    Builds a cascading tkinter Menu with sub-menus for theme selection
    and network adapter selection, plus checkbuttons for lock/on-top
    state, and commands for data stats, pause, about, and exit.
    """

    def __init__(self, app):
        """
        Initialize the context menu and attach it to the parent application.

        Args:
            app (NetworkMonitor): The parent application instance, used to
                                  call back into feature methods (toggle_pause,
                                  toggle_stats, show_about, etc.).
        """
        self.app = app
        self.menu = tk.Menu(
            app, tearoff=0,
            bg=Theme.BG_COLOR, fg=Theme.TEXT_MAIN
        )

        # --- Theme Submenu ---
        self.theme_menu = tk.Menu(self.menu, tearoff=0)
        for theme_name in Theme.get_available_themes():
            display_name = f"{theme_name} (Default)" if theme_name == "Dark" else theme_name
            self.theme_menu.add_command(
                label=display_name,
                command=lambda name=theme_name: self.change_theme(name)
            )

        # --- Adapter Submenu ---
        self.adapter_menu = tk.Menu(self.menu, tearoff=0)
        self.selected_adapter_var = tk.StringVar(value="Auto")
        self.refresh_adapters()

        # --- Main Menu Items ---
        self.is_locked_var = tk.BooleanVar(value=False)
        self.is_ontop_var = tk.BooleanVar(value=True)

        self.menu.add_cascade(label="Theme", menu=self.theme_menu)
        self.menu.add_cascade(label="Network Interface", menu=self.adapter_menu)
        self.menu.add_separator()
        self.menu.add_checkbutton(
            label="Lock Position",
            command=self.toggle_lock,
            variable=self.is_locked_var
        )
        self.menu.add_checkbutton(
            label="Always On Top",
            command=self.toggle_top,
            variable=self.is_ontop_var
        )
        self.menu.add_separator()
        self.menu.add_command(label="Data Usage Stat", command=self.app.toggle_stats)
        self.menu.add_separator()
        self.menu.add_command(label="Pause/Resume", command=self.app.toggle_pause)
        self.menu.add_command(label="About", command=self.app.show_about)
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=self.app.cleanup_and_exit)

    def refresh_adapters(self):
        """
        Rebuild the network adapter sub-menu with current system interfaces.

        Clears existing entries and re-scans for Wi-Fi interfaces. Adds
        each found Wi-Fi adapter as a radio button, plus an 'All Interfaces'
        fallback option. Syncs the radio variable with the application's
        current selected_interface.
        """
        # Clear existing entries
        self.adapter_menu.delete(0, tk.END)

        # Sync variable with current app state
        current = self.app.selected_interface if self.app.selected_interface else "Auto"
        self.selected_adapter_var.set(current)

        # Scan for Wi-Fi adapters
        try:
            interfaces = list(psutil.net_if_addrs().keys())
        except (OSError, psutil.Error) as e:
            logger.warning("Failed to enumerate network interfaces: %s", e)
            interfaces = []

        found_wifi = False

        # Add found Wi-Fi adapters as radio buttons
        for iface in interfaces:
            if "wi-fi" in iface.lower() or "wireless" in iface.lower():
                self.adapter_menu.add_radiobutton(
                    label=iface,
                    variable=self.selected_adapter_var,
                    value=iface,
                    command=lambda name=iface: self.set_adapter_wrapper(name)
                )
                found_wifi = True

        self.adapter_menu.add_separator()

        # Option to revert to all-interfaces aggregate
        self.adapter_menu.add_radiobutton(
            label="All Interfaces (Auto)",
            variable=self.selected_adapter_var,
            value="Auto",
            command=lambda: self.set_adapter_wrapper(None)
        )

        if not found_wifi:
            self.adapter_menu.add_command(
                label="(No Wi-Fi Found)", state=tk.DISABLED
            )

    def set_adapter_wrapper(self, name):
        """
        Update both the radio variable and the application's selected interface.

        Args:
            name (str or None): The interface name to monitor, or None for all.
        """
        val = name if name else "Auto"
        self.selected_adapter_var.set(val)
        self.app.set_interface(name)

    def change_theme(self, name):
        """
        Apply a new theme and update the context menu colors to match.

        Args:
            name (str): The theme name to apply (e.g. 'Dark', 'Light').
        """
        Theme.set_theme(name)
        self.app.apply_theme()
        # Rebuild menu style to match new colors
        self.rebuild_menu_style()

    def rebuild_menu_style(self):
        """
        Update the background, foreground, and selection colors of all menus
        to match the current theme palette.
        """
        cfg = {
            "bg": Theme.BG_COLOR,
            "fg": Theme.TEXT_MAIN,
            "activebackground": Theme.HOVER_COLOR,
            "activeforeground": Theme.TEXT_MAIN,
            "selectcolor": Theme.ACCENT_GREEN,
        }
        self.menu.config(**cfg)
        self.theme_menu.config(**cfg)
        self.adapter_menu.config(**cfg)

    def show(self, x, y):
        """
        Display the context menu at the specified screen coordinates.

        Refreshes the adapter list before showing to pick up any newly
        connected interfaces.

        Args:
            x (int): X screen coordinate for the menu.
            y (int): Y screen coordinate for the menu.
        """
        self.refresh_adapters()
        self.rebuild_menu_style()
        try:
            self.menu.tk_popup(x, y)
        finally:
            self.menu.grab_release()

    def toggle_lock(self):
        """
        Sync the application's lock state with the menu checkbutton variable.

        When locked, the widget window cannot be dragged to a new position.
        """
        self.app.is_locked = self.is_locked_var.get()

    def toggle_top(self):
        """
        Sync the application's always-on-top state with the menu checkbutton.

        When disabled, other windows may cover the widget.
        """
        state = self.is_ontop_var.get()
        self.app.attributes("-topmost", state)
