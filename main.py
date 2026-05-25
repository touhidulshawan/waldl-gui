"""
waldl-gui — Wallhaven Image Downloader  (Catppuccin Mocha)
GUI app to search, browse, and download wallpapers from wallhaven.cc
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
import json
import os
import io
import time
import traceback
from PIL import Image, ImageTk
from pathlib import Path


# ─── API ──────────────────────────────────────────────────────────────────────
API_BASE   = "https://wallhaven.cc/api/v1"
THUMB_SIZE = (224, 144)
GRID_COLS  = 4

CATEGORIES = {
    "All":              "111",
    "General":          "100",
    "Anime":            "010",
    "People":           "001",
    "General + Anime":  "110",
    "General + People": "101",
    "Anime + People":   "011",
}
PURITY_OPTIONS  = {"SFW only": "100", "Sketchy only": "010", "SFW + Sketchy": "110"}
SORTING_OPTIONS = ["date_added", "relevance", "random", "views", "favorites", "toplist"]
ORDER_OPTIONS   = ["desc", "asc"]
TOP_RANGE_OPT   = ["1d", "3d", "1w", "1M", "3M", "6M", "1y"]
RESOLUTIONS     = ["Any","1280x720","1280x800","1280x960","1280x1024",
                   "1366x768","1600x900","1600x1200","1920x1080","1920x1200",
                   "2560x1440","2560x1600","3840x2160"]
RATIOS  = ["Any","16x9","16x10","4x3","5x4","21x9","32x9"]
COLORS  = ["Any","660000","990000","cc0000","cc3333","ea4c88","993399","663399",
           "333399","0066cc","0099cc","66cccc","77cc33","669900","336600","666600",
           "999900","cccc33","ffff00","ffcc33","ff9900","ff6600","cc6633","996633",
           "663300","000000","999999","cccccc","ffffff","424153"]

# ─── Catppuccin Mocha palette ─────────────────────────────────────────────────
# Base layers
CAT_CRUST  = "#11111b"   # deepest bg   – window background
CAT_MANTLE = "#181825"   # deeper bg    – toolbar / log bar
CAT_BASE   = "#1e1e2e"   # base bg      – sidebar
CAT_SURF0  = "#313244"   # surface 0    – card / tile bg
CAT_SURF1  = "#45475a"   # surface 1    – subtle borders
CAT_SURF2  = "#585b70"   # surface 2    – dimmer elements

# Overlays / text
CAT_OVL0   = "#6c7086"   # overlay 0    – placeholder / very muted
CAT_OVL1   = "#7f849c"   # overlay 1    – muted text
CAT_OVL2   = "#9399b2"   # overlay 2    – dim text
CAT_SUB0   = "#a6adc8"   # subtext 0    – secondary text
CAT_SUB1   = "#bac2de"   # subtext 1    – secondary text bright
CAT_TEXT   = "#cdd6f4"   # text         – primary text

# Accent colours (Catppuccin Mocha)
CAT_LAVEN  = "#b4befe"   # lavender
CAT_BLUE   = "#89b4fa"   # blue
CAT_SAPPH  = "#74c7ec"   # sapphire
CAT_SKY    = "#89dceb"   # sky
CAT_TEAL   = "#94e2d5"   # teal
CAT_GREEN  = "#a6e3a1"   # green
CAT_YELLOW = "#f9e2af"   # yellow
CAT_PEACH  = "#fab387"   # peach
CAT_MAROON = "#eba0ac"   # maroon
CAT_RED    = "#f38ba8"   # red
CAT_MAUVE  = "#cba6f7"   # mauve  ← primary accent
CAT_PINK   = "#f5c2e7"   # pink
CAT_FLAM   = "#f2cdcd"   # flamingo

# Semantic aliases
BG        = CAT_CRUST
SIDEBAR   = CAT_BASE
CARD      = CAT_MANTLE
CARD_SEL  = CAT_SURF0
TOOLBAR   = CAT_MANTLE
ACCENT    = CAT_MAUVE      # primary action  (mauve)
ACCENT_H  = CAT_LAVEN      # hover / active  (lavender)
ACCENT2   = CAT_BLUE       # secondary actions
ACCENT2_H = CAT_SAPPH
FG        = CAT_TEXT
FG_DIM    = CAT_SUB0
FG_MUTED  = CAT_OVL1
SEP       = CAT_SURF0
BTN_SEL   = CAT_MAUVE      # selected border
PURITY_SFW     = CAT_GREEN
PURITY_SKETCHY = CAT_YELLOW
PURITY_NSFW    = CAT_RED
HEART_CLR      = CAT_PINK


# ─── TTK theme ────────────────────────────────────────────────────────────────
def apply_ttk_theme(root: tk.Tk):
    style = ttk.Style(root)
    style.theme_use("clam")

    # Scrollbar
    style.configure("Vertical.TScrollbar",
                    gripcount=0,
                    background=CAT_SURF0, darkcolor=CAT_SURF0, lightcolor=CAT_SURF0,
                    troughcolor=CAT_CRUST, bordercolor=CAT_CRUST,
                    arrowcolor=CAT_OVL2, relief="flat")
    style.map("Vertical.TScrollbar",
              background=[("active", CAT_SURF1), ("pressed", CAT_SURF2)])

    # Combobox
    style.configure("TCombobox",
                    fieldbackground=CAT_SURF0,
                    background=CAT_SURF0,
                    foreground=CAT_TEXT,
                    selectbackground=CAT_SURF1,
                    selectforeground=CAT_YELLOW,
                    bordercolor=CAT_SURF1,
                    arrowcolor=CAT_LAVEN,
                    relief="flat",
                    padding=(6, 4))
    style.map("TCombobox",
              fieldbackground=[("readonly", CAT_SURF0)],
              foreground=[("readonly", CAT_TEXT)],
              bordercolor=[("focus", CAT_MAUVE)])
    root.option_add("*TCombobox*Listbox.background", CAT_SURF0)
    root.option_add("*TCombobox*Listbox.foreground", CAT_TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", CAT_SURF1)
    root.option_add("*TCombobox*Listbox.selectForeground", CAT_YELLOW)
    root.option_add("*TCombobox*Listbox.font", ("JetBrains Mono", 9))

    # Progressbar
    style.configure("TProgressbar",
                    troughcolor=CAT_MANTLE,
                    background=CAT_MAUVE,
                    bordercolor=CAT_MANTLE,
                    lightcolor=CAT_LAVEN,
                    darkcolor=CAT_MAUVE,
                    thickness=4)

    # Separator
    style.configure("TSeparator", background=CAT_SURF1)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _font(size=9, weight="normal", family="JetBrains Mono"):
    """Return a font tuple, falling back gracefully."""
    return (family, size, weight)


def fetch_thumbnail(url: str):
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content))
    img.thumbnail(THUMB_SIZE, Image.LANCZOS)
    return ImageTk.PhotoImage(img)


def cat_button(parent, text, command,
                   bg=ACCENT2, fg=CAT_CRUST,
                   active_bg=None, **kw):
    """
    A flat button that swaps to a lighter shade on hover/press,
    with a small internal padding and the Catppuccin Mocha theme.
    """
    if active_bg is None:
        active_bg = ACCENT2_H if bg == ACCENT2 else ACCENT_H

    defaults = dict(
        relief=tk.FLAT,
        font=_font(9, "bold"),
        cursor="hand2",
        padx=12, pady=5,
        bd=0,
        highlightthickness=0,
    )
    defaults.update(kw)

    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg,
        activebackground=active_bg, activeforeground=fg,
        **defaults,
    )

    # Subtle hover effect
    btn.bind("<Enter>", lambda _: btn.config(bg=active_bg))
    btn.bind("<Leave>", lambda _: btn.config(bg=bg))
    return btn


def cat_entry(parent, var, show=None, width=None):
    kw = {}
    if show:   kw["show"]  = show
    if width:  kw["width"] = width
    e = tk.Entry(
        parent, textvariable=var,
        bg=CAT_SURF0, fg=CAT_TEXT,
        insertbackground=CAT_YELLOW,
        selectbackground=CAT_SURF1,
        selectforeground=CAT_YELLOW,
        relief=tk.FLAT,
        font=_font(9),
        highlightthickness=1,
        highlightbackground=CAT_SURF1,
        highlightcolor=CAT_MAUVE,
        **kw,
    )
    return e


# ─── Main App ─────────────────────────────────────────────────────────────────
class WallhavenApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Wallhaven Downloader")
        self.geometry("1340x900")
        self.minsize(960, 640)
        self.configure(bg=BG)

        apply_ttk_theme(self)

        # ── vars ──────────────────────────────────────────────────────────────
        self.api_key      = tk.StringVar()
        self.query        = tk.StringVar()
        self.tag_id       = tk.StringVar()
        self.category_var = tk.StringVar(value="All")
        self.purity_var   = tk.StringVar(value="SFW only")
        self.sorting_var  = tk.StringVar(value="date_added")
        self.order_var    = tk.StringVar(value="desc")
        self.toprange_var = tk.StringVar(value="1M")
        self.res_var      = tk.StringVar(value="Any")
        self.ratio_var    = tk.StringVar(value="Any")
        self.color_var    = tk.StringVar(value="Any")
        self.min_w        = tk.StringVar()
        self.min_h        = tk.StringVar()
        self.save_dir     = tk.StringVar(value=str(Path.home() / "Pictures/Wallhaven"))

        # ── state ─────────────────────────────────────────────────────────────
        self.current_page  = 1
        self.total_pages   = 1
        self.results: list = []
        self.selected: set = set()
        self.thumb_cache: dict = {}
        self.tile_refs: list  = []

        self._build_ui()
        self._log("Ready — enter a query and press Search.")

    # ══════════════════════════════════════════════════════════════════════════
    #  UI BUILD
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        # ── Sidebar shell (scrollable) ─────────────────────────────────────
        sb_shell = tk.Frame(self, bg=SIDEBAR, width=276)
        sb_shell.pack(side=tk.LEFT, fill=tk.Y)
        sb_shell.pack_propagate(False)

        sb_canvas = tk.Canvas(sb_shell, bg=SIDEBAR, highlightthickness=0)
        sb_vsb    = ttk.Scrollbar(sb_shell, orient=tk.VERTICAL, command=sb_canvas.yview)
        sb_canvas.configure(yscrollcommand=sb_vsb.set)
        sb_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        sb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sidebar  = tk.Frame(sb_canvas, bg=SIDEBAR)
        _sb_win  = sb_canvas.create_window((0, 0), window=sidebar, anchor="nw")

        def _on_sb_inner(e):
            sb_canvas.configure(scrollregion=sb_canvas.bbox("all"))
        def _on_sb_outer(e):
            sb_canvas.itemconfig(_sb_win, width=e.width)
        def _on_sb_scroll(e):
            if   e.num == 4: sb_canvas.yview_scroll(-1, "units")
            elif e.num == 5: sb_canvas.yview_scroll( 1, "units")
            else:            sb_canvas.yview_scroll(int(-1*(e.delta/120)), "units")

        sidebar.bind("<Configure>",  _on_sb_inner)
        sb_canvas.bind("<Configure>", _on_sb_outer)
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            sb_canvas.bind(seq, _on_sb_scroll)
            sidebar.bind(seq,   _on_sb_scroll)

        # ── Main area ─────────────────────────────────────────────────────
        main = tk.Frame(self, bg=BG)
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_sidebar(sidebar)
        self._build_toolbar(main)
        self._build_grid(main)
        self._build_log(main)

        # Propagate sidebar scroll to all children (after widgets exist)
        def _bind_all_sb(widget):
            for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                widget.bind(seq, _on_sb_scroll, add="+")
            for child in widget.winfo_children():
                _bind_all_sb(child)
        self.after(120, lambda: _bind_all_sb(sidebar))

    # ── Sidebar helpers ───────────────────────────────────────────────────────
    def _section_label(self, parent, title):
        """Decorative section header with left accent bar."""
        row = tk.Frame(parent, bg=SIDEBAR)
        row.pack(fill=tk.X, padx=8, pady=(14, 2))

        # orange accent bar
        tk.Frame(row, bg=ACCENT, width=3).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        tk.Label(row, text=title.upper(),
                 bg=SIDEBAR, fg=CAT_YELLOW,
                 font=_font(7, "bold")).pack(side=tk.LEFT, anchor="w")

        # separator line
        tk.Frame(parent, bg=SEP, height=1).pack(fill=tk.X, padx=8, pady=(0, 4))

        f = tk.Frame(parent, bg=SIDEBAR)
        f.pack(fill=tk.X, padx=10, pady=(0, 4))
        return f

    def _combo(self, parent, var, values, width=19):
        cb = ttk.Combobox(parent, textvariable=var, values=values,
                          state="readonly", width=width,
                          font=_font(9))
        cb.pack(anchor="w", pady=3)
        return cb

    def _field_label(self, parent, text):
        tk.Label(parent, text=text, bg=SIDEBAR, fg=FG_DIM,
                 font=_font(8)).pack(anchor="w", pady=(4, 0))

    def _build_sidebar(self, sb):
        # ── Logo ──────────────────────────────────────────────────────────
        logo_f = tk.Frame(sb, bg=SIDEBAR)
        logo_f.pack(fill=tk.X, pady=(20, 4))
        tk.Label(logo_f, text="⬡", bg=SIDEBAR, fg=ACCENT,
                 font=_font(28)).pack()
        tk.Label(logo_f, text="WALLHAVEN",
                 bg=SIDEBAR, fg=CAT_YELLOW,
                 font=_font(13, "bold")).pack()
        tk.Label(logo_f, text="downloader",
                 bg=SIDEBAR, fg=FG_MUTED,
                 font=_font(8)).pack()
        tk.Frame(sb, bg=SEP, height=1).pack(fill=tk.X, padx=8, pady=(12, 0))

        # ── API Key ───────────────────────────────────────────────────────
        f = self._section_label(sb, "API Key")
        self._field_label(f, "Key (optional)")
        e = cat_entry(f, self.api_key, show="●")
        e.pack(fill=tk.X, pady=2)
        tk.Label(f, text="Required for NSFW & private collections",
                 bg=SIDEBAR, fg=FG_MUTED, font=_font(7),
                 wraplength=230, justify="left").pack(anchor="w")

        # ── Search ────────────────────────────────────────────────────────
        f = self._section_label(sb, "Search")
        self._field_label(f, "Query / keywords")
        qe = cat_entry(f, self.query)
        qe.pack(fill=tk.X, pady=2)
        qe.bind("<Return>", lambda _: self._do_search())

        self._field_label(f, "Tag ID  (e.g. 37)")
        te = cat_entry(f, self.tag_id)
        te.pack(fill=tk.X, pady=2)
        te.bind("<Return>", lambda _: self._do_search())

        # ── Category ──────────────────────────────────────────────────────
        f = self._section_label(sb, "Category")
        for name in CATEGORIES:
            rb = tk.Radiobutton(
                f, text=name,
                variable=self.category_var, value=name,
                bg=SIDEBAR, fg=FG,
                selectcolor=CAT_SURF0,
                activebackground=SIDEBAR, activeforeground=CAT_YELLOW,
                font=_font(9),
                indicatoron=True,
                cursor="hand2",
            )
            rb.pack(anchor="w", pady=1)

        # ── Purity ────────────────────────────────────────────────────────
        f = self._section_label(sb, "Purity")
        for name in PURITY_OPTIONS:
            rb = tk.Radiobutton(
                f, text=name,
                variable=self.purity_var, value=name,
                bg=SIDEBAR, fg=FG,
                selectcolor=CAT_SURF0,
                activebackground=SIDEBAR, activeforeground=CAT_YELLOW,
                font=_font(9),
                cursor="hand2",
            )
            rb.pack(anchor="w", pady=1)

        # ── Sorting ───────────────────────────────────────────────────────
        f = self._section_label(sb, "Sorting")
        self._field_label(f, "Sort by")
        self._combo(f, self.sorting_var, SORTING_OPTIONS)
        self._field_label(f, "Order")
        self._combo(f, self.order_var, ORDER_OPTIONS, width=10)
        self._field_label(f, "Top range")
        self._combo(f, self.toprange_var, TOP_RANGE_OPT, width=8)

        # ── Image Filters ─────────────────────────────────────────────────
        f = self._section_label(sb, "Image Filters")
        self._field_label(f, "Resolution")
        self._combo(f, self.res_var, RESOLUTIONS)
        self._field_label(f, "Aspect ratio")
        self._combo(f, self.ratio_var, RATIOS)
        self._field_label(f, "Accent color")
        self._combo(f, self.color_var, COLORS)

        self._field_label(f, "Minimum W × H")
        mf = tk.Frame(f, bg=SIDEBAR)
        mf.pack(fill=tk.X, pady=2)
        cat_entry(mf, self.min_w, width=7).pack(side=tk.LEFT)
        tk.Label(mf, text=" × ", bg=SIDEBAR, fg=FG_DIM,
                 font=_font(10)).pack(side=tk.LEFT)
        cat_entry(mf, self.min_h, width=7).pack(side=tk.LEFT)

        # ── Save Directory ────────────────────────────────────────────────
        f = self._section_label(sb, "Save Directory")
        df = tk.Frame(f, bg=SIDEBAR)
        df.pack(fill=tk.X, pady=2)
        cat_entry(df, self.save_dir).pack(side=tk.LEFT, fill=tk.X,
                                               expand=True)
        cat_button(df, "…", self._browse_dir,
                       bg=CAT_SURF0, fg=FG, active_bg=CAT_SURF1,
                       padx=8).pack(side=tk.LEFT, padx=(4, 0))

        # ── Search button ─────────────────────────────────────────────────
        tk.Frame(sb, bg=SEP, height=1).pack(fill=tk.X, padx=8, pady=(16, 8))
        cat_button(
            sb, "  🔍  SEARCH  ", self._do_search,
            bg=ACCENT, fg=CAT_CRUST, active_bg=ACCENT_H,
            font=_font(11, "bold"),
            pady=10,
        ).pack(fill=tk.X, padx=10, pady=(0, 20))

    # ── Toolbar ───────────────────────────────────────────────────────────────
    def _build_toolbar(self, parent):
        tb = tk.Frame(parent, bg=TOOLBAR, height=50)
        tb.pack(fill=tk.X)
        tb.pack_propagate(False)

        # left group – pagination
        lg = tk.Frame(tb, bg=TOOLBAR)
        lg.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))

        cat_button(lg, "◀  Prev", self._prev_page,
                       bg=CAT_SURF0, fg=FG, active_bg=CAT_SURF1).pack(
                       side=tk.LEFT, pady=10, padx=(0, 4))

        self.page_lbl = tk.Label(lg, text="—  /  —",
                                  bg=TOOLBAR, fg=FG_DIM,
                                  font=_font(9))
        self.page_lbl.pack(side=tk.LEFT, padx=8)

        cat_button(lg, "Next  ▶", self._next_page,
                       bg=CAT_SURF0, fg=FG, active_bg=CAT_SURF1).pack(
                       side=tk.LEFT, pady=10, padx=(4, 0))

        # divider
        tk.Frame(tb, bg=SEP, width=1).pack(side=tk.LEFT, fill=tk.Y,
                                            padx=14, pady=10)

        # middle group – selection
        mg = tk.Frame(tb, bg=TOOLBAR)
        mg.pack(side=tk.LEFT, fill=tk.Y)

        cat_button(mg, "✔ All", self._select_all,
                       bg=CAT_GREEN, fg=CAT_CRUST, active_bg=CAT_GREEN).pack(
                       side=tk.LEFT, pady=10, padx=(0, 4))
        cat_button(mg, "✘ Clear", self._clear_sel,
                       bg=CAT_RED, fg=CAT_TEXT, active_bg=CAT_RED).pack(
                       side=tk.LEFT, pady=10)

        self.sel_lbl = tk.Label(mg, text="0 selected",
                                 bg=TOOLBAR, fg=CAT_YELLOW,
                                 font=_font(9, "bold"))
        self.sel_lbl.pack(side=tk.LEFT, padx=12)

        # right group – download
        cat_button(tb, "  ⬇  Download Selected  ",
                       self._download_selected,
                       bg=ACCENT, fg=CAT_CRUST, active_bg=ACCENT_H,
                       font=_font(10, "bold"),
                       pady=6).pack(side=tk.RIGHT, padx=12, pady=10)

    # ── Grid ──────────────────────────────────────────────────────────────────
    def _build_grid(self, parent):
        wrap = tk.Frame(parent, bg=BG)
        wrap.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.grid_frame = tk.Frame(self.canvas, bg=BG)
        self._cw = self.canvas.create_window((0, 0), window=self.grid_frame,
                                              anchor="nw")

        self.grid_frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(
            self._cw, width=e.width))
        self.canvas.bind_all("<MouseWheel>", self._scroll)
        self.canvas.bind_all("<Button-4>",   self._scroll)
        self.canvas.bind_all("<Button-5>",   self._scroll)

        self._show_placeholder("Search for wallpapers  ☝")

    def _scroll(self, e):
        if   e.num == 4: self.canvas.yview_scroll(-1, "units")
        elif e.num == 5: self.canvas.yview_scroll( 1, "units")
        else:            self.canvas.yview_scroll(int(-1*(e.delta/120)), "units")

    # ── Log / Status bar ──────────────────────────────────────────────────────
    def _build_log(self, parent):
        bottom = tk.Frame(parent, bg=CAT_CRUST)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)

        self.progress = ttk.Progressbar(bottom, mode="indeterminate",
                                         style="TProgressbar")
        self.progress.pack(fill=tk.X)

        self.log_var = tk.StringVar(value="Ready.")
        bar = tk.Frame(bottom, bg=CAT_MANTLE, pady=3)
        bar.pack(fill=tk.X)
        tk.Label(bar, text="›", bg=CAT_MANTLE, fg=ACCENT,
                 font=_font(10, "bold")).pack(side=tk.LEFT, padx=(8, 2))
        tk.Label(bar, textvariable=self.log_var,
                 bg=CAT_MANTLE, fg=FG_MUTED,
                 font=_font(8), anchor="w").pack(side=tk.LEFT, fill=tk.X)

    def _log(self, msg: str):
        print(msg)
        self.log_var.set(msg)
        self.update_idletasks()

    def _busy(self, on: bool):
        if on:  self.progress.start(10)
        else:   self.progress.stop()

    # ══════════════════════════════════════════════════════════════════════════
    #  SEARCH
    # ══════════════════════════════════════════════════════════════════════════
    def _build_params(self, page=1) -> dict:
        p: dict = {"page": page}
        q_parts = []
        if q   := self.query.get().strip():    q_parts.append(q)
        if tid := self.tag_id.get().strip():   q_parts.append(f"id:{tid}")
        if q_parts: p["q"] = " ".join(q_parts)

        p["categories"] = CATEGORIES.get(self.category_var.get(), "111")
        p["purity"]     = PURITY_OPTIONS.get(self.purity_var.get(), "100")
        p["sorting"]    = self.sorting_var.get()
        p["order"]      = self.order_var.get()
        if p["sorting"] == "toplist":
            p["topRange"] = self.toprange_var.get()
        if (r  := self.res_var.get())   != "Any": p["resolutions"] = r
        if (rt := self.ratio_var.get()) != "Any": p["ratios"]      = rt
        if (c  := self.color_var.get()) != "Any": p["colors"]      = c
        mw, mh = self.min_w.get().strip(), self.min_h.get().strip()
        if mw and mh: p["atleast"] = f"{mw}x{mh}"
        if key := self.api_key.get().strip(): p["apikey"] = key
        return p

    def _do_search(self, page=1):
        self.current_page = page
        self._busy(True)
        self._log(f"Searching page {page}…")
        threading.Thread(target=self._search_worker, args=(page,),
                         daemon=True).start()

    def _search_worker(self, page: int):
        try:
            params  = self._build_params(page)
            headers = {}
            if key := self.api_key.get().strip():
                headers["X-API-Key"] = key

            self.after(0, lambda: self._log(
                "GET /search  " +
                json.dumps({k: v for k, v in params.items() if k != "apikey"})))

            resp = requests.get(f"{API_BASE}/search", params=params,
                                headers=headers, timeout=20)
            self.after(0, lambda: self._log(f"HTTP {resp.status_code}"))

            if resp.status_code != 200:
                self.after(0, lambda: self._log(
                    f"Error {resp.status_code}: {resp.text[:200]}"))
                self.after(0, lambda: messagebox.showerror(
                    "API Error", f"HTTP {resp.status_code}\n{resp.text[:300]}"))
                self.after(0, lambda: self._busy(False))
                return

            data  = resp.json()
            walls = data.get("data", [])
            meta  = data.get("meta", {})
            total = meta.get("last_page", 1)
            self.results     = walls
            self.total_pages = total
            self.after(0, lambda: self._render(walls))

        except requests.exceptions.ConnectionError as e:
            self.after(0, lambda: self._log(f"Connection error: {e}"))
            self.after(0, lambda: messagebox.showerror("Connection Error",
                f"Could not reach wallhaven.cc\n\n{e}"))
            self.after(0, lambda: self._busy(False))
        except Exception:
            tb = traceback.format_exc()
            self.after(0, lambda: self._log(f"Exception: {tb[:120]}"))
            self.after(0, lambda: messagebox.showerror("Error", tb))
            self.after(0, lambda: self._busy(False))

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDER
    # ══════════════════════════════════════════════════════════════════════════
    def _show_placeholder(self, msg):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        tk.Label(self.grid_frame, text=msg,
                 bg=BG, fg=FG_MUTED,
                 font=_font(14)).grid(row=0, column=0,
                 columnspan=GRID_COLS, pady=140, padx=60)

    def _render(self, walls: list):
        self._busy(False)
        self.tile_refs.clear()
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.canvas.yview_moveto(0)
        self.page_lbl.config(
            text=f"{self.current_page}  /  {self.total_pages}")
        self._log(
            f"{len(walls)} results — page {self.current_page}/{self.total_pages}")

        if not walls:
            self._show_placeholder("No results found.")
            return

        for idx, wp in enumerate(walls):
            row, col = divmod(idx, GRID_COLS)
            self._make_tile(wp, row, col)

        self._refresh_sel_label()

    def _make_tile(self, wp: dict, row: int, col: int):
        wid = wp["id"]
        sel = wid in self.selected

        # outer padding frame
        outer = tk.Frame(self.grid_frame, bg=BG, padx=5, pady=5)
        outer.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)

        # card frame — border colour changes on select
        border_clr = CAT_YELLOW if sel else CAT_SURF1
        card = tk.Frame(outer, bg=border_clr, bd=1, relief=tk.FLAT)
        card.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # ── Thumbnail ─────────────────────────────────────────────────────
        img_lbl = tk.Label(inner, bg=CAT_SURF0,
                           width=THUMB_SIZE[0], height=THUMB_SIZE[1],
                           text="loading…", fg=FG_MUTED,
                           font=_font(8))
        img_lbl.pack()

        # ── Info bar ──────────────────────────────────────────────────────
        info = tk.Frame(inner, bg=CARD, pady=3)
        info.pack(fill=tk.X, padx=6)

        purity     = wp.get("purity", "")
        purity_clr = {
            "sfw":     PURITY_SFW,
            "sketchy": PURITY_SKETCHY,
            "nsfw":    PURITY_NSFW,
        }.get(purity, FG_MUTED)

        tk.Label(info, text=purity.upper(),
                 bg=CARD, fg=purity_clr,
                 font=_font(7, "bold")).pack(side=tk.LEFT)

        tk.Label(info, text=wp.get("resolution", "?×?"),
                 bg=CARD, fg=FG_DIM,
                 font=_font(7)).pack(side=tk.LEFT, padx=8)

        tk.Label(info, text=f"♥ {wp.get('favorites', 0)}",
                 bg=CARD, fg=HEART_CLR,
                 font=_font(7)).pack(side=tk.RIGHT)

        # ── Select bar ────────────────────────────────────────────────────
        sel_bar = tk.Frame(inner, bg=CAT_SURF0, pady=3)
        sel_bar.pack(fill=tk.X)

        var = tk.BooleanVar(value=sel)

        def toggle(w=wid, v=var, c=card, ib=inner):
            if v.get():
                self.selected.add(w)
                c.config(bg=CAT_YELLOW)
                ib.config(bg=CARD)
            else:
                self.selected.discard(w)
                c.config(bg=CAT_SURF1)
                ib.config(bg=CARD)
            self._refresh_sel_label()

        chk = tk.Checkbutton(
            sel_bar, text="  Select",
            variable=var, command=toggle,
            bg=CAT_SURF0, fg=FG,
            selectcolor=CAT_SURF1,
            activebackground=CAT_SURF0, activeforeground=CAT_YELLOW,
            font=_font(8),
            cursor="hand2",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
        )
        chk.pack(side=tk.LEFT, padx=6)

        # wallpaper ID chip
        tk.Label(sel_bar, text=f"#{wid}",
                 bg=CAT_SURF0, fg=FG_MUTED,
                 font=_font(7)).pack(side=tk.RIGHT, padx=6)

        # store refs
        self.tile_refs.append({
            "wp": wp, "var": var, "card": card, "inner": inner,
            "img_lbl": img_lbl,
        })

        # async thumbnail load
        thumb_url = wp.get("thumbs", {}).get("small", "")
        if thumb_url:
            threading.Thread(target=self._load_thumb,
                             args=(thumb_url, img_lbl, wid),
                             daemon=True).start()

    def _load_thumb(self, url, lbl, wid):
        if wid not in self.thumb_cache:
            try:
                self.thumb_cache[wid] = fetch_thumbnail(url)
            except Exception:
                return
        photo = self.thumb_cache[wid]
        self.after(0, lambda: self._apply_thumb(lbl, photo))

    @staticmethod
    def _apply_thumb(lbl, photo):
        try:
            lbl.config(image=photo, text="",
                       width=THUMB_SIZE[0], height=THUMB_SIZE[1])
            lbl.image = photo
        except tk.TclError:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  SELECTION
    # ══════════════════════════════════════════════════════════════════════════
    def _refresh_sel_label(self):
        n = len(self.selected)
        self.sel_lbl.config(text=f"{n} selected")

    def _select_all(self):
        for t in self.tile_refs:
            wid = t["wp"]["id"]
            self.selected.add(wid)
            t["var"].set(True)
            t["card"].config(bg=CAT_YELLOW)
        self._refresh_sel_label()

    def _clear_sel(self):
        for t in self.tile_refs:
            wid = t["wp"]["id"]
            self.selected.discard(wid)
            t["var"].set(False)
            t["card"].config(bg=CAT_SURF1)
        self._refresh_sel_label()

    # ══════════════════════════════════════════════════════════════════════════
    #  PAGINATION
    # ══════════════════════════════════════════════════════════════════════════
    def _prev_page(self):
        if self.current_page > 1:
            self._do_search(self.current_page - 1)

    def _next_page(self):
        if self.current_page < self.total_pages:
            self._do_search(self.current_page + 1)

    # ══════════════════════════════════════════════════════════════════════════
    #  DOWNLOAD
    # ══════════════════════════════════════════════════════════════════════════
    def _browse_dir(self):
        d = filedialog.askdirectory(initialdir=self.save_dir.get())
        if d:
            self.save_dir.set(d)

    def _download_selected(self):
        if not self.selected:
            messagebox.showwarning("Nothing selected",
                                   "Tick at least one image first.")
            return
        save = self.save_dir.get().strip()
        if not save:
            messagebox.showwarning("No directory",
                                   "Please choose a save directory.")
            return

        visible = {t["wp"]["id"]: t["wp"] for t in self.tile_refs}
        to_dl   = [visible[w] for w in self.selected if w in visible]
        skipped = self.selected - set(visible.keys())

        if skipped:
            messagebox.showinfo("Note",
                f"{len(skipped)} selected image(s) are on other pages "
                f"and will be skipped.\nNavigate there and download too.")
        if not to_dl:
            messagebox.showinfo("Nothing to download",
                "None of the selected images are on this page.")
            return

        os.makedirs(save, exist_ok=True)
        self._busy(True)
        self._log(f"Downloading {len(to_dl)} image(s) → {save}")
        threading.Thread(target=self._dl_worker, args=(to_dl, save),
                         daemon=True).start()

    def _dl_worker(self, walls: list, save: str):
        headers = {}
        if key := self.api_key.get().strip():
            headers["X-API-Key"] = key

        done, failed = 0, []
        total = len(walls)

        for wp in walls:
            wid     = wp["id"]
            img_url = wp.get("path", "")
            if not img_url:
                failed.append(wid); continue

            ext      = img_url.rsplit(".", 1)[-1].split("?")[0]
            filename = os.path.join(save, f"wallhaven-{wid}.{ext}")

            if os.path.exists(filename):
                done += 1
                self.after(0, lambda d=done, t=total:
                    self._log(f"Skipped (exists) {d}/{t}"))
                continue

            try:
                self.after(0, lambda u=img_url:
                    self._log(f"Downloading {u}"))
                r = requests.get(img_url, headers=headers,
                                 timeout=60, stream=True)
                r.raise_for_status()
                with open(filename, "wb") as f:
                    for chunk in r.iter_content(65536):
                        f.write(chunk)
                done += 1
                self.after(0, lambda d=done, t=total:
                    self._log(f"Done {d}/{t}"))
            except Exception as e:
                failed.append(wid)
                self.after(0, lambda err=str(e):
                    self._log(f"Failed: {err}"))
            time.sleep(0.2)

        self.after(0, lambda: self._busy(False))
        msg = f"Downloaded {done}/{total} image(s) to:\n{save}"
        if failed:
            msg += f"\n\nFailed IDs: {', '.join(failed)}"
            self.after(0, lambda: messagebox.showwarning(
                "Done (with errors)", msg))
        else:
            self.after(0, lambda: messagebox.showinfo(
                "Download complete ✔", msg))
        self.after(0, lambda: self._log(msg.split("\n")[0]))


# ─── Entry ────────────────────────────────────────────────────────────────────
def main():
    app = WallhavenApp()
    app.mainloop()

if __name__ == "__main__":
    main()
