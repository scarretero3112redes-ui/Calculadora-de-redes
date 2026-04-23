import tkinter as tk
from tkinter import ttk, messagebox
import math

# ─── COLORES Y ESTILOS ──────────────────────────────────────────────────────
BG_DARK    = "#1a1f2e"
BG_PANEL   = "#232940"
BG_INPUT   = "#2d3350"
BG_TABLE   = "#1e2438"
BG_HEADER  = "#2a3560"
BG_ALTROW  = "#252b44"
ACCENT     = "#4a7fff"
ACCENT2    = "#00c9a7"
TEXT_MAIN  = "#e8ecf5"
TEXT_MUTED = "#8892b0"
TEXT_HEAD  = "#ccd6f6"
TEXT_LABEL = "#a8b2d8"
RED_ERR    = "#ff6b6b"
GOLD       = "#ffd166"
GREEN_OK   = "#06d6a0"

FONT_TITLE  = ("Segoe UI", 20, "bold")
FONT_SUB    = ("Segoe UI", 10)
FONT_LABEL  = ("Segoe UI", 9)
FONT_VALUE  = ("Segoe UI", 10, "bold")
FONT_HEADER = ("Segoe UI", 9, "bold")
FONT_TABLE  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 9)
FONT_BADGE  = ("Segoe UI", 8, "bold")

# ─── LÓGICA DE CÁLCULO ──────────────────────────────────────────────────────
def calcular(ip_str, n_subredes):
    partes = ip_str.strip().split(".")
    if len(partes) != 4:
        raise ValueError("IP inválida")
    octetos = [int(x) for x in partes]
    if any(o < 0 or o > 255 for o in octetos):
        raise ValueError("Octetos fuera de rango")

    oct1 = octetos[0]
    if oct1 < 128:
        clase = "A"; prefijo_red = 8
    elif oct1 < 192:
        clase = "B"; prefijo_red = 16
    else:
        clase = "C"; prefijo_red = 24

    host_red = 2 ** (32 - prefijo_red) - 2

    # broadcast y primeras/últimas IPs de la red base
    base_broadcast = octetos[:3] + [255]
    base_1ra       = octetos[:3] + [1]
    base_ultima    = octetos[:3] + [254]

    # Bits necesarios para subredes
    bits_subred = math.ceil(math.log2(n_subredes)) if n_subredes > 1 else 1
    nuevo_prefijo = prefijo_red + bits_subred
    if nuevo_prefijo > 30:
        raise ValueError(f"Demasiadas subredes para clase {clase}")

    host_por_subred = 2 ** (32 - nuevo_prefijo) - 2
    salto = 2 ** (32 - nuevo_prefijo)

    # Máscara
    mascaras = {
        25: "255.255.255.128",
        26: "255.255.255.192",
        27: "255.255.255.224",
        28: "255.255.255.240",
        29: "255.255.255.248",
        30: "255.255.255.252",
        24: "255.255.255.0",
        16: "255.255.0.0",
        8:  "255.0.0.0",
    }
    mascara = mascaras.get(nuevo_prefijo, "255.255.255.0")

    # Octeto variable
    oct_variable = 4 if prefijo_red == 24 else (3 if prefijo_red == 16 else 2)

    # Generar subredes
    subredes = []
    base = octetos[:] 
    base[3] = 0  # asegurar que empieza en .0

    for i in range(n_subredes):
        offset = i * salto
        # reconstruir IP con offset en el octeto variable
        ip_subred = base[:]
        ip_subred[3] = offset % 256
        extra = offset // 256
        if oct_variable <= 3:
            ip_subred[2] += extra

        id_red     = ".".join(str(x) for x in ip_subred)
        bcast      = ip_subred[:]; bcast[3] = ip_subred[3] + salto - 1
        id_bcast   = ".".join(str(x) for x in bcast)
        primera    = ip_subred[:]; primera[3] += 1
        id_primera = ".".join(str(x) for x in primera)
        ultima     = ip_subred[:]; ultima[3] = bcast[3] - 1
        id_ultima  = ".".join(str(x) for x in ultima)

        # Último octeto en binario del broadcast
        bin_bcast = format(bcast[3], "08b")

        subredes.append({
            "num":      i + 1,
            "id_red":   id_red,
            "primera":  id_primera,
            "ultima":   id_ultima,
            "bcast":    id_bcast,
            "bin_oct":  bin_bcast,
        })

    return {
        "clase":          clase,
        "prefijo_red":    prefijo_red,
        "host_red":       host_red,
        "id_red":         ip_str,
        "broadcast":      ".".join(str(x) for x in base_broadcast),
        "primera_ip":     ".".join(str(x) for x in base_1ra),
        "ultima_ip":      ".".join(str(x) for x in base_ultima),
        "bits_subred":    bits_subred,
        "nuevo_prefijo":  nuevo_prefijo,
        "host_subred":    host_por_subred,
        "mascara":        mascara,
        "salto":          salto,
        "oct_variable":   oct_variable,
        "subredes":       subredes,
        "n_subredes":     n_subredes,
    }

