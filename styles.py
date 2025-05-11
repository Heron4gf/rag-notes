import customtkinter as ctk

# --- Color Palette ---
COLOR_PALETTE = {
    "app_bg": "#2B2B2B",
    "top_bar_bg": "#3C3F41",
    "entry_bg": "#45494A",
    "text_area_bg": "#2B2B2B",
    "button_fg": "#007ACC",
    "button_hover": "#005C99",
    "text_color_light": "#DCDCDC",
    "text_color_dark": "#2B2B2B",
    "placeholder_text": "#A9A9A9",
    "border_color_accent": "#007ACC",
    "border_color_medium": "#555555",
    "icon_color": "#DCDCDC",
    "suggestions_bg": "#3C3F41",
    "suggestion_item_bg": "#45494A",
    "suggestion_item_hover": "#505354",
}

# --- Fonts (now as tuples/dictionaries for direct use by CTk widgets) ---
FONTS = {
    "entry": ("Segoe UI", 15),
    "text_area": ("Consolas", 15),
    "icon": ("Arial", 22),
    "button": ("Segoe UI Semibold", 13),
    "suggestion": ("Segoe UI", 13),
}

# --- App Level Settings ---
APPEARANCE_MODE = "Dark"
DEFAULT_COLOR_THEME = "blue"

# --- Widget Specific Style Dictionaries ---

TOP_FRAME_STYLE = {
    "corner_radius": 0,
    "fg_color": COLOR_PALETTE["top_bar_bg"],
}

ICON_LABEL_STYLE = {
    "text_color": COLOR_PALETTE["icon_color"],
    "font": FONTS["icon"],
    "fg_color": "transparent",
}

SEARCH_ENTRY_STYLE = {
    "font": FONTS["entry"],
    "height": 38,
    "placeholder_text_color": COLOR_PALETTE["placeholder_text"],
    "border_color": COLOR_PALETTE["border_color_accent"],
    "fg_color": COLOR_PALETTE["entry_bg"],
    "text_color": COLOR_PALETTE["text_color_light"],
    "corner_radius": 6,
}

TEXT_AREA_STYLE = {
    "font": FONTS["text_area"],
    "wrap": ctk.WORD,
    "corner_radius": 8,
    "border_width": 1,
    "border_color": COLOR_PALETTE["border_color_medium"],
    "fg_color": COLOR_PALETTE["text_area_bg"],
    "text_color": COLOR_PALETTE["text_color_light"],
    "scrollbar_button_color": COLOR_PALETTE["button_fg"],
    "scrollbar_button_hover_color": COLOR_PALETTE["button_hover"],
    # "insertbackground": COLOR_PALETTE["text_color_light"], # <--- REMOVE THIS LINE
}

SUGGESTIONS_SCROLL_FRAME_STYLE = {
    "height": 120,
    "corner_radius": 6,
    "fg_color": COLOR_PALETTE["suggestions_bg"],
    "scrollbar_button_color": COLOR_PALETTE["button_fg"],
    "scrollbar_button_hover_color": COLOR_PALETTE["button_hover"],
    "border_width": 1,
    "border_color": COLOR_PALETTE["border_color_medium"],
}

SUGGESTION_BUTTON_STYLE = {
    "font": FONTS["suggestion"],
    "anchor": "w",
    "height": 32,
    "fg_color": COLOR_PALETTE["suggestion_item_bg"],
    "hover_color": COLOR_PALETTE["suggestion_item_hover"],
    "text_color": COLOR_PALETTE["text_color_light"],
    "corner_radius": 4,
}