import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox, simpledialog
import json
import math
import os
from PIL import Image, ImageTk


# --- DEFINICJE KLAS KSZTAŁTÓW ---

class Kształt:
    def __init__(self):
        self.id_na_plotnie = None

    def _wyczysc_stare_id(self, plotno):
        if self.id_na_plotnie:
            plotno.delete(self.id_na_plotnie)

    def rysuj(self, plotno, kolor_konturu=None): raise NotImplementedError

    def zawiera_punkt(self, x, y): raise NotImplementedError

    def przesun(self, dx, dy): raise NotImplementedError

    def aktualizuj_wspolrzedne(self, coords): raise NotImplementedError

    def to_dict(self): raise NotImplementedError

    @classmethod
    def from_dict(cls, data): raise NotImplementedError


class Linia(Kształt):
    def __init__(self, x1, y1, x2, y2, kolor='black'):
        super().__init__()
        self.typ = 'linia'
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.kolor = kolor

    def rysuj(self, plotno, kolor_konturu=None):
        self._wyczysc_stare_id(plotno)
        self.id_na_plotnie = plotno.create_line(self.x1, self.y1, self.x2, self.y2, fill=kolor_konturu or self.kolor,
                                                width=3, tags="vector")

    def zawiera_punkt(self, x, y):
        d_x, d_y = self.x2 - self.x1, self.y2 - self.y1
        if d_x == 0 and d_y == 0: return False
        dlugosc_kwadrat = d_x ** 2 + d_y ** 2
        t = max(0, min(1, ((x - self.x1) * d_x + (y - self.y1) * d_y) / dlugosc_kwadrat))
        proj_x, proj_y = self.x1 + t * d_x, self.y1 + t * d_y
        odleglosc = math.sqrt((x - proj_x) ** 2 + (y - proj_y) ** 2)
        return odleglosc < 5

    def przesun(self, dx, dy):
        self.x1 += dx;
        self.y1 += dy
        self.x2 += dx;
        self.y2 += dy

    def aktualizuj_wspolrzedne(self, coords):
        self.x1, self.y1, self.x2, self.y2 = coords

    def to_dict(self):
        return {'typ': self.typ, 'x1': self.x1, 'y1': self.y1, 'x2': self.x2, 'y2': self.y2, 'kolor': self.kolor}

    @classmethod
    def from_dict(cls, data):
        return cls(data['x1'], data['y1'], data['x2'], data['y2'], data['kolor'])


class Prostokat(Kształt):
    def __init__(self, x1, y1, x2, y2, kolor_konturu='black', kolor_wypelnienia=''):
        super().__init__()
        self.typ = 'prostokat'
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.kolor_konturu = kolor_konturu
        self.kolor_wypelnienia = kolor_wypelnienia

    def rysuj(self, plotno, kolor_konturu=None):
        self._wyczysc_stare_id(plotno)
        self.id_na_plotnie = plotno.create_rectangle(self.x1, self.y1, self.x2, self.y2,
                                                     outline=kolor_konturu or self.kolor_konturu,
                                                     fill=self.kolor_wypelnienia, width=2, tags="vector")

    def zawiera_punkt(self, x, y):
        lewo = min(self.x1, self.x2);
        prawo = max(self.x1, self.x2)
        gora = min(self.y1, self.y2);
        dol = max(self.y1, self.y2)
        return lewo <= x <= prawo and gora <= y <= dol

    def przesun(self, dx, dy):
        self.x1 += dx;
        self.y1 += dy
        self.x2 += dx;
        self.y2 += dy

    def aktualizuj_wspolrzedne(self, coords):
        self.x1, self.y1, self.x2, self.y2 = coords

    def to_dict(self):
        return {'typ': self.typ, 'x1': self.x1, 'y1': self.y1, 'x2': self.x2, 'y2': self.y2,
                'kolor_konturu': self.kolor_konturu, 'kolor_wypelnienia': self.kolor_wypelnienia}

    @classmethod
    def from_dict(cls, data):
        return cls(data['x1'], data['y1'], data['x2'], data['y2'], data['kolor_konturu'], data['kolor_wypelnienia'])


class Okrag(Prostokat):
    def __init__(self, x1, y1, x2, y2, kolor_konturu='blue', kolor_wypelnienia=''):
        super().__init__(x1, y1, x2, y2, kolor_konturu, kolor_wypelnienia)
        self.typ = 'okrag'

    def rysuj(self, plotno, kolor_konturu=None):
        self._wyczysc_stare_id(plotno)
        self.id_na_plotnie = plotno.create_oval(self.x1, self.y1, self.x2, self.y2,
                                                outline=kolor_konturu or self.kolor_konturu,
                                                fill=self.kolor_wypelnienia, width=2, tags="vector")


