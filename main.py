"""
WiFi Meter - Main Application Module

A Windows desktop widget that monitors real-time network (Wi-Fi) upload/download
speeds and displays cumulative session data usage. Uses tkinter for the GUI,
psutil for network statistics, and pystray for system tray integration.

Author: Hishan Umayanga
Version: 0.2
"""

import tkinter as tk
import psutil
import time
import threading
import logging
import ctypes
from theme import Theme
from ui.context_menu import ContextMenuManager
from ui.data_stats import DataStatsWindow
from ui.about_win import AboutWindow
import pystray
from PIL import Image, ImageDraw

# Configure basic logging for debugging and error tracking
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class NetworkMonitor(tk.Tk):
    """
    Main application class for the WiFi Meter desktop widget.

    Inherits from tk.Tk to create a frameless, always-on-top overlay window
    that displays real-time network upload/download speeds and a session
    total data counter. Supports drag-to-move, right-click context menu,
    system tray icon, pause/resume, theme switching, and network interface
    selection.
    """

    # Maximum allowed speed value (10 GB/s) to filter out spurious counter resets
    MAX_SPEED_BYTES = 10 * 1024 * 1024 * 1024

    def __init__(self):
        """
        Initialize the NetworkMonitor application.

        Sets up the frameless overlay window, detects the default Wi-Fi
        interface, creates UI labels for upload/download speed and session
        total, binds mouse events for dragging and context menu, starts the
        background network monitoring thread, and initializes the system
        tray icon.
        """
        super().__init__()

        # --- Window Setup ---
        self.title("WiFi Meter")
        self.geometry("190x48+100+100")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.config(bg=Theme.BG_COLOR)

        # --- State ---
        self.last_upload = 0
        self.last_download = 0
        self.last_time = time.time()
        self.is_locked = False
        self.is_paused = False
        self.resume_flash_time = 0
        self.selected_interface = None
        self.running = True

        # Drag state (None means not currently dragging)
        self._drag_x = None
        self._drag_y = None

        # Track whether the user intentionally hid the window (via tray icon).
        # This prevents keep_on_top from restoring a deliberately hidden window.
        self._user_hidden = False

        # Thread lock for shared mutable state accessed by the monitor thread
        self._lock = threading.Lock()

        # --- Auto-Detect Default Wi-Fi ---
        try:
            interfaces = psutil.net_if_addrs().keys()
            for iface in interfaces:
                if "wi-fi" in iface.lower() or "wireless" in iface.lower():
                    self.selected_interface = iface
                    break
        except (OSError, psutil.Error) as e:
            logger.warning("Failed to auto-detect Wi-Fi interface: %s", e)

        # --- Data Tracking ---
        self.total_upload_session = 0
        self.total_download_session = 0

        # --- UI Elements ---
        self.main_frame = tk.Frame(self, bg=Theme.BG_COLOR, highlightthickness=0)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.frame_speeds = tk.Frame(self.main_frame, bg=Theme.BG_COLOR)
        self.frame_speeds.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.lbl_up = tk.Label(
            self.frame_speeds, text="↑ 0.0 KB/s",
            font=(Theme.FONT_FAMILY, Theme.FONT_SIZE_MAIN),
            bg=Theme.BG_COLOR, fg=Theme.ACCENT_RED, anchor="w"
        )
        self.lbl_up.pack(fill=tk.X, pady=(2, 0))

        self.lbl_down = tk.Label(
            self.frame_speeds, text="↓ 0.0 KB/s",
            font=(Theme.FONT_FAMILY, Theme.FONT_SIZE_MAIN),
            bg=Theme.BG_COLOR, fg=Theme.ACCENT_GREEN, anchor="w"
        )
        self.lbl_down.pack(fill=tk.X, pady=(0, 2))

        self.lbl_total = tk.Label(
            self.main_frame, text="0 MB",
            font=(Theme.FONT_FAMILY, Theme.FONT_SIZE_MAIN, "bold"),
            bg=Theme.BG_COLOR, fg=Theme.ACCENT_BLUE
        )
        self.lbl_total.pack(side=tk.RIGHT, padx=10)

        # --- Interaction ---
        self.bind("<Button-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.do_move)
        self.bind("<Button-3>", self.show_context_menu)

        # --- Sub-Windows ---
        self.stats_win = None

        # --- Context Menu ---
        self.menu_manager = ContextMenuManager(self)

        # --- Threading & Timers ---
        self.monitor_thread = threading.Thread(
            target=self.update_network_stats, daemon=True
        )
        self.monitor_thread.start()

        self.keep_on_top()

        # --- Tray Icon ---
        self.tray_icon = None
        self.setup_tray()

        # --- Graceful shutdown on window close ---
        self.protocol("WM_DELETE_WINDOW", self.cleanup_and_exit)

    # ================================================================
    # Feature Methods
    # ================================================================

    def set_interface(self, name):
        """
        Set the active network interface to monitor.

        Resets upload/download baselines to zero so that switching interfaces
        does not produce a false data spike on the next reading.

        Args:
            name (str or None): The interface name (e.g. 'Wi-Fi') or None
                                to monitor all interfaces combined.
        """
        with self._lock:
            self.selected_interface = name
            # Reset counters to prevent massive spike when switching
            self.last_upload = 0
            self.last_download = 0

    def apply_theme(self):
        """
        Refresh all widget colors from the current Theme class attributes.

        Called after a theme change to propagate new BG/FG colors to the
        main window, speed labels, total label, and any open sub-windows.
        """
        self.config(bg=Theme.BG_COLOR)
        self.main_frame.config(bg=Theme.BG_COLOR)
        self.frame_speeds.config(bg=Theme.BG_COLOR)

        self.lbl_up.config(bg=Theme.BG_COLOR, fg=Theme.ACCENT_RED)
        self.lbl_down.config(bg=Theme.BG_COLOR, fg=Theme.ACCENT_GREEN)
        self.lbl_total.config(bg=Theme.BG_COLOR, fg=Theme.ACCENT_BLUE)

        # If stats window is open, refresh it too
        if self.stats_win and self.stats_win.winfo_exists():
            self.stats_win.config(bg=Theme.BG_COLOR)

    def toggle_pause(self):
        """
        Toggle between paused and running monitoring states.

        When paused, upload/download speeds display as zero and labels turn
        red. On resume, labels flash green for 2 seconds before returning
        to normal theme colors.
        """
        self.is_paused = not self.is_paused

        if self.is_paused:
            self.update_labels(0, 0)
        else:
            # Resume State: Flash Green for 2 seconds
            self.resume_flash_time = time.time()

    def _force_topmost(self):
        """
        Use the Win32 API (SetWindowPos) to forcefully place the window
        on top of all others, including the taskbar.

        This bypasses tkinter's wrapper and directly calls the Windows
        API, which is more reliable when the taskbar or other system
        windows have stolen focus.
        """
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            # HWND_TOPMOST = -1, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE = 0x0013
            ctypes.windll.user32.SetWindowPos(
                hwnd, -1, 0, 0, 0, 0, 0x0013
            )
        except Exception:
            # Fallback to tkinter method
            try:
                self.lift()
                self.attributes("-topmost", True)
            except tk.TclError:
                pass

    def keep_on_top(self):
        """
        Periodically ensure the widget window stays above all other windows.

        Uses the Win32 API for forceful topmost positioning. Runs every
        200ms for near-instant recovery when covered by the taskbar.
        If Windows hides the widget (e.g., clicking Start button), this
        method auto-restores it — unless the user intentionally hid it
        via the tray icon.
        """
        if not self.running:
            return
        try:
            state = self.state()
            if state == "normal":
                self._force_topmost()
            elif not self._user_hidden and state in ("iconic", "withdrawn"):
                # Windows hid us (taskbar click, Show Desktop, etc.)
                # Restore the widget automatically
                self.deiconify()
                self._force_topmost()
        except tk.TclError:
            return  # Window has been destroyed
        self.after(200, self.keep_on_top)

    # ================================================================
    # System Tray
    # ================================================================

    def create_tray_image(self):
        """
        Generate a 64x64 pixel icon image for the system tray.

        Creates a dark background with a green upward-pointing triangle
        as a simple visual indicator for the WiFi Meter.

        Returns:
            PIL.Image.Image: The generated tray icon image.
        """
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color=(30, 30, 30))
        dc = ImageDraw.Draw(image)
        dc.polygon([(32, 10), (10, 40), (54, 40)], fill=(31, 223, 100))
        return image

    def setup_tray(self):
        """
        Create and start the system tray icon in a background thread.

        The tray icon provides a 'Show/Hide' toggle and an 'Exit' option.
        Runs in a daemon thread so it does not block application shutdown.
        """
        def run_tray():
            try:
                image = self.create_tray_image()
                menu = pystray.Menu(
                    pystray.MenuItem("Show/Hide", self.trigger_toggle),
                    pystray.MenuItem("Exit", self.trigger_exit)
                )
                self.tray_icon = pystray.Icon(
                    "WiFi Meter", image, "WiFi Meter", menu
                )
                self.tray_icon.run()
            except Exception as e:
                logger.error("Failed to start tray icon: %s", e)

        threading.Thread(target=run_tray, daemon=True).start()

    def trigger_toggle(self, icon, item):
        """
        Tray callback: schedule toggle_visibility on the main thread.

        Args:
            icon: The pystray Icon instance (unused).
            item: The menu item that was clicked (unused).
        """
        self.after(0, self.toggle_visibility)

    def trigger_exit(self, icon, item):
        """
        Tray callback: schedule cleanup_and_exit on the main thread.

        Args:
            icon: The pystray Icon instance (unused).
            item: The menu item that was clicked (unused).
        """
        self.after(0, self.cleanup_and_exit)

    def toggle_visibility(self):
        """
        Toggle the main window between visible and hidden states.

        If currently visible ('normal'), hides the window via withdraw()
        and sets _user_hidden so keep_on_top won't auto-restore it.
        If hidden, restores it, clears the flag, and ensures it stays on top.
        """
        try:
            if self.state() == "normal":
                self._user_hidden = True
                self.withdraw()
            else:
                self._user_hidden = False
                self.deiconify()
                self._force_topmost()
        except tk.TclError:
            pass  # Window already destroyed

    # ================================================================
    # Window Dragging
    # ================================================================

    def start_move(self, event):
        """
        Record the starting mouse position for a window drag operation.

        Only records if the window position is not locked.

        Args:
            event: The tkinter mouse event with x, y coordinates.
        """
        if not self.is_locked:
            self._drag_x = event.x
            self._drag_y = event.y

    def stop_move(self, event):
        """
        Clear the drag anchor point when the mouse button is released.

        Args:
            event: The tkinter mouse event (unused).
        """
        self._drag_x = None
        self._drag_y = None

    def do_move(self, event):
        """
        Move the window following the mouse cursor during a drag.

        Calculates the delta from the drag start position and repositions
        the window accordingly. Only moves if position is not locked and
        a drag anchor has been established.

        Args:
            event: The tkinter mouse event with current x, y coordinates.
        """
        if not self.is_locked and self._drag_x is not None and self._drag_y is not None:
            deltax = event.x - self._drag_x
            deltay = event.y - self._drag_y
            x = self.winfo_x() + deltax
            y = self.winfo_y() + deltay
            self.geometry(f"+{x}+{y}")

    def show_context_menu(self, event):
        """
        Display the right-click context menu at the cursor position.

        Args:
            event: The tkinter mouse event with x_root, y_root screen
                   coordinates.
        """
        self.menu_manager.show(event.x_root, event.y_root)

    # ================================================================
    # Data Formatting
    # ================================================================

    def format_bytes(self, size):
        """
        Format a byte-per-second value into a human-readable string.

        Converts raw bytes into KB/s, MB/s, GB/s, or TB/s with one
        decimal place.

        Args:
            size (float): Speed in bytes per second.

        Returns:
            str: Formatted string like '12.3 KB/s' or '1.5 MB/s'.
        """
        if size < 0:
            size = 0
        power = 2 ** 10
        n = 0
        power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while size >= power and n < 4:
            size /= power
            n += 1
        return f"{size:.1f} {power_labels.get(n, '')}B/s"

    def format_session_total(self, size):
        """
        Format cumulative session bytes into a human-readable MB or GB string.

        Args:
            size (float): Total bytes transferred in the session.

        Returns:
            str: Formatted string like '523 MB' or '1.2 GB'.
        """
        if size < 0:
            size = 0
        mb = size / (1024 * 1024)
        if mb < 1000:
            return f"{int(mb)} MB"
        else:
            gb = mb / 1024
            return f"{gb:.1f} GB"

    # ================================================================
    # Network Monitoring (Background Thread)
    # ================================================================

    def get_io_counters(self):
        """
        Retrieve current network I/O counters for the selected interface.

        If a specific interface is selected, returns per-NIC counters for
        that interface. Otherwise returns aggregate counters for all
        interfaces.

        Returns:
            psutil._common.snetio or None: The I/O counter named tuple,
            or None if the selected interface is unavailable.
        """
        try:
            if self.selected_interface:
                stats = psutil.net_io_counters(pernic=True)
                return stats.get(self.selected_interface, None)
            else:
                return psutil.net_io_counters()
        except (OSError, psutil.Error) as e:
            logger.warning("Error reading IO counters: %s", e)
            return None

    def update_network_stats(self):
        """
        Background thread loop that polls network I/O counters every second.

        Computes the difference in bytes_sent and bytes_recv between
        successive readings to derive upload and download speeds. Accumulates
        session totals. When paused, updates the baseline without counting
        data. Schedules UI label updates on the main thread via `after()`.

        This method runs indefinitely until `self.running` is set to False.
        """
        # Initial wait for the selected interface to become available
        wait_count = 0
        while self.selected_interface and not self.get_io_counters():
            time.sleep(1)
            wait_count += 1
            if wait_count > 30:
                logger.warning(
                    "Interface '%s' not available after 30s, falling back to all.",
                    self.selected_interface
                )
                with self._lock:
                    self.selected_interface = None
                break

        io_1 = self.get_io_counters() or psutil.net_io_counters()
        self.last_upload = io_1.bytes_sent
        self.last_download = io_1.bytes_recv

        while self.running:
            time.sleep(1)

            # --- Pause Logic ---
            if self.is_paused:
                # Update baseline so we don't spike on resume, but don't count data
                io_temp = self.get_io_counters()
                if io_temp:
                    self.last_upload = io_temp.bytes_sent
                    self.last_download = io_temp.bytes_recv

                # Send zero speeds to the UI
                try:
                    self.after(0, self.update_labels, 0, 0)
                except tk.TclError:
                    break  # Window destroyed
                continue

            # --- Running Logic ---
            io_2 = self.get_io_counters()
            if not io_2:
                continue  # Interface might be down/gone

            us = io_2.bytes_sent - self.last_upload
            ds = io_2.bytes_recv - self.last_download

            # Clamp negative values (counter reset) and absurdly large spikes
            if us < 0 or us > self.MAX_SPEED_BYTES:
                us = 0
            if ds < 0 or ds > self.MAX_SPEED_BYTES:
                ds = 0

            with self._lock:
                self.total_upload_session += us
                self.total_download_session += ds

            self.last_upload = io_2.bytes_sent
            self.last_download = io_2.bytes_recv

            try:
                self.after(0, self.update_labels, us, ds)
            except tk.TclError:
                break  # Window destroyed

    # ================================================================
    # UI Updates (Main Thread)
    # ================================================================

    def update_labels(self, up_speed, down_speed):
        """
        Update the speed and session total labels on the main window.

        Applies color overrides for paused (red) and recently-resumed
        (green flash) states. Also updates the Data Stats sub-window if
        it is open.

        Args:
            up_speed (int): Upload speed in bytes for the last interval.
            down_speed (int): Download speed in bytes for the last interval.
        """
        # Determine color state
        accent_up = Theme.ACCENT_RED
        accent_down = Theme.ACCENT_GREEN

        current_time = time.time()

        if self.is_paused:
            # Paused -> Red Digits
            accent_up = Theme.get_color("PAUSED")
            accent_down = Theme.get_color("PAUSED")
        elif (current_time - self.resume_flash_time) < 2.0:
            # Resumed (< 2s ago) -> Green Flash
            accent_up = Theme.get_color("RESUMED")
            accent_down = Theme.get_color("RESUMED")

        # Apply formatted text and colors
        self.lbl_up.config(text=f"↑ {self.format_bytes(up_speed)}", fg=accent_up)
        self.lbl_down.config(
            text=f"↓ {self.format_bytes(down_speed)}", fg=accent_down
        )

        with self._lock:
            total_session = self.total_upload_session + self.total_download_session
        self.lbl_total.config(text=self.format_session_total(total_session))

        # Update stats sub-window if open
        if self.stats_win and self.stats_win.winfo_exists():
            with self._lock:
                up_total = self.total_upload_session
                down_total = self.total_download_session
            self.stats_win.update_stats(up_total, down_total)

    # ================================================================
    # Sub-Windows
    # ================================================================

    def toggle_stats(self):
        """
        Open the Data Usage Statistics window, or bring it to the front
        if it is already open.
        """
        if self.stats_win is None or not self.stats_win.winfo_exists():
            self.stats_win = DataStatsWindow(self)
        else:
            self.stats_win.lift()

    def show_about(self):
        """
        Open the About dialog window showing version and author info.
        """
        AboutWindow(self)

    # ================================================================
    # Shutdown
    # ================================================================

    def cleanup_and_exit(self, icon=None, item=None):
        """
        Gracefully shut down the application.

        Stops the system tray icon, signals the monitor thread to exit,
        and destroys the main window. Safe to call from both the tray
        menu and the context menu.

        Args:
            icon: Optional pystray Icon instance (for tray callback signature).
            item: Optional pystray MenuItem instance (for tray callback signature).
        """
        self.running = False
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception as e:
            logger.debug("Error stopping tray icon: %s", e)
        try:
            self.destroy()
        except tk.TclError:
            pass  # Already destroyed


if __name__ == "__main__":
    app = NetworkMonitor()
    app.mainloop()
