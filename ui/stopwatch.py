"""
WiFi Meter - Stopwatch Window Module

Provides a simple stopwatch utility window with start/pause and reset
functionality. Can be opened as a supplementary tool from the main widget.

Note: This module is defined but not currently wired into the context menu.
"""

import tkinter as tk
import time
from theme import Theme


class StopwatchWindow(tk.Toplevel):
    """
    A top-level window implementing a basic stopwatch with start/pause and reset.

    Displays elapsed time in HH:MM:SS format, updated every 50 milliseconds.
    Uses tkinter's `after()` scheduling for timer updates — no background
    threads are needed.
    """

    def __init__(self, parent):
        """
        Initialize the Stopwatch window.

        Creates the time display label and Start/Reset buttons. Begins the
        update loop immediately (in stopped state, so the display stays
        at 00:00:00 until the user presses Start).

        Args:
            parent (tk.Tk): The parent application window.
        """
        super().__init__(parent)
        self.title("Stopwatch")
        self.geometry("200x120")
        self.resizable(False, False)
        self.config(bg=Theme.BG_COLOR)
        self.attributes("-topmost", True)

        # Timer state
        self.is_running = False
        self.start_time = 0.0
        self.elapsed_time = 0.0
        self._update_job = None

        # Time display label
        self.time_lbl = tk.Label(
            self, text="00:00:00",
            font=(Theme.FONT_FAMILY, 24),
            bg=Theme.BG_COLOR, fg=Theme.ACCENT_BLUE
        )
        self.time_lbl.pack(pady=10)

        # Button frame
        btn_frame = tk.Frame(self, bg=Theme.BG_COLOR)
        btn_frame.pack(fill=tk.X, padx=10)

        self.btn_start = tk.Button(
            btn_frame, text="Start",
            command=self.toggle_start,
            bg=Theme.BG_COLOR, fg=Theme.TEXT_MAIN,
            cursor="hand2"
        )
        self.btn_start.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.btn_reset = tk.Button(
            btn_frame, text="Reset",
            command=self.reset_timer,
            bg=Theme.BG_COLOR, fg=Theme.TEXT_MAIN,
            cursor="hand2"
        )
        self.btn_reset.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Cancel the update loop when the window is closed
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start the display update loop
        self._schedule_update()

    def toggle_start(self):
        """
        Toggle the stopwatch between running and paused states.

        When starting, records the current time minus any previously
        elapsed time so the stopwatch resumes from where it left off.
        Updates the button label to reflect the new state.
        """
        if self.is_running:
            # Pause
            self.is_running = False
            self.btn_start.config(text="Start")
        else:
            # Start / Resume
            self.is_running = True
            self.start_time = time.time() - self.elapsed_time
            self.btn_start.config(text="Pause")

    def reset_timer(self):
        """
        Reset the stopwatch to 00:00:00 and stop it if running.

        Clears the elapsed time, resets the button text, and updates
        the display immediately.
        """
        self.is_running = False
        self.elapsed_time = 0.0
        self.btn_start.config(text="Start")
        self.time_lbl.config(text="00:00:00")

    def _schedule_update(self):
        """
        Schedule the next timer display update after 50 milliseconds.

        Saves the `after()` job ID so it can be cancelled on window close
        to prevent 'invalid command' TclErrors.
        """
        self.update_timer()
        self._update_job = self.after(50, self._schedule_update)

    def update_timer(self):
        """
        Recalculate and display the current elapsed time.

        Only recalculates if the stopwatch is currently running. Formats
        the elapsed seconds into HH:MM:SS display format.
        """
        if self.is_running:
            self.elapsed_time = time.time() - self.start_time

        # Format as HH:MM:SS
        total_secs = int(self.elapsed_time)
        mins, secs = divmod(total_secs, 60)
        hours, mins = divmod(mins, 60)

        self.time_lbl.config(text=f"{hours:02}:{mins:02}:{secs:02}")

    def _on_close(self):
        """
        Handle window close: cancel the update loop and destroy the window.

        Prevents TclError that would occur if the scheduled after() callback
        fires after the window has been destroyed.
        """
        if self._update_job is not None:
            self.after_cancel(self._update_job)
        self.destroy()
