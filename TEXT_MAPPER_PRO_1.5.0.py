import os
import sys
import threading
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import chardet
import difflib

# ─────────────────────────────────────────────────────────────────────────────
#  PALETA DE CORES
# ─────────────────────────────────────────────────────────────────────────────
DARK = {
    "bg":           "#0D1117",
    "surface":      "#161B22",
    "surface2":     "#1C2128",
    "border":       "#30363D",
    "border_focus": "#7C3AED",
    "accent":       "#7C3AED",
    "accent2":      "#4F8EF7",
    "accent_hover": "#9D5CF8",
    "text":         "#E6EDF3",
    "text_dim":     "#8B949E",
    "success":      "#3FB950",
    "warning":      "#D29922",
    "error":        "#F85149",
    "log_bg":       "#010409",
    "log_info":     "#4F8EF7",
    "log_warn":     "#D29922",
    "log_error":    "#F85149",
    "log_ok":       "#3FB950",
    "tree_odd":     "#161B22",
    "tree_even":    "#1C2128",
    "tree_sel":     "#2D3748",
    "scrollbar":    "#30363D",
    "progress_bg":  "#1C2128",
    "progress_fg":  "#7C3AED",
    "btn_primary":  "#7C3AED",
    "btn_primary_h":"#9D5CF8",
    "btn_secondary":"#21262D",
    "btn_second_h": "#30363D",
    "btn_action":   "#238636",
    "btn_action_h": "#2EA043",
}

LIGHT = {
    "bg":           "#F6F8FA",
    "surface":      "#FFFFFF",
    "surface2":     "#F0F2F5",
    "border":       "#D0D7DE",
    "border_focus": "#7C3AED",
    "accent":       "#7C3AED",
    "accent2":      "#0969DA",
    "accent_hover": "#9D5CF8",
    "text":         "#1F2328",
    "text_dim":     "#57606A",
    "success":      "#1A7F37",
    "warning":      "#9A6700",
    "error":        "#CF222E",
    "log_bg":       "#F6F8FA",
    "log_info":     "#0969DA",
    "log_warn":     "#9A6700",
    "log_error":    "#CF222E",
    "log_ok":       "#1A7F37",
    "tree_odd":     "#FFFFFF",
    "tree_even":    "#F6F8FA",
    "tree_sel":     "#DDF4FF",
    "scrollbar":    "#D0D7DE",
    "progress_bg":  "#E8EAED",
    "progress_fg":  "#7C3AED",
    "btn_primary":  "#7C3AED",
    "btn_primary_h":"#6D28D9",
    "btn_secondary":"#F6F8FA",
    "btn_second_h": "#E8EAED",
    "btn_action":   "#1F883D",
    "btn_action_h": "#1A7F37",
}