# --- KLASA KONWERTERA KOLORÓW ---

class ColorConverterDialog(tk.Toplevel):
    def __init__(self, parent, initial_rgb=None, callback=None):
        super().__init__(parent)
        self.title("Konwerter Kolorów RGB <-> CMYK")
        self.resizable(False, False)
        self.callback = callback
        self.is_modal = callback is not None

        self.r_var = tk.IntVar(value=0)
        self.g_var = tk.IntVar(value=0)
        self.b_var = tk.IntVar(value=0)
        self.c_var = tk.DoubleVar(value=0.0)
        self.m_var = tk.DoubleVar(value=0.0)
        self.y_var = tk.DoubleVar(value=0.0)
        self.k_var = tk.DoubleVar(value=100.0)

        if initial_rgb:
            r, g, b = initial_rgb
            self.r_var.set(r)
            self.g_var.set(g)
            self.b_var.set(b)

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        rgb_frame = ttk.LabelFrame(main_frame, text="Model RGB (0-255)")
        rgb_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self._create_slider_entry_block(rgb_frame, "R:", self.r_var, 0, 255, self.update_from_rgb)
        self._create_slider_entry_block(rgb_frame, "G:", self.g_var, 0, 255, self.update_from_rgb)
        self._create_slider_entry_block(rgb_frame, "B:", self.b_var, 0, 255, self.update_from_rgb)

        cmyk_frame = ttk.LabelFrame(main_frame, text="Model CMYK (0-100)")
        cmyk_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self._create_slider_entry_block(cmyk_frame, "C:", self.c_var, 0, 100, self.update_from_cmyk)
        self._create_slider_entry_block(cmyk_frame, "M:", self.m_var, 0, 100, self.update_from_cmyk)
        self._create_slider_entry_block(cmyk_frame, "Y:", self.y_var, 0, 100, self.update_from_cmyk)
        self._create_slider_entry_block(cmyk_frame, "K:", self.k_var, 0, 100, self.update_from_cmyk)

        preview_frame = ttk.LabelFrame(main_frame, text="Podgląd")
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.color_preview = tk.Frame(preview_frame, bg="#000000", width=100, height=100, relief=tk.SUNKEN,
                                      borderwidth=2)
        self.color_preview.pack(expand=True)
        self.hex_label = ttk.Label(preview_frame, text="#000000", font=("Monospace", 10))
        self.hex_label.pack(pady=5)

        if self.is_modal:
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(pady=10, fill=tk.X)
            ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Anuluj", command=self.destroy).pack(side=tk.LEFT, padx=5)

        self.r_var.trace_add("write", self.update_from_rgb)
        self.g_var.trace_add("write", self.update_from_rgb)
        self.b_var.trace_add("write", self.update_from_rgb)
        self.c_var.trace_add("write", self.update_from_cmyk)
        self.m_var.trace_add("write", self.update_from_cmyk)
        self.y_var.trace_add("write", self.update_from_cmyk)
        self.k_var.trace_add("write", self.update_from_cmyk)

        self.update_from_rgb()

        if self.is_modal:
            self.grab_set()
            self.transient(parent)

    def _create_slider_entry_block(self, parent, label, variable, from_, to, command):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(frame, text=label, width=3).pack(side=tk.LEFT)
        slider = ttk.Scale(frame, from_=from_, to=to, variable=variable, orient=tk.HORIZONTAL, command=command)
        slider.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        entry = ttk.Entry(frame, textvariable=variable, width=5)
        entry.pack(side=tk.LEFT)

    def _aktualizuj_podglad(self, r, g, b):
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.color_preview.config(bg=hex_color)
        self.hex_label.config(text=hex_color.upper())

    def update_from_rgb(self, *args):
        r, g, b = self.r_var.get(), self.g_var.get(), self.b_var.get()
        r_p, g_p, b_p = r / 255.0, g / 255.0, b / 255.0
        k = 1 - max(r_p, g_p, b_p)
        if k == 1:
            c_100, m_100, y_100 = 0.0, 0.0, 0.0
        else:
            c_100 = (1 - r_p - k) / (1 - k) * 100
            m_100 = (1 - g_p - k) / (1 - k) * 100
            y_100 = (1 - b_p - k) / (1 - k) * 100
        self.c_var.set(round(c_100, 2))
        self.m_var.set(round(m_100, 2))
        self.y_var.set(round(y_100, 2))
        self.k_var.set(round(k * 100, 2))
        self._aktualizuj_podglad(r, g, b)

    def update_from_cmyk(self, *args):
        c, m, y, k = self.c_var.get() / 100.0, self.m_var.get() / 100.0, self.y_var.get() / 100.0, self.k_var.get() / 100.0
        r, g, b = 255 * (1 - c) * (1 - k), 255 * (1 - m) * (1 - k), 255 * (1 - y) * (1 - k)
        r_int, g_int, b_int = int(round(r)), int(round(g)), int(round(b))
        self.r_var.set(r_int)
        self.g_var.set(g_int)
        self.b_var.set(b_int)
        self._aktualizuj_podglad(r_int, g_int, b_int)

    def _on_ok(self):
        r, g, b = self.r_var.get(), self.g_var.get(), self.b_var.get()
        if self.callback:
            self.callback((r, g, b))
        self.destroy()


