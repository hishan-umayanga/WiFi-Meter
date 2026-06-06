"""
WiFi Meter - About Window Module

Displays a small dialog with the application name, version number,
and developer credits. Opened from the context menu.
"""

import tkinter as tk
from theme import Theme


class AboutWindow(tk.Toplevel):
    """
    A top-level dialog window displaying application information.

    Shows the application name, version number, and the developer's name.
    Includes a Close button to dismiss the window. Only one instance
    should be open at a time (enforced by the caller).
    """

    def __init__(self, parent):
        """
        Initialize the About dialog.

        Creates a non-resizable, always-on-top window centered with theme
        colors, showing the app name, version, and developer credit.

        Args:
            parent (tk.Tk): The parent NetworkMonitor application window.
        """
        super().__init__(parent)
        self.title("About")
        self.geometry("250x170")
        self.resizable(False, False)
        self.config(bg=Theme.BG_COLOR)
        self.attributes("-topmost", True)

        # Application name
        tk.Label(
            self, text="WiFi Meter",
            font=(Theme.FONT_FAMILY, 14, "bold"),
            bg=Theme.BG_COLOR, fg=Theme.ACCENT_BLUE
        ).pack(pady=(15, 5))

        # Version info
        tk.Label(
            self, text="Version v0.2",
            font=(Theme.FONT_FAMILY, 10),
            bg=Theme.BG_COLOR, fg=Theme.TEXT_DIM
        ).pack(pady=2)

        # Developer label
        tk.Label(
            self, text="Developer:",
            font=(Theme.FONT_FAMILY, 10),
            bg=Theme.BG_COLOR, fg=Theme.TEXT_MAIN
        ).pack(pady=(10, 0))

        # Developer name
        tk.Label(
            self, text="Hishan Umayanga",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            bg=Theme.BG_COLOR, fg=Theme.ACCENT_GREEN
        ).pack()

        # Close button
        tk.Button(
            self, text="Close", command=self.destroy,
            bg=Theme.HOVER_COLOR, fg=Theme.TEXT_MAIN,
            bd=0, padx=10, pady=5,
            activebackground=Theme.ACCENT_BLUE,
            activeforeground=Theme.TEXT_MAIN,
            cursor="hand2"
        ).pack(pady=15)
