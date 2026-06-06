"""
WiFi Meter - Theme Configuration Module

Defines the Theme class with class-level color and font constants for each
supported visual theme. Themes can be switched at runtime via set_theme().

Supported themes: Dark (default), Light, Neon, Cyberpunk.
"""

import re


class Theme:
    """
    Centralized theme configuration using class-level attributes.

    All color values are stored as hex strings (e.g. '#2b2b2b'). UI widgets
    read from these attributes directly; calling set_theme() updates them
    in place so all subsequent reads reflect the new theme.
    """

    # Current State (Default: Dark)
    BG_COLOR = "#2b2b2b"
    TEXT_MAIN = "#ffffff"
    TEXT_DIM = "#aaaaaa"
    ACCENT_GREEN = "#1fdf64"
    ACCENT_RED = "#ff5f5f"
    ACCENT_BLUE = "#3399ff"
    BORDER_COLOR = "#444444"
    HOVER_COLOR = "#333333"
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE_MAIN = 10
    FONT_SIZE_SMALL = 9

    # Valid hex color pattern for input validation
    _HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')

    # Predefined theme palettes - keeps theme data separate from logic
    _THEMES = {
        "Dark": {
            "BG_COLOR": "#2b2b2b",
            "TEXT_MAIN": "#ffffff",
            "TEXT_DIM": "#aaaaaa",
            "ACCENT_GREEN": "#1fdf64",
            "ACCENT_RED": "#ff5f5f",
            "ACCENT_BLUE": "#3399ff",
            "HOVER_COLOR": "#333333",
        },
        "Light": {
            "BG_COLOR": "#ffffff",
            "TEXT_MAIN": "#000000",
            "TEXT_DIM": "#666666",
            "ACCENT_GREEN": "#2e7d32",
            "ACCENT_RED": "#c62828",
            "ACCENT_BLUE": "#1565c0",
            "HOVER_COLOR": "#f5f5f5",
        },
        "Neon": {
            "BG_COLOR": "#000000",
            "TEXT_MAIN": "#00ffea",
            "TEXT_DIM": "#008f82",
            "ACCENT_GREEN": "#39ff14",
            "ACCENT_RED": "#ff0099",
            "ACCENT_BLUE": "#00ccff",
            "HOVER_COLOR": "#1a1a1a",
        },
        "Cyberpunk": {
            "BG_COLOR": "#120d21",
            "TEXT_MAIN": "#fcee0a",
            "TEXT_DIM": "#cfcfcf",
            "ACCENT_GREEN": "#0afc5b",
            "ACCENT_RED": "#fc0a43",
            "ACCENT_BLUE": "#0aeffc",
            "HOVER_COLOR": "#2a1f45",
        },
    }

    @classmethod
    def set_theme(cls, name):
        """
        Switch all theme colors to the specified named theme.

        Updates the class-level color attributes so that all widgets reading
        from Theme.* will reflect the new palette. Unknown theme names are
        ignored (a warning is logged).

        Args:
            name (str): Theme name — one of 'Dark', 'Light', 'Neon', 'Cyberpunk'.
        """
        if name not in cls._THEMES:
            import logging
            logging.getLogger(__name__).warning("Unknown theme: %s", name)
            return

        palette = cls._THEMES[name]
        for attr, value in palette.items():
            setattr(cls, attr, value)

    @classmethod
    def get_color(cls, state):
        """
        Return a special-purpose color for the given UI state.

        Used by the main monitor to override label colors during pause
        and resume-flash states.

        Args:
            state (str): One of 'PAUSED' or 'RESUMED'.

        Returns:
            str: A hex color string. Returns cls.TEXT_MAIN for unknown states.
        """
        state_colors = {
            "PAUSED": "#ff0000",   # Pure Red
            "RESUMED": "#00ff00",  # Pure Green
        }
        return state_colors.get(state, cls.TEXT_MAIN)

    @classmethod
    def get_available_themes(cls):
        """
        Return a list of all registered theme names.

        Returns:
            list[str]: Available theme names (e.g. ['Dark', 'Light', ...]).
        """
        return list(cls._THEMES.keys())