# --- KLASA WIDOKU KOSTKI 3D ---

class CubeViewerDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Wizualizator Kostki RGB (3D)")
        self.geometry("400x400")

        self.angle_x = self.angle_y = self.angle_z = 0
        self.last_mouse_x = self.last_mouse_y = 0
        self.selected_vertex = None

        self.vertices = [
            (-1, -1, -1, "Black (0,0,0)", "#000000"),
            (1, -1, -1, "Red (R)", "#FF0000"),
            (-1, 1, -1, "Green (G)", "#00FF00"),
            (1, 1, -1, "Yellow (R+G)", "#FFFF00"),
            (-1, -1, 1, "Blue (B)", "#0000FF"),
            (1, -1, 1, "Magenta (R+B)", "#FF00FF"),
            (-1, 1, 1, "Cyan (G+B)", "#00FFFF"),
            (1, 1, 1, "White (R+G+B)", "#FFFFFF")
        ]
        self.edges = [
            (0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3), (2, 6),
            (3, 7), (4, 5), (4, 6), (5, 7), (6, 7)
        ]
        self.faces = [
            [0, 1, 3, 2], [4, 5, 7, 6], [0, 2, 6, 4],
            [1, 3, 7, 5], [0, 1, 5, 4], [2, 3, 7, 6]
        ]

        self.canvas = tk.Canvas(self, bg="lightgrey")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self._draw_cube()

    def _on_press(self, event):
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y

    def _on_drag(self, event):
        dx = event.x - self.last_mouse_x
        dy = event.y - self.last_mouse_y
        self.angle_y += dx * 0.01
        self.angle_x += dy * 0.01
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self._draw_cube()

    def _on_double_click(self, event):
        x, y = event.x, event.y
        projected_points, _ = self._project_vertices()
        closest = None
        min_dist = float('inf')
        for i, (px, py, _, _) in enumerate(projected_points):
            dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
            if dist < min_dist and dist < 10:
                min_dist = dist
                closest = i
        if closest is not None:
            self.selected_vertex = closest
            initial_hex = self.vertices[closest][4]
            r, g, b = int(initial_hex[1:3], 16), int(initial_hex[3:5], 16), int(initial_hex[5:7], 16)

            def callback(rgb):
                new_r, new_g, new_b = rgb
                new_hex = f"#{new_r:02x}{new_g:02x}{new_b:02x}"
                self.vertices[closest] = list(self.vertices[closest])
                self.vertices[closest][4] = new_hex
                self.vertices[closest] = tuple(self.vertices[closest])
                self._draw_cube()

            dialog = ColorConverterDialog(self, initial_rgb=(r, g, b), callback=callback)
            dialog.wait_window()

    def _rotate_point(self, x, y, z):
        cos_x, sin_x = math.cos(self.angle_x), math.sin(self.angle_x)
        y_rot, z_rot = y * cos_x - z * sin_x, y * sin_x + z * cos_x
        y, z = y_rot, z_rot
        cos_y, sin_y = math.cos(self.angle_y), math.sin(self.angle_y)
        x_rot, z_rot = x * cos_y + z * sin_y, -x * sin_y + z * cos_y
        return x_rot, y, z_rot

    def _project_vertices(self):
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        center_x, center_y = width / 2, height / 2
        scale = min(width, height) * 0.4
        projected_points, rotated_points = [], []

        for x, y, z, label, color in self.vertices:
            x_rot, y_rot, z_rot = self._rotate_point(x, y, z)
            rotated_points.append((x_rot, y_rot, z_rot))
            x_proj = center_x + x_rot * scale
            y_proj = center_y - y_rot * scale
            projected_points.append((x_proj, y_proj, label, color))

        return projected_points, rotated_points

    def _draw_cube(self):
        self.canvas.delete("all")
        projected_points, rotated_points = self._project_vertices()
        faces_with_z = []
        for face in self.faces:
            avg_z = sum(rotated_points[i][2] for i in face) / len(face)
            face_color = self._average_colors([self.vertices[i][4] for i in face])
            faces_with_z.append((avg_z, face, face_color))

        faces_with_z.sort(reverse=True, key=lambda x: x[0])

        for _, face, face_color in faces_with_z:
            points = []
            for i in face:
                points.extend(projected_points[i][:2])
            self.canvas.create_polygon(points, fill=face_color, outline='', width=0)

        for i_start, i_end in self.edges:
            x1, y1, _, color1 = projected_points[i_start]
            x2, y2, _, color2 = projected_points[i_end]
            edge_color = self._average_hex(color1, color2)
            self.canvas.create_line(x1, y1, x2, y2, fill=edge_color, width=2)

        for x_proj, y_proj, label, color in projected_points:
            self.canvas.create_oval(x_proj - 5, y_proj - 5, x_proj + 5, y_proj + 5, fill=color, outline="black")
            self.canvas.create_text(x_proj, y_proj - 10, text=label, anchor=tk.S, font=("Arial", 8))

    def _average_hex(self, hex1, hex2):
        return self._average_colors([hex1, hex2])

    def _average_colors(self, hex_list):
        r_sum, g_sum, b_sum = 0, 0, 0
        n = len(hex_list)
        for hex_color in hex_list:
            r_sum += int(hex_color[1:3], 16)
            g_sum += int(hex_color[3:5], 16)
            b_sum += int(hex_color[5:7], 16)
        return f"#{r_sum // n:02x}{g_sum // n:02x}{b_sum // n:02x}"