# ─── APLICACIÓN ─────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora de Subredes")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(bg=BG_DARK)
        self.resizable(True, True)
        self._build_ui()

    def _build_ui(self):
        # ── Encabezado ──────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_PANEL, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🌐  Calculadora de Subredes", font=FONT_TITLE,
                 bg=BG_PANEL, fg=TEXT_MAIN).pack(side="left", padx=24)
        tk.Label(hdr, text="IPv4 · VLSM", font=FONT_SUB,
                 bg=BG_PANEL, fg=TEXT_MUTED).pack(side="left", padx=4, pady=6)

        # ── Panel de entrada ────────────────────────────────────────────────
        inp = tk.Frame(self, bg=BG_PANEL, pady=16)
        inp.pack(fill="x", padx=0)

        inner = tk.Frame(inp, bg=BG_PANEL)
        inner.pack(padx=24)

        tk.Label(inner, text="Red Base (IP)", font=FONT_LABEL,
                 bg=BG_PANEL, fg=TEXT_LABEL).grid(row=0, column=0, sticky="w", pady=(0,4))
        self.ip_var = tk.StringVar(value="197.20.5.0")
        ip_entry = tk.Entry(inner, textvariable=self.ip_var, font=("Consolas", 12),
                            bg=BG_INPUT, fg=TEXT_MAIN, insertbackground=TEXT_MAIN,
                            relief="flat", width=18, bd=0)
        ip_entry.grid(row=1, column=0, ipady=7, padx=(0,20))

        tk.Label(inner, text="Nº Subredes", font=FONT_LABEL,
                 bg=BG_PANEL, fg=TEXT_LABEL).grid(row=0, column=1, sticky="w", pady=(0,4))
        self.ns_var = tk.StringVar(value="3")
        ns_entry = tk.Entry(inner, textvariable=self.ns_var, font=("Consolas", 12),
                            bg=BG_INPUT, fg=TEXT_MAIN, insertbackground=TEXT_MAIN,
                            relief="flat", width=8, bd=0)
        ns_entry.grid(row=1, column=1, ipady=7, padx=(0,20))

        btn = tk.Button(inner, text="  CALCULAR  ", font=("Segoe UI", 10, "bold"),
                        bg=ACCENT, fg="white", activebackground="#3568e5",
                        relief="flat", cursor="hand2", bd=0,
                        command=self.on_calcular)
        btn.grid(row=1, column=2, ipady=7, padx=(0,20))

        btn_clear = tk.Button(inner, text="Limpiar", font=FONT_LABEL,
                              bg=BG_INPUT, fg=TEXT_MUTED, activebackground=BG_INPUT,
                              relief="flat", cursor="hand2", bd=0,
                              command=self.on_clear)
        btn_clear.grid(row=1, column=3, ipady=7)

        ip_entry.bind("<Return>", lambda e: self.on_calcular())
        ns_entry.bind("<Return>", lambda e: self.on_calcular())

        # ── Separador ───────────────────────────────────────────────────────
        sep = tk.Frame(self, bg="#2a3050", height=1)
        sep.pack(fill="x")

        # ── Área principal (scrollable) ──────────────────────────────────────
        self.canvas = tk.Canvas(self, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(fill="both", expand=True)

        self.content = tk.Frame(self.canvas, bg=BG_DARK)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.content.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Estado inicial
        self._show_placeholder()

    def _on_frame_configure(self, e):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self.canvas.itemconfig(self.canvas_window, width=e.width)

    def _on_mousewheel(self, e):
        self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _show_placeholder(self):
        self._clear_content()
        f = tk.Frame(self.content, bg=BG_DARK)
        f.pack(expand=True, pady=80)
        tk.Label(f, text="🔢", font=("Segoe UI", 48), bg=BG_DARK, fg=TEXT_MUTED).pack()
        tk.Label(f, text="Introduce una red base y el número de subredes",
                 font=FONT_SUB, bg=BG_DARK, fg=TEXT_MUTED).pack(pady=8)

    def on_clear(self):
        self.ip_var.set("")
        self.ns_var.set("")
        self._show_placeholder()

    def on_calcular(self):
        try:
            ip = self.ip_var.get().strip()
            ns = int(self.ns_var.get().strip())
            if ns < 1:
                raise ValueError("Debe haber al menos 1 subred")
            resultado = calcular(ip, ns)
            self._mostrar_resultado(resultado)
        except ValueError as e:
            messagebox.showerror("Error de entrada", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado:\n{e}")

    def _mostrar_resultado(self, r):
        self._clear_content()
        pad = {"padx": 20, "pady": 10}

        # ── SECCIÓN GENERAL ─────────────────────────────────────────────────
        sec_gen = self._section(self.content, "📋  Información General de la Red")
        grid = tk.Frame(sec_gen, bg=BG_PANEL)
        grid.pack(fill="x", padx=16, pady=(0,12))

        fields_left = [
            ("Red Base",         r["id_red"]),
            ("Clase",            r["clase"]),
            ("Prefijo original", f"/{r['prefijo_red']}"),
            ("Hosts en la red",  f"{r['host_red']:,}"),
        ]
        fields_right = [
            ("ID Broadcast",     r["broadcast"]),
            ("1ª IP válida",     r["primera_ip"]),
            ("Última IP válida", r["ultima_ip"]),
            ("Nº subredes",      str(r["n_subredes"])),
        ]

        for i, (label, val) in enumerate(fields_left):
            self._kv(grid, label, val, i, 0)
        for i, (label, val) in enumerate(fields_right):
            self._kv(grid, label, val, i, 2)

        # ── SECCIÓN CÁLCULO DE SUBREDES ──────────────────────────────────────
        sec_calc = self._section(self.content, "⚙️  Cálculo de Subredes")
        grid2 = tk.Frame(sec_calc, bg=BG_PANEL)
        grid2.pack(fill="x", padx=16, pady=(0,12))

        fields_calc_l = [
            ("Bits de subred",    str(r["bits_subred"])),
            ("Nuevo prefijo",     f"/{r['nuevo_prefijo']}"),
            ("Host por subred",   str(r["host_subred"])),
        ]
        fields_calc_r = [
            ("Máscara de subred", r["mascara"]),
            ("Salto de subred",   str(r["salto"])),
            ("Octeto variable",   str(r["oct_variable"])),
        ]
        for i, (label, val) in enumerate(fields_calc_l):
            self._kv(grid2, label, val, i, 0)
        for i, (label, val) in enumerate(fields_calc_r):
            self._kv(grid2, label, val, i, 2)

        # Badges de resumen
        badges_frame = tk.Frame(sec_calc, bg=BG_PANEL)
        badges_frame.pack(fill="x", padx=16, pady=(4, 14))
        self._badge(badges_frame, f"/{r['nuevo_prefijo']} CIDR", ACCENT)
        self._badge(badges_frame, r["mascara"], ACCENT2)
        self._badge(badges_frame, f"Salto: {r['salto']}", GOLD)
        self._badge(badges_frame, f"{r['host_subred']} hosts/subred", GREEN_OK)

        # ── TABLA DE SUBREDES ────────────────────────────────────────────────
        sec_tab = self._section(self.content, f"📊  Tabla de Subredes  ({len(r['subredes'])} subredes)")

        # Encabezado tabla
        cols = ["#", "ID Red", "1ª IP Válida", "Última IP Válida", "Broadcast", "Bin. Últ. Octeto",
                "2⁷","2⁶","2⁵","2⁴","2³","2²","2¹","2⁰"]
        widths = [30, 120, 120, 130, 120, 130, 28,28,28,28,28,28,28,28]

        tbl_frame = tk.Frame(sec_tab, bg=BG_TABLE)
        tbl_frame.pack(fill="x", padx=16, pady=(0,14))

        # Header row
        hrow = tk.Frame(tbl_frame, bg=BG_HEADER)
        hrow.pack(fill="x")
        for col, w in zip(cols, widths):
            tk.Label(hrow, text=col, font=FONT_HEADER, bg=BG_HEADER, fg=TEXT_HEAD,
                     width=w//7, anchor="center", pady=7).pack(side="left", padx=1)

        # Data rows
        for idx, sub in enumerate(r["subredes"]):
            bg = BG_TABLE if idx % 2 == 0 else BG_ALTROW
            row = tk.Frame(tbl_frame, bg=bg)
            row.pack(fill="x")

            bits = list(sub["bin_oct"])

            cells = [
                (str(sub["num"]),  ACCENT,    widths[0]),
                (sub["id_red"],    TEXT_MAIN, widths[1]),
                (sub["primera"],   GREEN_OK,  widths[2]),
                (sub["ultima"],    TEXT_MAIN, widths[3]),
                (sub["bcast"],     RED_ERR,   widths[4]),
                (sub["bin_oct"],   GOLD,      widths[5]),
            ]
            for text, color, w in cells:
                font = FONT_MONO if text.replace(".","").isdigit() and "." in text else FONT_TABLE
                tk.Label(row, text=text, font=font, bg=bg, fg=color,
                         width=w//7, anchor="center", pady=6).pack(side="left", padx=1)

            # Bit columns
            bit_colors = [ACCENT if b == "1" else TEXT_MUTED for b in bits]
            for b, bc, w in zip(bits, bit_colors, widths[6:]):
                tk.Label(row, text=b, font=("Consolas", 9, "bold"), bg=bg, fg=bc,
                         width=w//7, anchor="center", pady=6).pack(side="left", padx=1)

        # ── PIE ─────────────────────────────────────────────────────────────
        foot = tk.Frame(self.content, bg=BG_DARK, pady=20)
        foot.pack(fill="x")
        tk.Label(foot, text=f"✅  Cálculo completado · {len(r['subredes'])} subredes generadas",
                 font=FONT_LABEL, bg=BG_DARK, fg=GREEN_OK).pack()

    def _section(self, parent, title):
        frame = tk.Frame(parent, bg=BG_PANEL, bd=0)
        frame.pack(fill="x", padx=20, pady=(14, 0))
        tk.Label(frame, text=title, font=("Segoe UI", 11, "bold"),
                 bg=BG_PANEL, fg=ACCENT, pady=10, padx=16,
                 anchor="w").pack(fill="x")
        sep = tk.Frame(frame, bg=ACCENT, height=1)
        sep.pack(fill="x", padx=16)
        return frame

    def _kv(self, parent, label, value, row, col_offset):
        tk.Label(parent, text=label, font=FONT_LABEL, bg=BG_PANEL,
                 fg=TEXT_LABEL, anchor="w").grid(
            row=row, column=col_offset, sticky="w", padx=(16 if col_offset==0 else 40, 8), pady=3)
        tk.Label(parent, text=value, font=FONT_VALUE, bg=BG_PANEL,
                 fg=TEXT_MAIN, anchor="w").grid(
            row=row, column=col_offset+1, sticky="w", padx=(0, 20), pady=3)

    def _badge(self, parent, text, color):
        tk.Label(parent, text=text, font=FONT_BADGE, bg=color, fg="white",
                 padx=10, pady=3, relief="flat").pack(side="left", padx=(0, 8))


if __name__ == "__main__":
    app = App()
    app.mainloop()