# ─────────────────────────────────────────────────────────────────────────────
#  WIDGET: BOTÃO MODERNO (Canvas-based com hover animado)
# ─────────────────────────────────────────────────────────────────────────────
class ModernButton(tk.Canvas):
    """Botão customizado com cantos arredondados e animação de hover."""

    def __init__(self, parent, text, command=None, style="primary",
                 width=180, height=34, font_size=9, icon="", **kwargs):
        super().__init__(parent, highlightthickness=0, bd=0,
                         width=width, height=height, **kwargs)
        self.command  = command
        self.style    = style
        self._text    = text
        self._icon    = icon
        self._fs      = font_size
        self._width   = width
        self._height  = height
        self._anim_id = None
        self._current_color = None
        self._target_color  = None
        self._disabled      = False
        self._drawing       = False

        self.bind("<Enter>",         self._on_enter)
        self.bind("<Leave>",         self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

        self._draw(None)

    def _get_colors(self, hover=False, pressed=False):
        C = self.master.winfo_toplevel()._C if hasattr(self.master.winfo_toplevel(), '_C') else DARK
        if self._disabled:
            return C["border"], C["text_dim"]
        if self.style == "primary":
            bg = C["btn_primary_h"] if hover or pressed else C["btn_primary"]
        elif self.style == "action":
            bg = C["btn_action_h"] if hover or pressed else C["btn_action"]
        elif self.style == "accent2":
            bg = C["accent_hover"] if hover or pressed else C["accent2"]
        else:
            bg = C["btn_second_h"] if hover or pressed else C["btn_secondary"]
        fg = C["text"]
        return bg, fg

    def _draw(self, event, hover=False, pressed=False):
        self._drawing = True
        try:
            self.delete("all")
            C = self.master.winfo_toplevel()._C if hasattr(self.master.winfo_toplevel(), '_C') else DARK
            self.configure(bg=C["bg"])
            bg, fg = self._get_colors(hover, pressed)
            w, h, r = self._width, self._height, 8
            self._rounded_rect(2, 2, w-2, h-2, r, fill=bg, outline="")
            label = (self._icon + "  " + self._text) if self._icon else self._text
            self.create_text(w//2, h//2, text=label, fill=fg,
                             font=("Segoe UI", self._fs, "bold"), anchor="center")
        finally:
            self._drawing = False

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [
            x1+r, y1,   x2-r, y1,
            x2, y1,     x2, y1+r,
            x2, y2-r,   x2, y2,
            x2-r, y2,   x1+r, y2,
            x1, y2,     x1, y2-r,
            x1, y1+r,   x1, y1,
        ]
        self.create_polygon(pts, smooth=True, **kw)

    def _on_enter(self, e):
        if not self._disabled:
            self._draw(e, hover=True)

    def _on_leave(self, e):
        if not self._disabled:
            self._draw(e, hover=False)

    def _on_press(self, e):
        if not self._disabled:
            self._draw(e, pressed=True)

    def _on_release(self, e):
        if not self._disabled:
            self._draw(e, hover=True)
            if self.command:
                self.command()

    def config_state(self, state):
        self._disabled = (state == 'disabled')
        self._draw(None)

    def refresh(self):
        self._draw(None)

    def configure(self, **kwargs):
        if "text" in kwargs:
            self._text = kwargs.pop("text")
        if "icon" in kwargs:
            self._icon = kwargs.pop("icon")
        super().configure(**kwargs)
        if not getattr(self, "_drawing", False):
            self._draw(None)

    def config(self, **kwargs):
        self.configure(**kwargs)


# ─────────────────────────────────────────────────────────────────────────────
#  WIDGET: ENTRADA MODERNA
# ─────────────────────────────────────────────────────────────────────────────
class ModernEntry(tk.Frame):
    """Entry com borda colorida ao focar."""

    def __init__(self, parent, textvariable=None, width=40, readonly=False, **kwargs):
        C = parent.winfo_toplevel()._C if hasattr(parent.winfo_toplevel(), '_C') else DARK
        super().__init__(parent, bg=C["border"], padx=1, pady=1)
        self._entry = tk.Entry(
            self, textvariable=textvariable, width=width,
            bg=C["surface2"], fg=C["text"], insertbackground=C["text"],
            relief="flat", bd=4,
            font=("Segoe UI", 9),
            state="readonly" if readonly else "normal",
            readonlybackground=C["surface2"],
        )
        self._entry.pack(fill="both", expand=True)
        self._entry.bind("<FocusIn>",  self._focus_in)
        self._entry.bind("<FocusOut>", self._focus_out)

    def _focus_in(self, e):
        C = self.winfo_toplevel()._C if hasattr(self.winfo_toplevel(), '_C') else DARK
        self.configure(bg=C["border_focus"])

    def _focus_out(self, e):
        C = self.winfo_toplevel()._C if hasattr(self.winfo_toplevel(), '_C') else DARK
        self.configure(bg=C["border"])

    def refresh(self, C):
        self.configure(bg=C["border"])
        self._entry.configure(bg=C["surface2"], fg=C["text"],
                               insertbackground=C["text"],
                               readonlybackground=C["surface2"])


# ─────────────────────────────────────────────────────────────────────────────
#  WIDGET: CARD (frame com borda e padding)
# ─────────────────────────────────────────────────────────────────────────────
class Card(tk.Frame):
    def __init__(self, parent, title="", **kwargs):
        C = parent.winfo_toplevel()._C if hasattr(parent.winfo_toplevel(), '_C') else DARK
        super().__init__(parent, bg=C["surface"], padx=0, pady=0)

        if title:
            hdr = tk.Frame(self, bg=C["surface"], pady=0)
            hdr.pack(fill="x", padx=12, pady=(10, 4))
            tk.Label(hdr, text=title, bg=C["surface"], fg=C["accent"],
                     font=("Segoe UI", 8, "bold")).pack(side="left")
            # Linha separadora
            sep = tk.Frame(self, bg=C["border"], height=1)
            sep.pack(fill="x", padx=12, pady=(0, 8))

        self.body = tk.Frame(self, bg=C["surface"], padx=12, pady=8)
        self.body.pack(fill="both", expand=True)


# ─────────────────────────────────────────────────────────────────────────────
#  WIDGET: BARRA DE PROGRESSO CUSTOMIZADA
# ─────────────────────────────────────────────────────────────────────────────
class ModernProgressBar(tk.Canvas):
    def __init__(self, parent, height=6, **kwargs):
        C = parent.winfo_toplevel()._C if hasattr(parent.winfo_toplevel(), '_C') else DARK
        super().__init__(parent, height=height, highlightthickness=0, bd=0,
                         bg=C["bg"], **kwargs)
        self._max = 100
        self._val = 0
        self._h   = height
        self.bind("<Configure>", self._redraw)

    def config(self, **kw):
        if "maximum" in kw:
            self._max = kw.pop("maximum")
        if "value" in kw:
            self._val = kw.pop("value")
        if kw:
            super().config(**kw)
        self._redraw(None)

    def _redraw(self, event):
        self.delete("all")
        C = self.winfo_toplevel()._C if hasattr(self.winfo_toplevel(), '_C') else DARK
        self.configure(bg=C["bg"])
        w = self.winfo_width() or 400
        h = self._h
        r = h // 2
        # Track
        self._rounded_rect(0, 0, w, h, r, fill=C["progress_bg"])
        # Fill
        ratio = (self._val / self._max) if self._max else 0
        fw = int(w * ratio)
        if fw > r * 2:
            self._rounded_rect(0, 0, fw, h, r, fill=C["progress_fg"])
        elif fw > 0:
            self.create_oval(0, 0, h, h, fill=C["progress_fg"], outline="")

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [
            x1+r, y1,   x2-r, y1,
            x2, y1,     x2, y1+r,
            x2, y2-r,   x2, y2,
            x2-r, y2,   x1+r, y2,
            x1, y2,     x1, y2-r,
            x1, y1+r,   x1, y1,
        ]
        self.create_polygon(pts, smooth=True, **kw)

    def refresh(self):
        self._redraw(None)


# ─────────────────────────────────────────────────────────────────────────────
#  APLICAÇÃO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
class TextMapperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Text Translation Mapper Pro — 1.5.0")
        self.geometry("1200x800")
        self.minsize(1100, 700)

        # Tema — começa no dark
        self._dark_mode = True
        self._C = DARK.copy()

        # ── Estados ──────────────────────────────────────────────────────────
        self.folder_a = tk.StringVar()
        self.folder_b = tk.StringVar()
        self.folder_c = tk.StringVar()

        self.encoding_options = ["utf-8","cp1252","utf-16-le","utf-16-be","latin-1","shift-jis","big5"]
        self.encoding_ab       = tk.StringVar(value="utf-8")
        self.encoding_c_out    = tk.StringVar(value="utf-8")
        self.force_encoding_c  = tk.BooleanVar(value=False)

        self.dark_mode             = tk.BooleanVar(value=True)
        self.recursive_search      = tk.BooleanVar(value=True)
        self.file_extension        = tk.StringVar(value=".txt")
        self.match_by_filename_only= tk.BooleanVar(value=False)
        self.brute_force_by_order  = tk.BooleanVar(value=False)
        self.unified_dict          = tk.BooleanVar(value=False)
        self.ignore_prefixes       = tk.StringVar(value="")
        self.mapping_mode          = tk.StringVar(value="content")
        self.validate_positional   = tk.BooleanVar(value=True)
        self.fuzzy_threshold       = tk.DoubleVar(value=100.0)

        self.mappings         = {}
        self.mappings_by_name = {}
        self.mappings_list    = []
        self.global_mapping   = {}   # Dicionário único mesclado de todos os pares A/B

        # Status counters
        self._status_mapped    = 0
        self._status_processed = 0

        # Coleções de widgets para re-tematizar
        self._all_widgets      = []
        self._modern_buttons   = []
        self._modern_entries   = []
        self._progress_bars    = []
        self._cards            = []

        self._build_ui()
        self._apply_theme()
        self._update_mode_options()

    # ── Tema ─────────────────────────────────────────────────────────────────
    def _apply_theme(self):
        C = self._C
        self.configure(bg=C["bg"])

        # TTK styles
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", background=C["bg"], foreground=C["text"],
                        font=("Segoe UI", 9))
        style.configure("TFrame",         background=C["bg"])
        style.configure("TLabel",         background=C["bg"], foreground=C["text"],
                        font=("Segoe UI", 9))
        style.configure("Dim.TLabel",     background=C["bg"], foreground=C["text_dim"],
                        font=("Segoe UI", 8))
        style.configure("Header.TLabel",  background=C["surface"], foreground=C["text"],
                        font=("Segoe UI", 9, "bold"))
        style.configure("Accent.TLabel",  background=C["surface"], foreground=C["accent"],
                        font=("Segoe UI", 8, "bold"))

        style.configure("TLabelframe",        background=C["surface"],
                        foreground=C["accent"], relief="flat", borderwidth=0)
        style.configure("TLabelframe.Label",  background=C["surface"],
                        foreground=C["accent"], font=("Segoe UI", 9, "bold"))

        style.configure("TCombobox",
                        fieldbackground=C["surface2"], background=C["surface2"],
                        foreground=C["text"], selectbackground=C["accent"],
                        selectforeground=C["text"], arrowcolor=C["text_dim"],
                        borderwidth=0)
        style.map("TCombobox",
                  fieldbackground=[("readonly", C["surface2"])],
                  foreground=[("readonly", C["text"])])

        style.configure("TCheckbutton",
                        background=C["surface"], foreground=C["text"],
                        indicatorcolor=C["accent"], indicatorrelief="flat",
                        font=("Segoe UI", 9))
        style.map("TCheckbutton",
                  background=[("active", C["surface"])],
                  indicatorcolor=[("selected", C["accent"]), ("!selected", C["border"])])

        style.configure("TRadiobutton",
                        background=C["surface"], foreground=C["text"],
                        indicatorcolor=C["accent"],
                        font=("Segoe UI", 9))
        style.map("TRadiobutton",
                  background=[("active", C["surface"])],
                  indicatorcolor=[("selected", C["accent"]), ("!selected", C["border"])])

        style.configure("TScale",
                        background=C["surface"], troughcolor=C["border"],
                        sliderrelief="flat")

        # Treeview
        style.configure("Treeview",
                        background=C["tree_odd"], foreground=C["text"],
                        fieldbackground=C["tree_odd"],
                        rowheight=26, font=("Segoe UI", 9),
                        borderwidth=0, relief="flat")
        style.configure("Treeview.Heading",
                        background=C["surface2"], foreground=C["text_dim"],
                        font=("Segoe UI", 8, "bold"),
                        relief="flat", borderwidth=0)
        style.map("Treeview",
                  background=[("selected", C["tree_sel"])],
                  foreground=[("selected", C["text"])])
        style.map("Treeview.Heading",
                  background=[("active", C["border"])])

        # Scrollbar
        style.configure("TScrollbar",
                        background=C["surface2"], troughcolor=C["surface"],
                        arrowcolor=C["text_dim"], relief="flat", borderwidth=0)

        # Separador
        style.configure("TSeparator", background=C["border"])

        # PanedWindow
        style.configure("TPanedwindow", background=C["bg"])

        # Widgets tk nativos
        self._refresh_tk_widgets(C)

        # Refresh custom widgets
        for btn in self._modern_buttons:
            try:
                btn.configure(bg=C["bg"])
                btn.refresh()
            except tk.TclError:
                pass
        for entry in self._modern_entries:
            try:
                entry.refresh(C)
            except tk.TclError:
                pass
        for pb in self._progress_bars:
            try:
                pb.refresh()
            except tk.TclError:
                pass

        # Log console
        try:
            self.log_text.configure(
                bg=C["log_bg"], fg=C["text"], insertbackground=C["text"],
                selectbackground=C["accent"], selectforeground=C["text"])
            self.log_text.tag_config("INFO",    foreground=C["log_info"])
            self.log_text.tag_config("WARN",    foreground=C["log_warn"])
            self.log_text.tag_config("ERROR",   foreground=C["log_error"])
            self.log_text.tag_config("OK",      foreground=C["log_ok"])
            self.log_text.tag_config("DIM",     foreground=C["text_dim"])
        except: pass

        # Listbox
        try:
            self.files_listbox.configure(
                bg=C["surface"], fg=C["text"],
                selectbackground=C["tree_sel"], selectforeground=C["text"],
                activestyle="none")
        except: pass

        # Status bar
        try:
            self.status_bar.configure(bg=C["surface2"])
            self.status_label.configure(bg=C["surface2"], fg=C["text_dim"])
            self.version_label.configure(bg=C["surface2"], fg=C["text_dim"])
        except: pass

        # Title bar area
        try:
            self.title_frame.configure(bg=C["surface"])
            self.title_label.configure(bg=C["surface"], fg=C["text"])
            self.subtitle_label.configure(bg=C["surface"], fg=C["text_dim"])
            self.logo_frame.configure(bg=C["accent"])
        except: pass

        # Refresh treeview stripes
        self._apply_treeview_stripes()

    def _refresh_tk_widgets(self, C):
        """Propaga bg/fg para todos os frames tk registrados."""
        for w in self._all_widgets:
            try:
                cls = w.winfo_class()
                if cls in ("Frame", "Labelframe"):
                    w.configure(bg=C["surface"])
                elif cls == "Label":
                    parent_bg = C["bg"]
                    try: parent_bg = w.master.cget("bg")
                    except: pass
                    w.configure(bg=parent_bg, fg=C["text"])
            except tk.TclError:
                pass

    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        self._C = DARK.copy() if self._dark_mode else LIGHT.copy()
        self.dark_mode.set(self._dark_mode)
        text = "Modo Claro" if self._dark_mode else "Modo Escuro"
        icon = "☀" if self._dark_mode else "🌙"
        self.theme_btn.configure(text=text, icon=icon)
        self._apply_theme()

    def _apply_treeview_stripes(self):
        C = self._C
        try:
            self.tree.tag_configure("odd",  background=C["tree_odd"])
            self.tree.tag_configure("even", background=C["tree_even"])
        except: pass

    # ── Helpers de layout ────────────────────────────────────────────────────
    def _make_label(self, parent, text, style="normal", **kw):
        C = self._C
        bg = kw.pop("bg", parent.cget("bg") if hasattr(parent, "cget") else C["bg"])
        fg_map = {
            "normal": C["text"],
            "dim":    C["text_dim"],
            "accent": C["accent"],
            "header": C["text"],
        }
        font_map = {
            "normal": ("Segoe UI", 9),
            "dim":    ("Segoe UI", 8),
            "accent": ("Segoe UI", 8, "bold"),
            "header": ("Segoe UI", 9, "bold"),
        }
        lbl = tk.Label(parent, text=text, bg=bg, fg=fg_map.get(style, C["text"]),
                       font=font_map.get(style, ("Segoe UI", 9)), **kw)
        self._all_widgets.append(lbl)
        return lbl

    def _make_sep(self, parent, orient="h"):
        C = self._C
        if orient == "h":
            sep = tk.Frame(parent, bg=C["border"], height=1)
        else:
            sep = tk.Frame(parent, bg=C["border"], width=1)
        return sep

    def _make_modern_btn(self, parent, text, command=None, style="secondary",
                         width=160, height=32, font_size=9, icon=""):
        btn = ModernButton(parent, text=text, command=command, style=style,
                           width=width, height=height, font_size=font_size,
                           icon=icon, bg=self._C["bg"])
        self._modern_buttons.append(btn)
        return btn

    def _make_modern_entry(self, parent, textvariable=None, width=40, readonly=False):
        entry = ModernEntry(parent, textvariable=textvariable,
                            width=width, readonly=readonly)
        self._modern_entries.append(entry)
        return entry

    # ── Construção da UI ─────────────────────────────────────────────────────
    def _build_ui(self):
        C = self._C

        # ── Cabeçalho / Title Bar ────────────────────────────────────────────
        self.title_frame = tk.Frame(self, bg=C["surface"], pady=0)
        self.title_frame.pack(fill="x", side="top")

        inner_title = tk.Frame(self.title_frame, bg=C["surface"], padx=16, pady=10)
        inner_title.pack(fill="x")

        # Logo pill
        self.logo_frame = tk.Frame(inner_title, bg=C["accent"],
                                   padx=10, pady=4)
        self.logo_frame.pack(side="left", padx=(0, 12))
        tk.Label(self.logo_frame, text="TMP", bg=C["accent"], fg="#FFFFFF",
                 font=("Segoe UI", 10, "bold")).pack()

        title_text_frame = tk.Frame(inner_title, bg=C["surface"])
        title_text_frame.pack(side="left", fill="y")
        self.title_label = tk.Label(title_text_frame,
                                    text="Text Translation Mapper Pro",
                                    bg=C["surface"], fg=C["text"],
                                    font=("Segoe UI", 13, "bold"))
        self.title_label.pack(anchor="w")
        self.subtitle_label = tk.Label(title_text_frame,
                                       text="v1.5.0  •  Mapeamento inteligente de traduções",
                                       bg=C["surface"], fg=C["text_dim"],
                                       font=("Segoe UI", 8))
        self.subtitle_label.pack(anchor="w")

        # Botões lado direito do header
        btn_area = tk.Frame(inner_title, bg=C["surface"])
        btn_area.pack(side="right")

        help_btn = self._make_modern_btn(btn_area, "Ajuda", command=self._show_instructions,
                                         style="secondary", width=90, height=30, icon="❓")
        help_btn.pack(side="left", padx=(0, 8))

        self.theme_btn = self._make_modern_btn(btn_area, "Modo Claro",
                                               command=self._toggle_theme,
                                               style="secondary", width=120, height=30, icon="☀")
        self.theme_btn.pack(side="left")

        # Separador abaixo do header
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        # ── Área de conteúdo principal ───────────────────────────────────────
        main = tk.Frame(self, bg=C["bg"], padx=16, pady=12)
        main.pack(fill="both", expand=True)

        # ── Seção de Pastas ──────────────────────────────────────────────────
        folders_card = tk.Frame(main, bg=C["surface"], pady=0)
        folders_card.pack(fill="x", pady=(0, 10))

        # Card header
        fhdr = tk.Frame(folders_card, bg=C["surface"], padx=14, pady=8)
        fhdr.pack(fill="x")
        tk.Label(fhdr, text="📂  CONFIGURAÇÃO DE PASTAS", bg=C["surface"],
                 fg=C["accent"], font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Frame(folders_card, bg=C["border"], height=1).pack(fill="x", padx=14)

        fbody = tk.Frame(folders_card, bg=C["surface"], padx=14, pady=10)
        fbody.pack(fill="x")
        fbody.columnconfigure(1, weight=1)

        folder_defs = [
            ("A  •  Originais",  "📄", self.folder_a),
            ("B  •  Traduções",  "📋", self.folder_b),
            ("C  •  A Traduzir", "🎯", self.folder_c),
        ]
        self._folder_entries = []
        for i, (label_text, icon, var) in enumerate(folder_defs):
            lbl_frame = tk.Frame(fbody, bg=C["surface"])
            lbl_frame.grid(row=i, column=0, sticky="w", pady=4, padx=(0, 12))
            tk.Label(lbl_frame, text=icon, bg=C["surface"], fg=C["text"],
                     font=("Segoe UI", 10)).pack(side="left", padx=(0, 4))
            tk.Label(lbl_frame, text=label_text, bg=C["surface"], fg=C["text"],
                     font=("Segoe UI", 9, "bold")).pack(side="left")

            entry = self._make_modern_entry(fbody, textvariable=var, width=60, readonly=True)
            entry.grid(row=i, column=1, padx=(0, 10), pady=4, sticky="ew")
            self._folder_entries.append(entry)

            browse_btn = self._make_modern_btn(fbody, "Procurar",
                                               command=lambda v=var: self._select_folder(v),
                                               style="secondary", width=90, height=28, icon="🔍")
            browse_btn.grid(row=i, column=2, pady=4)

        # ── Barra de Configuração + Ações ────────────────────────────────────
        cfg_bar = tk.Frame(main, bg=C["surface"])
        cfg_bar.pack(fill="x", pady=(0, 10))
        tk.Frame(cfg_bar, bg=C["border"], height=1).pack(fill="x")

        cfg_inner = tk.Frame(cfg_bar, bg=C["surface"], padx=14, pady=8)
        cfg_inner.pack(fill="x")

        # Encoding
        enc_grp = tk.Frame(cfg_inner, bg=C["surface"])
        enc_grp.pack(side="left")

        def _lbl(txt, parent=enc_grp):
            tk.Label(parent, text=txt, bg=C["surface"], fg=C["text_dim"],
                     font=("Segoe UI", 8)).pack(side="left", padx=(0, 3))

        _lbl("Enc A/B")
        ttk.Combobox(enc_grp, textvariable=self.encoding_ab,
                     values=self.encoding_options, width=9,
                     state="readonly").pack(side="left", padx=(0, 10))
        _lbl("Enc C/Out")
        ttk.Combobox(enc_grp, textvariable=self.encoding_c_out,
                     values=self.encoding_options, width=9,
                     state="readonly").pack(side="left", padx=(0, 6))

        ttk.Checkbutton(enc_grp, text="Forçar em C",
                         variable=self.force_encoding_c).pack(side="left", padx=(0, 16))

        _lbl("Extensão", parent=enc_grp)
        ext_entry = tk.Entry(enc_grp, textvariable=self.file_extension, width=7,
                              bg=C["surface2"], fg=C["text"], insertbackground=C["text"],
                              relief="flat", bd=4, font=("Segoe UI", 9))
        ext_entry.pack(side="left", padx=(0, 16))

        ttk.Checkbutton(enc_grp, text="Brute Force (Ordem)",
                         variable=self.brute_force_by_order,
                         command=self._toggle_brute_force).pack(side="left")

        # Botões de ação principais
        btn_grp = tk.Frame(cfg_inner, bg=C["surface"])
        btn_grp.pack(side="right")

        self.btn_build = self._make_modern_btn(
            btn_grp, "1. Criar Dicionário",
            command=self.build_mappings,
            style="primary", width=200, height=34, icon="⚙")
        self.btn_build.pack(side="left", padx=(0, 8))

        self.btn_apply = self._make_modern_btn(
            btn_grp, "2. Aplicar Dicionário",
            command=self.apply_mappings,
            style="action", width=210, height=34, icon="▶")
        self.btn_apply.config_state("disabled")
        self.btn_apply.pack(side="left", padx=(0, 8))

        self.btn_report = self._make_modern_btn(
            btn_grp, "3. Aplicar Relatório",
            command=self.apply_report,
            style="accent2", width=190, height=34, icon="📋")
        self.btn_report.config_state("disabled")
        self.btn_report.pack(side="left")

        # ── Opções de Processamento ──────────────────────────────────────────
        opts_card = tk.Frame(main, bg=C["surface"])
        opts_card.pack(fill="x", pady=(0, 10))
        tk.Frame(opts_card, bg=C["border"], height=1).pack(fill="x")

        ohdr = tk.Frame(opts_card, bg=C["surface"], padx=14, pady=6)
        ohdr.pack(fill="x")
        tk.Label(ohdr, text="⚙  OPÇÕES DE PROCESSAMENTO", bg=C["surface"],
                 fg=C["accent"], font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Frame(opts_card, bg=C["border"], height=1).pack(fill="x", padx=14)

        opts_body = tk.Frame(opts_card, bg=C["surface"], padx=14, pady=10)
        opts_body.pack(fill="x")

        # Coluna 1: checkboxes gerais
        col1 = tk.Frame(opts_body, bg=C["surface"])
        col1.pack(side="left", padx=(0, 24))

        ttk.Checkbutton(col1, text="Busca em Subpastas",
                         variable=self.recursive_search).pack(anchor="w", pady=2)
        self.match_by_filename_only_check = ttk.Checkbutton(
            col1, text="Apenas Nome (Ignorar Estrutura)",
            variable=self.match_by_filename_only)
        self.match_by_filename_only_check.pack(anchor="w", pady=2)

        # ── Dicionário Único ─────────────────────────────────────────────────
        sep_frame = tk.Frame(col1, bg=C["border"], height=1)
        sep_frame.pack(fill="x", pady=(6, 4))

        unified_row = tk.Frame(col1, bg=C["surface"])
        unified_row.pack(anchor="w")

        # Badge colorido ao lado do label para destacar a opção
        badge = tk.Label(unified_row, text=" NOVO ", bg=C["accent"],
                         fg="#FFFFFF", font=("Segoe UI", 7, "bold"),
                         padx=3, pady=0)
        badge.pack(side="left", padx=(0, 5))

        self.unified_dict_check = ttk.Checkbutton(
            unified_row,
            text="Dicionário Único (todos A/B → todos C)",
            variable=self.unified_dict,
            command=self._toggle_unified_dict)
        self.unified_dict_check.pack(side="left", anchor="w")

        # Label de descrição sutil abaixo do checkbox
        tk.Label(col1,
                 text="Mescla todos os pares A/B num só dicionário",
                 bg=C["surface"], fg=C["text_dim"],
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", padx=(0, 0), pady=(1, 0))

        # Coluna 2: modo de mapeamento
        col2 = tk.Frame(opts_body, bg=C["surface"])
        col2.pack(side="left", padx=(0, 24))
        tk.Label(col2, text="Modo de Mapeamento", bg=C["surface"],
                 fg=C["text_dim"], font=("Segoe UI", 8, "bold")).pack(anchor="w")
        rb_frame = tk.Frame(col2, bg=C["surface"])
        rb_frame.pack(anchor="w")
        ttk.Radiobutton(rb_frame, text="Conteúdo",
                         variable=self.mapping_mode, value="content").pack(side="left")
        ttk.Radiobutton(rb_frame, text="Posicional",
                         variable=self.mapping_mode, value="positional").pack(side="left", padx=8)

        self.validate_check = ttk.Checkbutton(col2,
            text="Validar similaridade na posição",
            variable=self.validate_positional)
        self.validate_check.pack(anchor="w", pady=2)

        # Coluna 3: ignorar prefixos
        col3 = tk.Frame(opts_body, bg=C["surface"])
        col3.pack(side="left", padx=(0, 24))
        tk.Label(col3, text="Ignorar linhas com prefixo",
                 bg=C["surface"], fg=C["text_dim"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        pfx_row = tk.Frame(col3, bg=C["surface"])
        pfx_row.pack(anchor="w", pady=4)
        pfx_entry = tk.Entry(pfx_row, textvariable=self.ignore_prefixes, width=10,
                              bg=C["surface2"], fg=C["text"], insertbackground=C["text"],
                              relief="flat", bd=4, font=("Segoe UI", 9))
        pfx_entry.pack(side="left")
        tk.Label(pfx_row, text=" ex: ;  //", bg=C["surface"], fg=C["text_dim"],
                 font=("Segoe UI", 8)).pack(side="left", padx=4)

        # Coluna 4 (direita): fuzzy slider
        col4 = tk.Frame(opts_body, bg=C["surface"])
        col4.pack(side="right")
        tk.Label(col4, text="Limiar de Similaridade (Fuzzy)",
                 bg=C["surface"], fg=C["text_dim"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        sl_row = tk.Frame(col4, bg=C["surface"])
        sl_row.pack(anchor="w", pady=4)

        self.fuzzy_val_label = tk.Label(sl_row, text="100%", bg=C["surface"],
                                         fg=C["accent"], font=("Segoe UI", 12, "bold"),
                                         width=5, anchor="e")
        self.fuzzy_val_label.pack(side="right", padx=(8, 0))

        self.fuzzy_scale = ttk.Scale(sl_row, from_=0, to=100,
                                      orient="horizontal",
                                      variable=self.fuzzy_threshold, length=180,
                                      command=self._update_fuzzy_label)
        self.fuzzy_scale.pack(side="left")

        self.mapping_mode.trace_add("write", self._update_mode_options)

        # ── Painel central: lista + treeview ─────────────────────────────────
        paned = ttk.PanedWindow(main, orient="horizontal")
        paned.pack(fill="both", expand=True, pady=(0, 10))

        # Lista de arquivos
        list_outer = tk.Frame(paned, bg=C["surface"])
        list_hdr = tk.Frame(list_outer, bg=C["surface"], padx=10, pady=6)
        list_hdr.pack(fill="x")
        tk.Label(list_hdr, text="📁  ARQUIVOS A/B MAPEADOS",
                 bg=C["surface"], fg=C["accent"],
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Frame(list_outer, bg=C["border"], height=1).pack(fill="x", padx=10)

        list_inner = tk.Frame(list_outer, bg=C["surface"], padx=8, pady=8)
        list_inner.pack(fill="both", expand=True)

        listbox_scroll = ttk.Scrollbar(list_inner, orient="vertical")
        self.files_listbox = tk.Listbox(
            list_inner,
            font=("Segoe UI", 9),
            bg=C["surface"], fg=C["text"],
            selectbackground=C["tree_sel"], selectforeground=C["text"],
            relief="flat", bd=0, activestyle="none",
            yscrollcommand=listbox_scroll.set,
            highlightthickness=0)
        listbox_scroll.config(command=self.files_listbox.yview)
        listbox_scroll.pack(side="right", fill="y")
        self.files_listbox.pack(fill="both", expand=True)
        self.files_listbox.bind("<<ListboxSelect>>", self._on_file_select)
        paned.add(list_outer, weight=1)

        # Preview / Treeview
        tree_outer = tk.Frame(paned, bg=C["surface"])
        tree_hdr = tk.Frame(tree_outer, bg=C["surface"], padx=10, pady=6)
        tree_hdr.pack(fill="x")
        tk.Label(tree_hdr, text="📖  PREVIEW DO DICIONÁRIO",
                 bg=C["surface"], fg=C["accent"],
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Frame(tree_outer, bg=C["border"], height=1).pack(fill="x", padx=10)

        tree_inner = tk.Frame(tree_outer, bg=C["surface"], padx=8, pady=8)
        tree_inner.pack(fill="both", expand=True)

        tree_scroll_y = ttk.Scrollbar(tree_inner, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(tree_inner, orient="horizontal")
        self.tree = ttk.Treeview(tree_inner,
                                  columns=("idx", "orig", "trans"),
                                  show="headings",
                                  yscrollcommand=tree_scroll_y.set,
                                  xscrollcommand=tree_scroll_x.set)
        for col, txt, w, anchor in [
            ("idx",  "№",            50,  "center"),
            ("orig", "Original (A)", 340, "w"),
            ("trans","Tradução (B)", 340, "w"),
        ]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w, anchor=anchor, minwidth=40)

        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)
        paned.add(tree_outer, weight=3)

        # ── Progress Bar ─────────────────────────────────────────────────────
        prog_row = tk.Frame(main, bg=C["bg"])
        prog_row.pack(fill="x", pady=(0, 6))

        self.progress_label = tk.Label(prog_row, text="Aguardando...",
                                        bg=C["bg"], fg=C["text_dim"],
                                        font=("Segoe UI", 8))
        self.progress_label.pack(side="left", padx=(0, 10))

        self.progress = ModernProgressBar(prog_row, height=8)
        self.progress.pack(side="left", fill="x", expand=True)
        self._progress_bars.append(self.progress)

        self.progress_pct = tk.Label(prog_row, text="0%",
                                      bg=C["bg"], fg=C["accent"],
                                      font=("Segoe UI", 8, "bold"), width=5)
        self.progress_pct.pack(side="left", padx=(8, 0))

        # ── Console de Log ───────────────────────────────────────────────────
        log_outer = tk.Frame(main, bg=C["surface"])
        log_outer.pack(fill="x")

        log_hdr = tk.Frame(log_outer, bg=C["surface"], padx=10, pady=5)
        log_hdr.pack(fill="x")
        tk.Label(log_hdr, text="⬛  CONSOLE", bg=C["surface"],
                 fg=C["accent"], font=("Segoe UI", 8, "bold")).pack(side="left")

        clear_btn = self._make_modern_btn(log_hdr, "Limpar",
                                          command=self._clear_log,
                                          style="secondary", width=70, height=22,
                                          font_size=7)
        clear_btn.pack(side="right")

        tk.Frame(log_outer, bg=C["border"], height=1).pack(fill="x", padx=10)

        log_inner = tk.Frame(log_outer, bg=C["log_bg"], padx=6, pady=6)
        log_inner.pack(fill="x")

        log_scroll = ttk.Scrollbar(log_inner, orient="vertical")
        self.log_text = tk.Text(
            log_inner, height=7, state="disabled",
            font=("Consolas", 9),
            bg=C["log_bg"], fg=C["text"],
            insertbackground=C["text"],
            relief="flat", bd=0,
            selectbackground=C["accent"],
            highlightthickness=0,
            yscrollcommand=log_scroll.set)
        log_scroll.config(command=self.log_text.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_text.pack(fill="x")

        # Tags de cor por nível
        self.log_text.tag_config("INFO",  foreground=C["log_info"])
        self.log_text.tag_config("WARN",  foreground=C["log_warn"])
        self.log_text.tag_config("ERROR", foreground=C["log_error"])
        self.log_text.tag_config("OK",    foreground=C["log_ok"])
        self.log_text.tag_config("DIM",   foreground=C["text_dim"])

        # ── Status Bar ───────────────────────────────────────────────────────
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", side="bottom")
        self.status_bar = tk.Frame(self, bg=C["surface2"], pady=4)
        self.status_bar.pack(fill="x", side="bottom")

        self.status_label = tk.Label(
            self.status_bar,
            text="  ●  Pronto  •  0 arquivos mapeados  •  0 processados",
            bg=C["surface2"], fg=C["text_dim"],
            font=("Segoe UI", 8))
        self.status_label.pack(side="left", padx=12)

        self.version_label = tk.Label(
            self.status_bar, text="Text Mapper Pro  v1.5.0  ",
            bg=C["surface2"], fg=C["text_dim"],
            font=("Segoe UI", 8))
        self.version_label.pack(side="right", padx=12)

    # ── Log ──────────────────────────────────────────────────────────────────
    def _log(self, message, level="INFO"):
        self.log_text.config(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{ts}] [{level:5s}]  "
        self.log_text.insert("end", prefix, "DIM")
        self.log_text.insert("end", message + "\n", level)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def _update_status(self):
        mode = "Conteúdo" if self.mapping_mode.get() == "content" else "Posicional"
        txt = (f"  ●  {mode}  •  "
               f"{self._status_mapped} arquivos mapeados  •  "
               f"{self._status_processed} processados")
        self.status_label.configure(text=txt)

    def _update_progress(self, val, maximum):
        self.progress.config(maximum=maximum, value=val)
        pct = int(val / maximum * 100) if maximum else 0
        self.progress_pct.configure(text=f"{pct}%")

    # ── Interação ─────────────────────────────────────────────────────────────
    def _select_folder(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(path)

    def _get_pattern(self):
        ext = self.file_extension.get().strip()
        if not ext.startswith("."): ext = "." + ext
        return f"**/*{ext}" if self.recursive_search.get() else f"*{ext}"

    def _update_fuzzy_label(self, val):
        self.fuzzy_val_label.configure(text=f"{float(val):.0f}%")

    def _update_mode_options(self, *args):
        mode = self.mapping_mode.get()
        if mode == "positional":
            self.validate_check.config(state="normal",
                                        text="Validar similaridade na posição (usar limiar)")
        else:
            self.validate_check.config(state="disabled",
                                        text="Validar orig. em C")
        self.fuzzy_scale.config(state="normal")
        self._update_status()

    def _toggle_brute_force(self):
        if self.brute_force_by_order.get():
            self.match_by_filename_only_check.config(state="disabled")
            self.match_by_filename_only.set(True)
            self._log("Modo Brute Force ativado: usando ORDEM dos arquivos", "WARN")
        else:
            self.match_by_filename_only_check.config(state="normal")

    def _toggle_unified_dict(self):
        """Ativa/desativa Dicionário Único e atualiza o status."""
        if self.unified_dict.get():
            # Dicionário Único é só útil no modo conteúdo; avisa se for posicional
            if self.mapping_mode.get() == "positional":
                self._log(
                    "Dicionário Único funciona melhor no modo Conteúdo.", "WARN")
            self._log(
                "Dicionário Único ativado: todos os pares A/B serão mesclados "
                "e aplicados a todos os arquivos em C.", "INFO")
            # Desabilita opções de correspondência que são irrelevantes
            self.match_by_filename_only_check.config(state="disabled")
        else:
            self._log("Dicionário Único desativado.", "INFO")
            if not self.brute_force_by_order.get():
                self.match_by_filename_only_check.config(state="normal")

    # ── Leitura de arquivo ────────────────────────────────────────────────────
    def _read_file(self, path, fallback_var, force_encoding=None):
        try:
            if force_encoding is not None:
                with open(path, "r", encoding=force_encoding) as f:
                    return f.read().splitlines(keepends=True)
            with open(path, "rb") as f:
                raw = f.read()
        except Exception as e:
            self._log(f"Erro ao ler {path}: {e}", "ERROR")
            return ["<ERRO>\n"]

        if not raw: return ["\n"]

        bom_map = {b"\xef\xbb\xbf": "utf-8-sig",
                   b"\xff\xfe":     "utf-16-le",
                   b"\xfe\xff":     "utf-16-be"}
        for bom, enc in bom_map.items():
            if raw.startswith(bom):
                try: return raw.decode(enc).splitlines(keepends=True)
                except: pass

        detector = chardet.UniversalDetector()
        for line in raw.splitlines(keepends=True)[:200]:
            detector.feed(line)
            if detector.done: break
        detector.close()

        if detector.result["encoding"] and detector.result["confidence"] > 0.8:
            try: return raw.decode(detector.result["encoding"]).splitlines(keepends=True)
            except: pass

        for enc in ["utf-8", "cp1252", "utf-16", "latin-1", fallback_var.get().lower()]:
            try: return raw.decode(enc).splitlines(keepends=True)
            except: continue

        return raw.decode("utf-8", errors="replace").splitlines(keepends=True)

    def _should_ignore(self, line, prefixes):
        if not prefixes: return False
        stripped = line.lstrip()
        for p in prefixes:
            if p and stripped.startswith(p): return True
        return False

    # ── Build Mappings ────────────────────────────────────────────────────────
    def build_mappings(self):
        if not self.folder_a.get() or not self.folder_b.get():
            messagebox.showerror("Erro", "Selecione as pastas A e B.")
            return

        pattern = self._get_pattern()
        mode    = self.mapping_mode.get()
        prefixes= self.ignore_prefixes.get().split()

        self.btn_build.config_state("disabled")
        self.files_listbox.delete(0, "end")
        self.tree.delete(*self.tree.get_children())
        self.mappings.clear()
        self.mappings_by_name.clear()
        self.mappings_list = []
        self.global_mapping = {}   # Resetar dicionário único
        self._status_mapped = 0

        self.progress_label.configure(text="Construindo mapeamentos...")
        self._log("Iniciando construção dos mapeamentos A↔B...", "INFO")

        def worker():
            path_a = Path(self.folder_a.get())
            path_b = Path(self.folder_b.get())
            files_a = {f.relative_to(path_a).as_posix().lower(): f
                       for f in path_a.glob(pattern)}
            files_b = {f.relative_to(path_b).as_posix().lower(): f
                       for f in path_b.glob(pattern)}

            common = sorted(set(files_a.keys()) & set(files_b.keys()), key=str.lower)
            total  = len(common)
            self.after(0, lambda: self._update_progress(0, total or 1))

            self.mappings_list = []

            for i, rel_lower in enumerate(common):
                file_a = files_a[rel_lower]
                file_b = files_b[rel_lower]
                rel    = file_a.relative_to(path_a).as_posix()

                lines_a = self._read_file(file_a, self.encoding_ab)
                lines_b = self._read_file(file_b, self.encoding_ab)

                mapping = []
                for la, lb in zip(lines_a, lines_b):
                    orig  = la.rstrip("\n\r")
                    trans = lb.rstrip("\n\r")
                    if self._should_ignore(orig, prefixes): continue
                    mapping.append({"orig": orig, "trans": trans})

                if mode == "content":
                    content_map = {}
                    for item in mapping:
                        if item["trans"] is not None:
                            v = item["trans"]
                            content_map[item["orig"]] = v + "\n" if not v.endswith("\n") else v
                    self.mappings[rel_lower]      = content_map
                    self.mappings_list.append(content_map)
                else:
                    self.mappings[rel_lower] = mapping
                    self.mappings_list.append(mapping)

                fname_lower = Path(rel).name.lower()
                if fname_lower not in self.mappings_by_name:
                    self.mappings_by_name[fname_lower] = self.mappings[rel_lower]

                # Acumular no dicionário único (modo conteúdo)
                if mode == "content":
                    self.global_mapping.update(self.mappings[rel_lower])

                tag = "odd" if i % 2 == 0 else "even"
                self.after(0, lambda d=rel, t=tag: self.files_listbox.insert("end", d))
                self.after(0, lambda v=i+1, mx=total: self._update_progress(v, mx or 1))

            self.after(0, self._build_finished)

        threading.Thread(target=worker, daemon=True).start()

    def _build_finished(self):
        self.btn_build.config_state("normal")
        if self.mappings:
            self.btn_apply.config_state("normal")
        self._status_mapped = len(self.mappings)
        self._status_processed = 0
        self._update_status()
        self.progress_label.configure(text="Mapeamento concluído.")
        self._log(f"Concluído: {len(self.mappings)} arquivo(s) mapeado(s).", "OK")
        messagebox.showinfo("Sucesso",
                            f"Dicionários criados!\n{len(self.mappings)} arquivo(s) mapeado(s).")

    def _on_file_select(self, event):
        sel = self.files_listbox.curselection()
        if not sel: return
        fname   = self.files_listbox.get(sel[0])
        mapping = self.mappings.get(fname.lower())
        if not mapping: return

        mode = self.mapping_mode.get()
        self.tree.delete(*self.tree.get_children())

        if mode == "content" and isinstance(mapping, dict):
            for idx, (orig, trans) in enumerate(mapping.items(), 1):
                tag = "odd" if idx % 2 == 0 else "even"
                self.tree.insert("", "end", values=(idx, orig, trans), tags=(tag,))
        else:
            if isinstance(mapping, dict):
                mapping = [{"orig": k, "trans": v} for k, v in mapping.items()]
            for idx, item in enumerate(mapping, 1):
                trans = item["trans"]
                if trans is None:        trans = "[SEM TRADUÇÃO]"
                elif not trans.endswith("\n"): trans = trans + "\n"
                tag = "odd" if idx % 2 == 0 else "even"
                self.tree.insert("", "end", values=(idx, item["orig"], trans), tags=(tag,))

        self._apply_treeview_stripes()

    # ── Apply Mappings ────────────────────────────────────────────────────────
    def apply_mappings(self):
        if not self.folder_c.get():
            messagebox.showerror("Erro", "Selecione a pasta C.")
            return

        parent_dir   = Path(self.folder_c.get()).parent
        out_dir_name = Path(self.folder_c.get()).name + "_TRA"
        out_dir      = parent_dir / out_dir_name
        out_dir.mkdir(exist_ok=True)
        report_path  = parent_dir / f"relatorio_{out_dir_name}.txt"

        self.btn_apply.config_state("disabled")
        mode        = self.mapping_mode.get()
        by_name     = self.match_by_filename_only.get()
        threshold   = self.fuzzy_threshold.get() / 100.0
        brute_force = self.brute_force_by_order.get()
        use_unified = self.unified_dict.get()
        prefixes    = self.ignore_prefixes.get().split()

        self.progress_label.configure(text="Aplicando traduções em C...")

        if use_unified:
            n = len(self.global_mapping)
            self._log(f"Dicionário Único ativo: {n} entradas mescladas de todos os pares A/B.", "INFO")
        else:
            self._log("Iniciando aplicação em C...", "INFO")

        def worker():
            pattern     = self._get_pattern()
            files_c     = sorted(Path(self.folder_c.get()).glob(pattern),
                                  key=lambda x: x.name.lower())
            total       = len(files_c)
            untranslated= {}
            processed   = 0

            self.after(0, lambda: self._update_progress(0, total or 1))

            force_enc_c = self.encoding_c_out.get() if self.force_encoding_c.get() else None
            if force_enc_c:
                self._log(f"Forçando codificação em C: {force_enc_c}", "WARN")

            for i, file_c in enumerate(files_c):
                rel       = file_c.relative_to(Path(self.folder_c.get())).as_posix()
                rel_lower = rel.lower()

                if use_unified:
                    # Dicionário único: um só dict para todos os arquivos C
                    mapping = self.global_mapping if self.global_mapping else None
                    if not mapping:
                        self._log(
                            f"Dicionário único vazio! Reconstrua os mapeamentos.", "ERROR")
                elif brute_force:
                    mapping = self.mappings_list[i] if i < len(self.mappings_list) else None
                    if not mapping:
                        self._log(f"Sem mapeamento para '{rel}' (índice {i})", "WARN")
                else:
                    mapping = (self.mappings_by_name.get(file_c.name.lower()) if by_name
                               else self.mappings.get(rel_lower))

                lines_c                   = self._read_file(file_c, self.encoding_c_out, force_enc_c)
                output, issues_fail, issues_fuzzy = [], [], []

                if not mapping:
                    output = [line.rstrip("\r\n") + "\n" for line in lines_c]
                    issues_fail.append("[!] Sem mapeamento encontrado.")
                else:
                    if mode == "content":
                        if isinstance(mapping, list):
                            content_map = {}
                            for item in mapping:
                                if item["trans"] is not None:
                                    v = item["trans"]
                                    content_map[item["orig"]] = v + "\n" if not v.endswith("\n") else v
                            mapping = content_map
                        keys = list(mapping.keys())
                        for idx, line in enumerate(lines_c, 1):
                            s = line.rstrip("\r\n")
                            if not s or self._should_ignore(line, prefixes):
                                output.append(s + "\n"); continue
                            if s in mapping:
                                output.append(mapping[s]); continue
                            if threshold < 1.0:
                                matches = difflib.get_close_matches(s, keys, n=1, cutoff=threshold)
                                if matches:
                                    best = matches[0]
                                    sim  = difflib.SequenceMatcher(None, s, best).ratio()
                                    output.append(mapping[best])
                                    issues_fuzzy.append(
                                        f'L{idx}: [FUZZY {sim*100:.0f}%] "{s}" → "{best}"')
                                    continue
                            output.append(s + "\n")
                            issues_fail.append(f'L{idx}: [FALHA] "{s}"')
                    else:
                        if isinstance(mapping, dict):
                            mapping = [{"orig": k, "trans": v} for k, v in mapping.items()]
                        for idx, line in enumerate(lines_c, 1):
                            s = line.rstrip("\r\n")
                            if not s or self._should_ignore(line, prefixes):
                                output.append(s + "\n"); continue
                            map_idx = idx - 1
                            if map_idx < len(mapping):
                                item   = mapping[map_idx]
                                orig_s = item["orig"].strip() if item["orig"] else ""
                                if not self.validate_positional.get():
                                    t = item["trans"]
                                    output.append(t + "\n" if t and not t.endswith("\n")
                                                  else (t or s + "\n"))
                                else:
                                    sim = difflib.SequenceMatcher(None, s, orig_s).ratio()
                                    if sim >= threshold:
                                        t = item["trans"]
                                        output.append(t + "\n" if t and not t.endswith("\n")
                                                      else (t or s + "\n"))
                                        if sim < 1.0:
                                            issues_fuzzy.append(
                                                f'L{idx}: [FUZZY POSICIONAL {sim*100:.0f}%]')
                                    else:
                                        output.append(s + "\n")
                                        issues_fail.append(
                                            f'L{idx}: [FALHA POSICIONAL {sim*100:.0f}%]')
                            else:
                                output.append(s + "\n")
                                issues_fail.append(f"L{idx}: [FORA DE ÍNDICE]")

                out_file = out_dir / rel
                out_file.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with open(out_file, "w", encoding=self.encoding_c_out.get()) as f:
                        f.writelines(output)
                    processed += 1
                except Exception as e:
                    self._log(f"Erro ao salvar {out_file}: {e}", "ERROR")

                if issues_fail or issues_fuzzy:
                    untranslated[rel] = issues_fail + issues_fuzzy

                self.after(0, lambda v=i+1, mx=total: self._update_progress(v, mx or 1))

            # Relatório
            with open(report_path, "w", encoding="utf-8") as r:
                brute_str    = "Sim" if brute_force else "Não"
                unified_str  = "Sim" if use_unified else "Não"
                validate_str = "Sim" if self.validate_positional.get() else "Não"
                r.write(f"# RELATÓRIO v1.5.0 - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                r.write(f"# Modo: {mode.capitalize()} | Validar: {validate_str} | "
                        f"Limiar: {threshold*100:.0f}% | Busca: "
                        f"{'Nome' if by_name else 'Estrutura'}\n")
                r.write(f"# Brute Force: {brute_str} | Dicionário Único: {unified_str} | "
                        f"Ignorar Prefixos: {' '.join(prefixes) or 'Nenhum'}\n")
                r.write(f"# A/B mapeados: {len(self.mappings_list)} | "
                        f"C processados: {len(files_c)}\n")
                r.write(f"# Codificação A/B: {self.encoding_ab.get()} | "
                        f"Saída: {self.encoding_c_out.get()}\n")
                r.write(f"# Pasta de Saída: {out_dir_name}\n")
                r.write("# " + "=" * 80 + "\n\n")
                if untranslated:
                    r.write(f"# ARQUIVOS COM PROBLEMAS ({len(untranslated)}):\n")
                    for p, iss in untranslated.items():
                        r.write(f"\nARQUIVO: {p}\n")
                        for item in iss:
                            if any(t in item for t in ["[FALHA", "[FORA DE ÍNDICE]", "[!]"]):
                                r.write(f"  {item}\n")
                        for item in iss:
                            if "[FUZZY" in item:
                                r.write(f"  {item}\n")
                        r.write("-" * 40 + "\n")
                else:
                    r.write("# TODOS OS ARQUIVOS FORAM TRADUZIDOS COM SUCESSO!\n")
                r.write(f"\n# Total processados: {processed}\n")
                r.write(f"# Com problemas: {len(untranslated)}\n")
                if use_unified:
                    r.write(f"\n# NOTA: Dicionário Único foi usado.\n")
                    r.write(f"# Um único dicionário com {len(self.global_mapping)} entradas "
                            f"# foi aplicado a todos os {len(files_c)} arquivo(s) em C.\n")
                if brute_force:
                    r.write("\n# NOTA: Modo Brute Force (ORDEM) foi usado.\n")

            self.after(0, lambda: self._apply_finished(processed, out_dir, report_path))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_finished(self, count, out_dir, report):
        self.btn_apply.config_state("normal")
        self._last_report_path = report      # guarda para o botão 3
        self._last_out_dir     = out_dir
        self.btn_report.config_state("normal")
        self._status_processed = count
        self._update_status()
        self.progress_label.configure(text=f"Concluído — {count} arquivo(s) processado(s).")
        self._log(f"Tradução finalizada: {count} arquivo(s). Saída: {out_dir}", "OK")
        messagebox.showinfo("Concluído!",
                            f"Tradução finalizada!\n{count} arquivo(s) processado(s).\n\n"
                            f"Relatório:\n{report}\n\nArquivos em:\n{out_dir}")

    # ── Aplicar Relatório (Botão 3) ───────────────────────────────────────────
    def apply_report(self):
        """Lê o relatório de FALHAs, abre editor linha a linha e reaplica."""
        # ── 1. Determinar arquivo de relatório ────────────────────────────────
        report_path = getattr(self, '_last_report_path', None)
        out_dir     = getattr(self, '_last_out_dir',     None)

        if not report_path or not Path(report_path).exists():
            # Deixa o usuário escolher manualmente
            report_path = filedialog.askopenfilename(
                title="Selecione o arquivo de relatório",
                filetypes=[("Arquivos de texto", "*.txt"), ("Todos", "*.*")])
            if not report_path:
                return
            report_path = Path(report_path)
        else:
            report_path = Path(report_path)

        # ── 2. Parsear relatório ──────────────────────────────────────────────
        try:
            content = report_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ler o relatório:\n{e}")
            return

        # Extrair: pasta de saída (linha "# Pasta de Saída: ...") e codificação de saída
        out_enc   = "utf-8"
        out_dir_r = None
        for line in content.splitlines():
            if line.startswith("# Pasta de Saída:"):
                out_dir_r = line.split(":", 1)[1].strip()
            if line.startswith("# Codificação A/B:"):
                # "# Codificação A/B: utf-8 | Saída: utf-8"
                parts = line.split("|")
                for p in parts:
                    if "Saída:" in p:
                        out_enc = p.split(":", 1)[1].strip()

        # Se não achou no relatório, usa o armazenado
        if out_dir is None and out_dir_r:
            # Tenta resolver relativo ao relatório
            out_dir = report_path.parent / out_dir_r
        elif out_dir is None:
            out_dir = filedialog.askdirectory(title="Selecione a pasta de saída (_TRA)")
            if not out_dir:
                return
            out_dir = Path(out_dir)
        else:
            out_dir = Path(out_dir)

        if not out_dir.exists():
            # Tenta resolver pelo diretório do relatório
            out_dir = report_path.parent / out_dir.name
            if not out_dir.exists():
                messagebox.showerror("Erro", f"Pasta de saída não encontrada:\n{out_dir}")
                return

        # ── 3. Extrair blocos de FALHA ────────────────────────────────────────
        # Formato:
        #   ARQUIVO: msg_eng_00.txt
        #     L66: [FALHA] "texto original"
        import re
        fail_pattern = re.compile(r'L(\d+): \[FALHA[^]]*\] "(.+)"')
        blocks = {}   # {rel_path: [(line_num, orig_text), ...]}
        current_file = None
        for line in content.splitlines():
            line = line.rstrip()
            if line.startswith("ARQUIVO:"):
                current_file = line[len("ARQUIVO:"):].strip()
                blocks[current_file] = []
            elif current_file:
                m = fail_pattern.search(line)
                if m:
                    lnum = int(m.group(1))
                    orig = m.group(2)
                    blocks[current_file].append((lnum, orig))

        # Remove arquivos sem falhas
        blocks = {k: v for k, v in blocks.items() if v}

        if not blocks:
            messagebox.showinfo("Relatório", "Nenhuma linha com [FALHA] encontrada no relatório.")
            return

        total_fails = sum(len(v) for v in blocks.values())
        self._log(f"Relatório: {len(blocks)} arquivo(s) com {total_fails} FALHA(s) encontradas.", "WARN")

        # ── 4. Janela de edição ───────────────────────────────────────────────
        self._open_report_editor(blocks, out_dir, out_enc, report_path)

    def _open_report_editor(self, blocks, out_dir, out_enc, report_path):
        """Janela modal para editar as traduções das linhas com FALHA."""
        C = self._C
        win = tk.Toplevel(self)
        win.title("Aplicar Relatório — Corrigir FALHAs")
        win.geometry("900x640")
        win.configure(bg=C["bg"])
        win.grab_set()

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(win, bg=C["accent"], padx=16, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📋  Corrigir Traduções com FALHA",
                 bg=C["accent"], fg="#FFFFFF",
                 font=("Segoe UI", 12, "bold")).pack(side="left")
        total_f = sum(len(v) for v in blocks.values())
        tk.Label(hdr, text=f"{len(blocks)} arquivo(s)  •  {total_f} FALHA(s)",
                 bg=C["accent"], fg="#FFFFFF",
                 font=("Segoe UI", 9)).pack(side="right")

        # ── Instrução ─────────────────────────────────────────────────────────
        info = tk.Frame(win, bg=C["surface"], padx=14, pady=8)
        info.pack(fill="x")
        tk.Label(info, bg=C["surface"], fg=C["text_dim"],
                 font=("Segoe UI", 8),
                 text=("Para cada linha com FALHA, edite a coluna \"Tradução Corrigida\" "
                       "e clique em  Aplicar Correções.")).pack(anchor="w")
        tk.Frame(win, bg=C["border"], height=1).pack(fill="x")

        # ── Tabela de edição ──────────────────────────────────────────────────
        tbl_frame = tk.Frame(win, bg=C["bg"])
        tbl_frame.pack(fill="both", expand=True, padx=10, pady=8)

        cols = ("arquivo", "linha", "original", "traducao")
        tv = ttk.Treeview(tbl_frame, columns=cols, show="headings", selectmode="browse")
        tv.heading("arquivo",  text="Arquivo")
        tv.heading("linha",    text="L#")
        tv.heading("original", text="Texto Original (FALHOU)")
        tv.heading("traducao", text="Tradução Corrigida")
        tv.column("arquivo",  width=150, minwidth=80)
        tv.column("linha",    width=50,  minwidth=40,  anchor="center")
        tv.column("original", width=320, minwidth=120)
        tv.column("traducao", width=320, minwidth=120)

        sy = ttk.Scrollbar(tbl_frame, orient="vertical",   command=tv.yview)
        sx = ttk.Scrollbar(tbl_frame, orient="horizontal",  command=tv.xview)
        tv.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        tv.pack(fill="both", expand=True)

        # Popula treeview + guarda dados editáveis
        # edit_data[iid] = {"file": str, "lnum": int, "orig": str, "trans": tk.StringVar}
        edit_data = {}
        for fname, items in blocks.items():
            for lnum, orig in items:
                iid = tv.insert("", "end",
                                values=(fname, lnum, orig, orig))
                sv = tk.StringVar(value=orig)
                edit_data[iid] = {"file": fname, "lnum": lnum,
                                  "orig": orig, "trans": sv}

        # ── Painel de edição inline ───────────────────────────────────────────
        edit_bar = tk.Frame(win, bg=C["surface"], padx=12, pady=8)
        edit_bar.pack(fill="x")
        tk.Label(edit_bar, text="Tradução:", bg=C["surface"], fg=C["text"],
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 6))
        current_var = tk.StringVar()
        edit_entry = tk.Entry(edit_bar, textvariable=current_var, width=70,
                              bg=C["surface2"], fg=C["text"],
                              insertbackground=C["text"],
                              relief="flat", bd=4, font=("Segoe UI", 9))
        edit_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        current_iid = [None]   # lista para mutabilidade no closure

        def on_select(event):
            sel = tv.selection()
            if not sel:
                return
            iid = sel[0]
            current_iid[0] = iid
            d = edit_data[iid]
            current_var.set(d["trans"].get())
            edit_entry.focus_set()
            edit_entry.selection_range(0, "end")

        def on_entry_change(*_):
            iid = current_iid[0]
            if iid and iid in edit_data:
                val = current_var.get()
                edit_data[iid]["trans"].set(val)
                # Atualiza visual na treeview
                row = tv.item(iid, "values")
                tv.item(iid, values=(row[0], row[1], row[2], val))

        tv.bind("<<TreeviewSelect>>", on_select)
        current_var.trace_add("write", on_entry_change)

        def save_entry(event=None):
            """Confirma edição e avança para próximo item."""
            on_entry_change()
            sel = tv.selection()
            if not sel:
                return
            cur = sel[0]
            children = tv.get_children()
            idx = children.index(cur)
            if idx + 1 < len(children):
                nxt = children[idx + 1]
                tv.selection_set(nxt)
                tv.see(nxt)

        edit_entry.bind("<Return>", save_entry)
        edit_entry.bind("<Tab>",    save_entry)

        # ── Botões de ação ────────────────────────────────────────────────────
        btn_row = tk.Frame(win, bg=C["bg"], pady=10)
        btn_row.pack(fill="x", padx=10)

        status_lbl = tk.Label(btn_row, text="", bg=C["bg"], fg=C["text_dim"],
                              font=("Segoe UI", 8))
        status_lbl.pack(side="left", padx=(0, 16))

        def do_apply():
            """Reaplica as traduções corrigidas nos arquivos _TRA."""
            applied = 0
            errors  = 0
            # Agrupa correções por arquivo
            corrections = {}  # {fname: {lnum: new_trans}}
            for iid, d in edit_data.items():
                f = d["file"]
                ln = d["lnum"]
                t  = d["trans"].get().strip()
                corrections.setdefault(f, {})[ln] = t

            for fname, line_map in corrections.items():
                file_path = out_dir / fname
                if not file_path.exists():
                    self._log(f"Arquivo não encontrado para corrigir: {file_path}", "ERROR")
                    errors += 1
                    continue
                try:
                    lines = file_path.read_text(encoding=out_enc,
                                                errors="replace").splitlines(keepends=True)
                    for lnum, new_trans in line_map.items():
                        idx = lnum - 1
                        if 0 <= idx < len(lines):
                            # Preserva o terminador de linha original
                            orig_line = lines[idx]
                            eol = ""
                            if orig_line.endswith("\r\n"): eol = "\r\n"
                            elif orig_line.endswith("\n"): eol = "\n"
                            lines[idx] = new_trans.rstrip("\r\n") + eol
                        else:
                            self._log(f"{fname}: Linha {lnum} fora do intervalo.", "WARN")
                    file_path.write_text("".join(lines), encoding=out_enc)
                    applied += 1
                    self._log(f"Corrigido: {fname} ({len(line_map)} linha(s))", "OK")
                except Exception as e:
                    self._log(f"Erro ao corrigir {fname}: {e}", "ERROR")
                    errors += 1

            msg = f"{applied} arquivo(s) corrigido(s)"
            if errors:
                msg += f", {errors} erro(s)"
            status_lbl.configure(text=msg, fg=C["success"] if not errors else C["error"])
            self._log(f"Aplicação do relatório concluída: {msg}", "OK" if not errors else "WARN")
            messagebox.showinfo("Correção aplicada",
                                f"{msg}\n\nArquivos atualizados em:\n{out_dir}",
                                parent=win)

        apply_btn = self._make_modern_btn(btn_row, "Aplicar Correções",
                                          command=do_apply,
                                          style="action", width=180, height=32, icon="✔")
        apply_btn.pack(side="right", padx=(8, 0))

        close_btn = self._make_modern_btn(btn_row, "Fechar",
                                          command=win.destroy,
                                          style="secondary", width=100, height=32)
        close_btn.pack(side="right")

    # ── Ajuda ─────────────────────────────────────────────────────────────────
    def _show_instructions(self):
        C = self._C
        hw = tk.Toplevel(self)
        hw.title("Ajuda — Text Mapper Pro v1.5.0")
        hw.geometry("680x560")
        hw.configure(bg=C["surface"])
        hw.resizable(True, True)

        # Header da janela de ajuda
        hdr = tk.Frame(hw, bg=C["accent"], padx=20, pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📖  Guia de Uso", bg=C["accent"], fg="#FFFFFF",
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(hdr, text="Text Translation Mapper Pro  v1.5.0",
                 bg=C["accent"], fg="#FFFFFF", font=("Segoe UI", 9)).pack(side="right")

        frame = tk.Frame(hw, bg=C["surface"])
        frame.pack(fill="both", expand=True, padx=16, pady=12)

        scroll = ttk.Scrollbar(frame)
        scroll.pack(side="right", fill="y")

        txt = tk.Text(frame, wrap="word", font=("Segoe UI", 10),
                      bg=C["surface"], fg=C["text"],
                      insertbackground=C["text"],
                      relief="flat", bd=0, highlightthickness=0,
                      padx=8, pady=8,
                      yscrollcommand=scroll.set)
        scroll.config(command=txt.yview)
        txt.pack(fill="both", expand=True)

        txt.tag_config("h1",    foreground=C["accent"],  font=("Segoe UI", 12, "bold"))
        txt.tag_config("h2",    foreground=C["accent2"], font=("Segoe UI", 10, "bold"))
        txt.tag_config("body",  foreground=C["text"],    font=("Segoe UI", 13))
        txt.tag_config("dim",   foreground=C["text_dim"],font=("Segoe UI", 13))
        txt.tag_config("code",  foreground=C["success"],  font=("Consolas", 13),
                       background=C["surface2"])

        instructions = [
            ("h1", "TEXT TRANSLATION MAPPER PRO — v1.5.0\n\n"),
            ("h2", "NOVO NA VERSÃO 1.5.0\n"),
            ("body", "→ Interface completamente redesenhada com tema escuro premium\n"),
            ("body", "→ Console de log com cores por nível (INFO / WARN / ERROR / OK)\n"),
            ("body", "→ Progress bar com porcentagem dinâmica\n\n"),
            ("body", "→ Adicionada funcionalidades extras\n\n"),
            ("h2", "1. CONCEITO DAS PASTAS\n"),
            ("body", "• PASTA A (Originais): Arquivos originais (ex: Inglês).\n"),
            ("body", "• PASTA B (Traduções): Mesmos arquivos traduzidos (ex: Português).\n"),
            ("dim",  "  A e B DEVEM ter os mesmos nomes e mesma quantidade!\n"),
            ("body", "• PASTA C (A Traduzir): Arquivos novos com nomes DIFERENTES.\n\n"),
            ("h2", "2. PASSO A PASSO\n"),
            ("body", "1. Selecione as pastas A, B e C.\n"),
            ("body", "2. Configure a extensão dos arquivos.\n"),
            ("body", "3. Defina prefixos a ignorar, se necessário (ex: "),
            ("code",  "; //"),
            ("body", ").\n"),
            ("body", "4. Se C tiver nomes diferentes de A/B, ative "),
            ("code",  "Brute Force (Ordem)"),
            ("body", ".\n"),
            ("body", "5. Ajuste o Limiar de Fuzzy Match (recomendado: 90%).\n"),
            ("body", "6. Clique em "),
            ("code",  "1. Criar Dicionário"),
            ("body", ".\n"),
            ("body", "7. Clique em "),
            ("code",  "2. Aplicar Dicionário"),
            ("body", ".\n"),
            ("body", "8. Clique em "),
            ("code",  "3. Aplicar Relatório [OPCIONAL]"),
            ("body", ".\n"),
            ("body",  "O passo 8 irá aplicar os textos do relatório nos arquivos traduzidos\n"),
            ("body",  "lhe dando a opção de corrigir somente o necessário rapidamente.\n"),
            ("body", "\n\n"),
            ("h2", "3. MODOS DE MAPEAMENTO\n"),
            ("body", "• Conteúdo: Substitui qualquer linha de C que bata com uma linha de A.\n"),
            ("body", "• Posicional: Substitui pela posição (linha 5 em A/B → linha 5 em C).\n\n"),
            ("h2", "4. FUZZY MATCH\n"),
            ("body", "O Limiar de Similaridade define a % mínima para aceitar uma correspondência\n"),
            ("body", "aproximada. Em 100% só aceita correspondências exatas.\n\n"),
            ("h2", "5. IMPORTANTE\n"),
            ("body", "• A e B DEVEM ter mesma quantidade e mesmos nomes.\n"),
            ("body", "• C DEVE ter mesma quantidade que A/B.\n"),
            ("body", "• A ordem é determinada pela ordenação ALFABÉTICA.\n"),
        ]

        for tag, content in instructions:
            txt.insert("end", content, tag)

        txt.config(state="disabled")


# ─────────────────────────────────────────────────────────────────────────────
#  VERIFICAÇÃO DE INICIALIZAÇÃO (Splash Screen & dummy.bin)
# ─────────────────────────────────────────────────────────────────────────────
def get_app_dir():
    """Retorna o diretório base da aplicação.
    - Quando rodando como EXE (PyInstaller --onefile): usa sys._MEIPASS
      para acessar arquivos embutidos via --add-data (ex: splash.png).
    - Quando rodando como .py: usa o diretório do script.
    O dummy.bin sempre é criado/lido ao lado do EXE (sys.executable.parent).
    """
    if getattr(sys, 'frozen', False):
        return Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def get_exe_dir():
    """Diretório persistente ao lado do EXE (para dummy.bin etc.)."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

class SplashWindow(tk.Tk):
    """Tela de splash estilizada com tema escuro premium para primeira inicialização."""

    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.title("Bem-vindo")
        
        # Forçar tema escuro consistente
        self.configure(bg="#0D1117")
        self._C = DARK # Fornecer acesso às cores escuras caso necessário
        
        self.app_dir = get_app_dir()
        self.image_path = self.app_dir / "splash.png"
        
        self.photo = None
        has_image = False
        
        if self.image_path.exists():
            try:
                self.photo = tk.PhotoImage(file=str(self.image_path))
                has_image = True
            except Exception as e:
                pass

        # Dimensões dinâmicas: se houver imagem, calcula a altura necessária (imagem + botão)
        if has_image:
            img_w = self.photo.width()
            img_h = self.photo.height()
            w = max(500, img_w + 40)
            h = img_h + 130
        else:
            w, h = 500, 360
            
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(False, False)
        
        if has_image:
            self.lbl_img = tk.Label(self, image=self.photo, bg="#0D1117")
            self.lbl_img.pack(pady=(20, 10))
        else:
            self._show_fallback()
            
        # Área do botão inferior (Sempre abaixo da imagem ou do fallback)
        self.btn_frame = tk.Frame(self, bg="#0D1117")
        self.btn_frame.pack(side="bottom", pady=20)
        
        # Botão OK estilizado com hover
        self.btn = tk.Button(
            self.btn_frame, text="OK", command=self._on_ok,
            bg="#7C3AED", fg="#FFFFFF", font=("Segoe UI", 10, "bold"),
            activebackground="#9D5CF8", activeforeground="#FFFFFF",
            relief="flat", bd=0, width=15, height=2, cursor="hand2"
        )
        self.btn.pack()
        
        self.btn.bind("<Enter>", lambda e: self.btn.configure(bg="#9D5CF8"))
        self.btn.bind("<Leave>", lambda e: self.btn.configure(bg="#7C3AED"))

    def _show_fallback(self):
        # Card de fallback estilizado e arredondado simulado
        card = tk.Frame(self, bg="#161B22", padx=20, pady=20,
                        highlightthickness=1, highlightbackground="#30363D")
        card.pack(pady=30, padx=20, fill="both", expand=True)
        
        tk.Label(
            card, text="✨  Text Translation Mapper Pro  ✨",
            bg="#161B22", fg="#7C3AED", font=("Segoe UI", 14, "bold")
        ).pack(pady=(20, 15))
        
        tk.Label(
            card, text="Configurando o ambiente para a primeira execução.\n\n"
                       "Pressione OK para abrir o canal oficial e iniciar a aplicação.",
            bg="#161B22", fg="#E6EDF3", font=("Segoe UI", 9), justify="center"
        ).pack(pady=10)

    def _on_ok(self):
        # 1. Criar dummy.bin ao lado do .exe
        try:
            exe_dir = get_exe_dir()
            with open(exe_dir / "dummy.bin", "wb") as f:
                f.write(b"Text Mapper Pro - Initialized")
        except Exception as e:
            print(f"Erro ao criar dummy.bin: {e}")
            
        # 2. Fechar splash e abrir a janela principal
        self.destroy()
        self.callback()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    def launch_main_app(open_url=False):
        app = TextMapperApp()
        if open_url:
            app.after(600, lambda: webbrowser.open("https://www.image2url.com/r2/default/images/1780009830006-2f6b2d9d-2363-41ee-8455-f4d6f2916b54.png"))
        app.mainloop()

    exe_dir    = get_exe_dir()       # pasta ao lado do .exe (persistente)
    dummy_file = exe_dir / "dummy.bin"

    if dummy_file.exists():
        launch_main_app(open_url=False)
    else:
        splash = SplashWindow(callback=lambda: launch_main_app(open_url=True))
        splash.mainloop()