# --- GŁÓWNA KLASA APLIKACJI ---

class EdytorGraficzny:
    def __init__(self, root):
        self.root = root
        self.root.title("Edytor Graficzny Wektorowo-Rastrowy")

        self.ksztalty = []
        self.tryb = tk.StringVar(value="rysuj")
        self.wybrany_typ_ksztaltu = tk.StringVar(value="linia")
        self.start_x, self.start_y = None, None
        self.ostatni_x, self.ostatni_y = 0, 0
        self.aktualny_ksztalt_rysowany = None
        self.zaznaczony_obiekt = None
        self.kolor_zaznaczenia = 'red'
        self.obraz_oryginalny = None
        self.obraz_wyswietlany = None
        self.id_obrazu_na_plotnie = None
        self.zoom_level = 1.0
        self.id_tekstow_rgb = []
        self.konwerter_kolorow_okno = None
        self.kostka_3d_okno = None

        self.stworz_menu_glowne()
        self.ramka_narzedzi = tk.Frame(root, relief=tk.RAISED, borderwidth=2)
        self.ramka_narzedzi.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.stworz_przybornik()
        self.plotno = tk.Canvas(root, bg="white", width=800, height=600)
        self.plotno.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.bind_events()

    def stworz_menu_glowne(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        plik_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Plik", menu=plik_menu)
        plik_menu.add_command(label="Otwórz obraz (PPM, JPEG)...", command=self.wczytaj_obraz)
        plik_menu.add_command(label="Zapisz obraz jako JPEG...", command=self.zapisz_jako_jpeg, state=tk.DISABLED)
        plik_menu.add_separator()
        plik_menu.add_command(label="Wczytaj wektory (JSON)...", command=self.wczytaj_z_pliku_json)
        plik_menu.add_command(label="Zapisz wektory (JSON)...", command=self.zapisz_do_pliku_json)
        plik_menu.add_separator()
        plik_menu.add_command(label="Zakończ", command=self.root.quit)
        self.plik_menu = plik_menu

        narzedzia_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Narzędzia", menu=narzedzia_menu)
        narzedzia_menu.add_command(label="Konwerter Kolorów RGB/CMYK...", command=self.otworz_konwerter_kolorow)
        narzedzia_menu.add_command(label="Wizualizator Kostki RGB (3D)...", command=self.otworz_widok_kostki_3d)

    def stworz_przybornik(self):
        ttk.Label(self.ramka_narzedzi, text="Tryb Pracy").pack(pady=5)
        ttk.Radiobutton(self.ramka_narzedzi, text="Rysowanie", variable=self.tryb, value="rysuj").pack(anchor=tk.W)
        ttk.Radiobutton(self.ramka_narzedzi, text="Edycja", variable=self.tryb, value="edytuj").pack(anchor=tk.W)
        ttk.Separator(self.ramka_narzedzi, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(self.ramka_narzedzi, text="Kształt").pack(pady=5)
        ttk.Radiobutton(self.ramka_narzedzi, text="Linia", variable=self.wybrany_typ_ksztaltu, value="linia").pack(
            anchor=tk.W)
        ttk.Radiobutton(self.ramka_narzedzi, text="Prostokąt", variable=self.wybrany_typ_ksztaltu,
                        value="prostokat").pack(anchor=tk.W)
        ttk.Radiobutton(self.ramka_narzedzi, text="Okrąg", variable=self.wybrany_typ_ksztaltu, value="okrag").pack(
            anchor=tk.W)
        ttk.Separator(self.ramka_narzedzi, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(self.ramka_narzedzi, text="Współrzędne Zaznaczenia").pack(pady=5)
        self.pola_edycji = {}
        for label in ["x1", "y1", "x2", "y2"]:
            ramka_pola = tk.Frame(self.ramka_narzedzi)
            ramka_pola.pack(fill='x', padx=5, pady=2)
            ttk.Label(ramka_pola, text=label, width=4).pack(side=tk.LEFT)
            pole = ttk.Entry(ramka_pola)
            pole.pack(side=tk.LEFT, expand=True, fill='x')
            self.pola_edycji[label] = pole
        ttk.Button(self.ramka_narzedzi, text="Zastosuj Zmiany", command=self.zastosuj_zmiany_z_pol).pack(fill='x',
                                                                                                         pady=5)
        ttk.Separator(self.ramka_narzedzi, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(self.ramka_narzedzi, text="Narzędzia Obrazu").pack(pady=5)
        self.jakosc_jpeg = tk.IntVar(value=85)
        ttk.Label(self.ramka_narzedzi, text="Jakość JPEG (1-95):").pack()
        ttk.Scale(self.ramka_narzedzi, from_=1, to=95, variable=self.jakosc_jpeg, orient=tk.HORIZONTAL,
                  command=lambda v: self.jakosc_jpeg.set(int(float(v)))).pack(fill='x', padx=5)
        ttk.Button(self.ramka_narzedzi, text="Resetuj Widok", command=self.resetuj_widok).pack(fill='x', pady=5)

    def bind_events(self):
        self.plotno.bind("<ButtonPress-1>", self.on_press)
        self.plotno.bind("<B1-Motion>", self.on_drag)
        self.plotno.bind("<ButtonRelease-1>", self.on_release)
        self.plotno.bind("<MouseWheel>", self.on_zoom_scroll)
        self.plotno.bind("<Button-4>", self.on_zoom_scroll)
        self.plotno.bind("<Button-5>", self.on_zoom_scroll)
        self.plotno.bind("<ButtonPress-2>", self.on_pan_start)
        self.plotno.bind("<B2-Motion>", self.on_pan_move)
        self.plotno.bind("<ButtonRelease-2>", self.on_pan_release)

    def _otworz_okno_dialogowe(self, dialog_class, attribute_name):
        window = getattr(self, attribute_name)
        if window and window.winfo_exists():
            window.lift()
            window.focus()
        else:
            def on_close():
                if getattr(self, attribute_name):
                    getattr(self, attribute_name).destroy()
                setattr(self, attribute_name, None)

            new_window = dialog_class(self.root)
            setattr(self, attribute_name, new_window)
            new_window.protocol("WM_DELETE_WINDOW", on_close)

    def otworz_konwerter_kolorow(self):
        self._otworz_okno_dialogowe(ColorConverterDialog, "konwerter_kolorow_okno")

    def otworz_widok_kostki_3d(self):
        self._otworz_okno_dialogowe(CubeViewerDialog, "kostka_3d_okno")

    def on_press(self, event):
        if self.tryb.get() == "rysuj":
            self.on_press_rysuj(event)
        elif self.tryb.get() == "edytuj":
            self.on_press_edytuj(event)

    def on_drag(self, event):
        if self.tryb.get() == "rysuj":
            self.on_drag_rysuj(event)
        elif self.tryb.get() == "edytuj":
            self.on_drag_edytuj(event)

    def on_release(self, event):
        if self.tryb.get() == "rysuj":
            self.on_release_rysuj(event)
        elif self.tryb.get() == "edytuj":
            self.on_release_edytuj(event)

    def on_press_rysuj(self, event):
        self.start_x, self.start_y = self.plotno.canvasx(event.x), self.plotno.canvasy(event.y)
        ksztalt = self.wybrany_typ_ksztaltu.get()
        if ksztalt == "linia":
            self.aktualny_ksztalt_rysowany = Linia(self.start_x, self.start_y, self.start_x, self.start_y)
        elif ksztalt == "prostokat":
            self.aktualny_ksztalt_rysowany = Prostokat(self.start_x, self.start_y, self.start_x, self.start_y)
        elif ksztalt == "okrag":
            self.aktualny_ksztalt_rysowany = Okrag(self.start_x, self.start_y, self.start_x, self.start_y)
        if self.aktualny_ksztalt_rysowany: self.aktualny_ksztalt_rysowany.rysuj(self.plotno)

    def on_drag_rysuj(self, event):
        if self.aktualny_ksztalt_rysowany:
            end_x, end_y = self.plotno.canvasx(event.x), self.plotno.canvasy(event.y)
            self.aktualny_ksztalt_rysowany.x2, self.aktualny_ksztalt_rysowany.y2 = end_x, end_y
            self.aktualny_ksztalt_rysowany.rysuj(self.plotno)

    def on_release_rysuj(self, event):
        if self.aktualny_ksztalt_rysowany:
            self.on_drag_rysuj(event)
            self.ksztalty.append(self.aktualny_ksztalt_rysowany)
            self.aktualny_ksztalt_rysowany = None

    def on_press_edytuj(self, event):
        self.ostatni_x, self.ostatni_y = self.plotno.canvasx(event.x), self.plotno.canvasy(event.y)
        obiekt_do_zaznaczenia = None
        canvas_x, canvas_y = self.plotno.canvasx(event.x), self.plotno.canvasy(event.y)
        for obiekt in reversed(self.ksztalty):
            if obiekt.zawiera_punkt(canvas_x, canvas_y):
                obiekt_do_zaznaczenia = obiekt
                break
        self.zaznacz_obiekt(obiekt_do_zaznaczenia)

    def on_drag_edytuj(self, event):
        if self.zaznaczony_obiekt:
            canvas_x, canvas_y = self.plotno.canvasx(event.x), self.plotno.canvasy(event.y)
            dx, dy = canvas_x - self.ostatni_x, canvas_y - self.ostatni_y
            self.zaznaczony_obiekt.przesun(dx, dy)
            self.zaznaczony_obiekt.rysuj(self.plotno, kolor_konturu=self.kolor_zaznaczenia)
            self.ostatni_x, self.ostatni_y = canvas_x, canvas_y
            self.aktualizuj_pola_edycji(self.zaznaczony_obiekt)

    def on_release_edytuj(self, event):
        pass

    def zaznacz_obiekt(self, obiekt):
        if self.zaznaczony_obiekt and self.zaznaczony_obiekt in self.ksztalty:
            self.zaznaczony_obiekt.rysuj(self.plotno)
        self.zaznaczony_obiekt = obiekt
        if self.zaznaczony_obiekt:
            self.zaznaczony_obiekt.rysuj(self.plotno, kolor_konturu=self.kolor_zaznaczenia)
        self.aktualizuj_pola_edycji(obiekt)

    def aktualizuj_pola_edycji(self, obiekt):
        if obiekt:
            for label, value in zip(["x1", "y1", "x2", "y2"], [obiekt.x1, obiekt.y1, obiekt.x2, obiekt.y2]):
                self.pola_edycji[label].delete(0, tk.END)
                self.pola_edycji[label].insert(0, int(value))
        else:
            for pole in self.pola_edycji.values(): pole.delete(0, tk.END)

    def zastosuj_zmiany_z_pol(self):
        if not self.zaznaczony_obiekt: return
        nowe_wspolrzedne = [
            int(self.pola_edycji['x1'].get()), int(self.pola_edycji['y1'].get()),
            int(self.pola_edycji['x2'].get()), int(self.pola_edycji['y2'].get())
        ]
        self.zaznaczony_obiekt.aktualizuj_wspolrzedne(nowe_wspolrzedne)
        self.zaznaczony_obiekt.rysuj(self.plotno, kolor_konturu=self.kolor_zaznaczenia)

    def zapisz_do_pliku_json(self):
        sciezka_pliku = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not sciezka_pliku: return
        dane_do_zapisu = [ksztalt.to_dict() for ksztalt in self.ksztalty]
        with open(sciezka_pliku, 'w') as f:
            json.dump(dane_do_zapisu, f, indent=4)
        print(f"Zapisano rysunek wektorowy do pliku {sciezka_pliku}")

    def wczytaj_z_pliku_json(self):
        sciezka_pliku = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not sciezka_pliku: return
        with open(sciezka_pliku, 'r') as f:
            dane_z_pliku = json.load(f)

        self.resetuj_widok()
        self.ksztalty.clear();
        self.zaznacz_obiekt(None)
        mapa_klas = {'linia': Linia, 'prostokat': Prostokat, 'okrag': Okrag}
        for dane_ksztaltu in dane_z_pliku:
            klasa_ksztaltu = mapa_klas.get(dane_ksztaltu.get('typ'))
            if klasa_ksztaltu:
                nowy_ksztalt = klasa_ksztaltu.from_dict(dane_ksztaltu)
                self.ksztalty.append(nowy_ksztalt)
                nowy_ksztalt.rysuj(self.plotno)
        print(f"Wczytano rysunek wektorowy z pliku {sciezka_pliku}.")

    def resetuj_widok(self):
        self.plotno.delete("all")
        self.zoom_level = 1.0
        self.id_obrazu_na_plotnie = None
        self.id_tekstow_rgb.clear()
        if self.obraz_oryginalny:
            self.obraz_wyswietlany = ImageTk.PhotoImage(self.obraz_oryginalny)
            self.id_obrazu_na_plotnie = self.plotno.create_image(0, 0, anchor=tk.NW, image=self.obraz_wyswietlany)
        for ksztalt in self.ksztalty: ksztalt.rysuj(self.plotno)
        if self.zaznaczony_obiekt in self.ksztalty:
            self.zaznaczony_obiekt.rysuj(self.plotno, kolor_konturu=self.kolor_zaznaczenia)
        self.plotno.xview_moveto(0.0);
        self.plotno.yview_moveto(0.0)

    def _wczytaj_obraz_pil(self, sciezka_pliku):
        img = Image.open(sciezka_pliku)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return img

    def wczytaj_obraz(self):
        sciezka_pliku = filedialog.askopenfilename(filetypes=[
            ("Obrazy", "*.ppm *.jpg *.jpeg"),
            ("Pliki PPM", "*.ppm"),
            ("Pliki JPEG", "*.jpg *.jpeg"),
            ("Wszystkie pliki", "*.*")
        ])
        if not sciezka_pliku: return

        nowy_obraz = self._wczytaj_obraz_pil(sciezka_pliku)

        if nowy_obraz:
            self.resetuj_widok()
            self.obraz_oryginalny = nowy_obraz
            self.obraz_wyswietlany = ImageTk.PhotoImage(self.obraz_oryginalny)
            self.id_obrazu_na_plotnie = self.plotno.create_image(0, 0, anchor=tk.NW, image=self.obraz_wyswietlany)
            self.plotno.lower(self.id_obrazu_na_plotnie)
            self.plik_menu.entryconfig("Zapisz obraz jako JPEG...", state=tk.NORMAL)
            print(f"Wczytano obraz {sciezka_pliku} (Rozmiar: {nowy_obraz.width}x{nowy_obraz.height})")
        else:
            self.plik_menu.entryconfig("Zapisz obraz jako JPEG...", state=tk.DISABLED)

    def zapisz_jako_jpeg(self):
        if not self.obraz_oryginalny:
            messagebox.showwarning("Brak Obrazu", "Nie wczytano żadnego obrazu...")
            return
        sciezka_pliku = filedialog.asksaveasfilename(defaultextension=".jpg",
                                                     filetypes=[("JPEG files", "*.jpg *.jpeg")])
        if not sciezka_pliku: return

        jakosc = self.jakosc_jpeg.get()
        self.obraz_oryginalny.convert('RGB').save(sciezka_pliku, 'JPEG', quality=jakosc)
        print(f"Zapisano obraz do {sciezka_pliku} z jakością {jakosc}")

    def on_zoom_scroll(self, event):
        x, y = self.plotno.canvasx(event.x), self.plotno.canvasy(event.y)
        factor = 1.1 if (event.num == 4 or event.delta > 0) else 0.9

        new_zoom_level = self.zoom_level * factor
        if new_zoom_level < 0.05 or new_zoom_level > 100:
            print(f"Osiągnięto limit zoomu: {new_zoom_level:.2f}");
            return

        if self.obraz_oryginalny and self.id_obrazu_na_plotnie:
            old_coords = self.plotno.coords(self.id_obrazu_na_plotnie)
            old_x, old_y = (old_coords[0], old_coords[1]) if old_coords else (0, 0)

            new_img_x = (old_x - x) * factor + x
            new_img_y = (old_y - y) * factor + y
            new_width = int(self.obraz_oryginalny.width * new_zoom_level)
            new_height = int(self.obraz_oryginalny.height * new_zoom_level)

            if new_width > 0 and new_height > 0:
                resized_pil_img = self.obraz_oryginalny.resize((new_width, new_height), Image.NEAREST)
                self.obraz_wyswietlany = ImageTk.PhotoImage(resized_pil_img)
                self.plotno.delete(self.id_obrazu_na_plotnie)
                self.id_obrazu_na_plotnie = self.plotno.create_image(new_img_x, new_img_y, anchor=tk.NW,
                                                                     image=self.obraz_wyswietlany)
                self.plotno.lower(self.id_obrazu_na_plotnie)

        self.plotno.scale("vector", x, y, factor, factor)
        self.zoom_level = new_zoom_level
        self.aktualizuj_rgb_na_pikselach()

    def on_pan_start(self, event):
        self.plotno.scan_mark(event.x, event.y)
        self.czysc_rgb_na_pikselach()

    def on_pan_move(self, event):
        self.plotno.scan_dragto(event.x, event.y, gain=1)

    def on_pan_release(self, event):
        self.aktualizuj_rgb_na_pikselach()

    def czysc_rgb_na_pikselach(self):
        for text_id in self.id_tekstow_rgb: self.plotno.delete(text_id)
        self.id_tekstow_rgb.clear()

    def aktualizuj_rgb_na_pikselach(self):
        self.czysc_rgb_na_pikselach()
        if not self.obraz_oryginalny or self.zoom_level < 20 or not self.id_obrazu_na_plotnie:
            return

        img_coords = self.plotno.coords(self.id_obrazu_na_plotnie)
        if not img_coords: return
        img_x_on_canvas, img_y_on_canvas = img_coords[0], img_coords[1]

        x_min, y_min = self.plotno.canvasx(0), self.plotno.canvasy(0)
        x_max, y_max = self.plotno.canvasx(self.plotno.winfo_width()), self.plotno.canvasy(self.plotno.winfo_height())

        img_x_start = max(0, int((x_min - img_x_on_canvas) / self.zoom_level))
        img_y_start = max(0, int((y_min - img_y_on_canvas) / self.zoom_level))
        img_x_end = min(self.obraz_oryginalny.width, int((x_max - img_x_on_canvas) / self.zoom_level) + 1)
        img_y_end = min(self.obraz_oryginalny.height, int((y_max - img_y_on_canvas) / self.zoom_level) + 1)

        liczba_pikseli = (img_x_end - img_x_start) * (img_y_end - img_y_start)
        if liczba_pikseli > 500:
            print(f"Pomijanie rysowania RGB: zbyt wiele pikseli w widoku ({liczba_pikseli})");
            return

        widoczny_region = self.obraz_oryginalny.crop((img_x_start, img_y_start, img_x_end, img_y_end))
        piksele = widoczny_region.load()

        font_size = max(1, min(6, int(self.zoom_level / 4)));
        font = ("Arial", font_size)

        for y in range(widoczny_region.height):
            for x in range(widoczny_region.width):
                img_x, img_y = img_x_start + x, img_y_start + y
                r, g, b = piksele[x, y]
                text = f"{r}\n{g}\n{b}"
                canvas_x = (img_x + 0.5) * self.zoom_level + img_x_on_canvas
                canvas_y = (img_y + 0.5) * self.zoom_level + img_y_on_canvas
                text_id = self.plotno.create_text(canvas_x, canvas_y, text=text, font=font, fill="black",
                                                  tags="pixel_rgb_text")
                self.id_tekstow_rgb.append(text_id)


# --- URUCHOMIENIE APLIKACJI ---

def main():
    root = tk.Tk()
    app = EdytorGraficzny(root)
    root.mainloop()


if __name__ == "__main__":
    main()