"""
WiFi Meter - Data Stats Window Module

Displays a pop-up window showing cumulative upload and download data
usage for the current monitoring session, updated in real-time.
"""

import tkinter as tk
from theme import Theme


class DataStatsWindow(tk.Toplevel):
    """
    A top-level window that shows session-total upload and download statistics.

    Opened via the 'Data Usage Stat' context menu option. Updates
    continuously while the main monitor is running.
    """

    def __init__(self, parent):
        """
        Initialize the Data Stats window.

        Creates labels for session upload/download totals, styled with
        the current theme colors. The window is set to always-on-top
        and is not resizable.

        Args:
            parent (tk.Tk): The parent NetworkMonitor application window.
        """
        super().__init__(parent)
        self.title("Data Usage")
        self.geometry("250x150")
        self.resizable(False, False)
        self.config(bg=Theme.BG_COLOR)
        self.attributes("-topmost", True)

        tk.Label(
            self, text="Session Data Usage",
            font=(Theme.FONT_FAMILY, 12, "bold"),
            bg=Theme.BG_COLOR, fg=Theme.TEXT_MAIN
        ).pack(pady=10)

        # Upload total label
        self.lbl_total_up = tk.Label(
            self, text="Total Upload: 0.0 MB",
            bg=Theme.BG_COLOR, fg=Theme.ACCENT_RED,
            font=(Theme.FONT_FAMILY, 10)
        )
        self.lbl_total_up.pack(anchor="w", padx=20, pady=5)

        # Download total label
        self.lbl_total_down = tk.Label(
            self, text="Total Download: 0.0 MB",
            bg=Theme.BG_COLOR, fg=Theme.ACCENT_GREEN,
            font=(Theme.FONT_FAMILY, 10)
        )
        self.lbl_total_down.pack(anchor="w", padx=20, pady=5)

    def format_size(self, size):
        """
        Convert a byte count into a human-readable size string.

        Iterates through B, KB, MB, GB, TB units until the value is
        below 1024, then returns it formatted with two decimal places.

        Args:
            size (float): Size in bytes.

        Returns:
            str: Formatted string like '12.34 MB' or '1.56 GB'.
        """
        if size < 0:
            size = 0
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def update_stats(self, total_up, total_down):
        """
        Refresh the upload and download total labels with new values.

        Called periodically from the main application's update_labels()
        method whenever this window is open and visible.

        Args:
            total_up (int): Total bytes uploaded this session.
            total_down (int): Total bytes downloaded this session.
        """
        try:
            self.lbl_total_up.config(
                text=f"Total Upload: {self.format_size(total_up)}"
            )
            self.lbl_total_down.config(
                text=f"Total Download: {self.format_size(total_down)}"
            )
        except tk.TclError:
            pass  # Window was closed
