import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox, simpledialog
import json
import math
import os

# --- Blok importu Pillow (PIL) ---
# Należy zainstalować tę bibliotekę: pip install Pillow
try:
    from PIL import Image, ImageTk
except ImportError:
    print("--------------------------------------------------")
    print("BŁĄD: Nie znaleziono biblioteki Pillow (PIL).")
    print("Aby wczytywać i zapisywać pliki JPEG oraz PPM,")
    print("zainstaluj ją za pomocą polecenia:")
    print("pip install Pillow")
    print("--------------------------------------------------")


    # Zastąpmy messagebox, aby program się uruchomił, ale pokazał błąd
    class MockMessageBox:
        def showerror(self, title, message):
            print(f"BŁĄD: {title} - {message}")


    messagebox = MockMessageBox()


# ------------------------------------


# --- DEFINICJE KLAS KSZTAŁTÓW ---
# (Bez zmian - ten kod jest już poprawny)

class Kształt:
    """ Klasa bazowa dla wszystkich figur geometrycznych. """

    def __init__(self):
        self.id_na_plotnie = None

    def rysuj(self, plotno, kolor_konturu=None):
        raise NotImplementedError

    def zawiera_punkt(self, x, y):
        raise NotImplementedError

    def przesun(self, dx, dy):
        raise NotImplementedError

    def aktualizuj_wspolrzedne(self, coords):
        raise NotImplementedError

    def to_dict(self):
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data):
        raise NotImplementedError


class Linia(Kształt):
    def __init__(self, x1, y1, x2, y2, kolor='black'):
        super().__init__()
        self.typ = 'linia'
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        self.kolor = kolor

    def rysuj(self, plotno, kolor_konturu=None):
        if self.id_na_plotnie:
            try:
                plotno.delete(self.id_na_plotnie)
            except tk.TclError:
                pass  # Obiekt mógł zostać usunięty przez reset płótna
        self.id_na_plotnie = plotno.create_line(
            self.x1, self.y1, self.x2, self.y2,
            fill=kolor_konturu or self.kolor, width=3,
            tags="vector"  # <-- DODANO TAG
        )

    def zawiera_punkt(self, x, y):
        d_x, d_y = self.x2 - self.x1, self.y2 - self.y1
        if d_x == 0 and d_y == 0: return False
        dlugosc_kwadrat = d_x ** 2 + d_y ** 2
        t = max(0, min(1, ((x - self.x1) * d_x + (y - self.y1) * d_y) / dlugosc_kwadrat))
        proj_x = self.x1 + t * d_x
        proj_y = self.y1 + t * d_y
        odleglosc = math.sqrt((x - proj_x) ** 2 + (y - proj_y) ** 2)
        return odleglosc < 5  # 5 pikseli tolerancji

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
        if self.id_na_plotnie:
            try:
                plotno.delete(self.id_na_plotnie)
            except tk.TclError:
                pass
        self.id_na_plotnie = plotno.create_rectangle(
            self.x1, self.y1, self.x2, self.y2,
            outline=kolor_konturu or self.kolor_konturu, fill=self.kolor_wypelnienia, width=2,
            tags="vector"  # <-- DODANO TAG
        )

    def zawiera_punkt(self, x, y):
        lewo = min(self.x1, self.x2)
        prawo = max(self.x1, self.x2)
        gora = min(self.y1, self.y2)
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


class Okrag(Prostokat):  # Okrąg dziedziczy po prostokącie
    def __init__(self, x1, y1, x2, y2, kolor_konturu='blue', kolor_wypelnienia=''):
        super().__init__(x1, y1, x2, y2, kolor_konturu, kolor_wypelnienia)
        self.typ = 'okrag'

    def rysuj(self, plotno, kolor_konturu=None):
        if self.id_na_plotnie:
            try:
                plotno.delete(self.id_na_plotnie)
            except tk.TclError:
                pass
        self.id_na_plotnie = plotno.create_oval(
            self.x1, self.y1, self.x2, self.y2,
            outline=kolor_konturu or self.kolor_konturu, fill=self.kolor_wypelnienia, width=2,
            tags="vector"  # <-- DODANO TAG
        )

    # Metody `zawiera_punkt`, `przesun`, `aktualizuj_wspolrzedne`, `to_dict`
    # są dziedziczone z Prostokat i działają poprawnie.


# --- GŁÓWNA KLASA APLIKACJI ---

class EdytorGraficzny:
    def __init__(self, root):
        self.root = root
        self.root.title("Edytor Graficzny Wektorowo-Rastrowy")

        # --- Zmienne Stanu Wektorowego ---
        self.ksztalty = []
        self.tryb = tk.StringVar(value="rysuj")
        self.wybrany_typ_ksztaltu = tk.StringVar(value="linia")
        self.start_x, self.start_y = None, None
        self.ostatni_x, self.ostatni_y = 0, 0
        self.aktualny_ksztalt_rysowany = None
        self.zaznaczony_obiekt = None
        self.kolor_zaznaczenia = 'red'

        # --- NOWE Zmienne Stanu Rastrowego ---
        self.obraz_oryginalny = None  # Obiekt PIL.Image
        self.obraz_wyswietlany = None  # Obiekt ImageTk.PhotoImage
        self.id_obrazu_na_plotnie = None
        self.zoom_level = 1.0
        self.id_tekstow_rgb = []  # Lista ID tekstów RGB na płótnie

        # --- Interfejs Użytkownika ---
        self.stworz_menu_glowne()

        self.ramka_narzedzi = tk.Frame(root, relief=tk.RAISED, borderwidth=2)
        self.ramka_narzedzi.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        self.stworz_przybornik()

        self.plotno = tk.Canvas(root, bg="white", width=800, height=600)
        self.plotno.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.bind_events()

    def stworz_menu_glowne(self):
        """Tworzy górny pasek menu dla operacji na plikach."""
        menu_bar = tk.Menu(self.root)

        # --- Menu Plik ---
        plik_menu = tk.Menu(menu_bar, tearoff=0)

        plik_menu.add_command(label="Otwórz obraz (PPM, JPEG)...", command=self.wczytaj_obraz)
        plik_menu.add_command(label="Zapisz obraz jako JPEG...", command=self.zapisz_jako_jpeg, state=tk.DISABLED)
        plik_menu.add_separator()
        plik_menu.add_command(label="Wczytaj wektory (JSON)...", command=self.wczytaj_z_pliku_json)
        plik_menu.add_command(label="Zapisz wektory (JSON)...", command=self.zapisz_do_pliku_json)
        plik_menu.add_separator()
        plik_menu.add_command(label="Zakończ", command=self.root.quit)

        menu_bar.add_cascade(label="Plik", menu=plik_menu)
        self.root.config(menu=menu_bar)
        self.plik_menu = plik_menu  # Zapisujemy referencję, by móc aktywować "Zapisz"

    def stworz_przybornik(self):
        """Tworzy panel z narzędziami."""
        # --- Sekcja Trybu ---
        ttk.Label(self.ramka_narzedzi, text="Tryb Pracy").pack(pady=5)
        ttk.Radiobutton(self.ramka_narzedzi, text="Rysowanie", variable=self.tryb, value="rysuj").pack(anchor=tk.W)
        ttk.Radiobutton(self.ramka_narzedzi, text="Edycja", variable=self.tryb, value="edytuj").pack(anchor=tk.W)

        ttk.Separator(self.ramka_narzedzi, orient='horizontal').pack(fill='x', pady=10)

        # --- Sekcja Rysowania ---
        ttk.Label(self.ramka_narzedzi, text="Kształt").pack(pady=5)
        ttk.Radiobutton(self.ramka_narzedzi, text="Linia", variable=self.wybrany_typ_ksztaltu, value="linia").pack(
            anchor=tk.W)
        ttk.Radiobutton(self.ramka_narzedzi, text="Prostokąt", variable=self.wybrany_typ_ksztaltu,
                        value="prostokat").pack(anchor=tk.W)
        ttk.Radiobutton(self.ramka_narzedzi, text="Okrąg", variable=self.wybrany_typ_ksztaltu, value="okrag").pack(
            anchor=tk.W)

        ttk.Separator(self.ramka_narzedzi, orient='horizontal').pack(fill='x', pady=10)

        # --- Sekcja Edycji ---
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

        # --- NOWA Sekcja Obrazu ---
        ttk.Label(self.ramka_narzedzi, text="Narzędzia Obrazu").pack(pady=5)

        self.jakosc_jpeg = tk.IntVar(value=85)
        ttk.Label(self.ramka_narzedzi, text="Jakość JPEG (1-95):").pack()
        ttk.Scale(self.ramka_narzedzi, from_=1, to=95, variable=self.jakosc_jpeg,
                  orient=tk.HORIZONTAL, command=lambda v: self.jakosc_jpeg.set(int(float(v)))).pack(fill='x', padx=5)

        ttk.Button(self.ramka_narzedzi, text="Resetuj Widok", command=self.resetuj_widok).pack(fill='x', pady=5)

    def bind_events(self):
        # --- Zdarzenia myszy dla trybów ---
        self.plotno.bind("<ButtonPress-1>", self.on_press)
        self.plotno.bind("<B1-Motion>", self.on_drag)
        self.plotno.bind("<ButtonRelease-1>", self.on_release)

        # --- NOWE Zdarzenia dla Zoomu (Powiększania) ---
        self.plotno.bind("<MouseWheel>", self.on_zoom_scroll)  # Windows/macOS
        self.plotno.bind("<Button-4>", self.on_zoom_scroll)  # Linux (scroll up)
        self.plotno.bind("<Button-5>", self.on_zoom_scroll)  # Linux (scroll down)

        # --- NOWE Zdarzenia dla Panoramy (Przesuwania) ---
        self.plotno.bind("<ButtonPress-2>", self.on_pan_start)  # Środkowy przycisk myszy
        self.plotno.bind("<B2-Motion>", self.on_pan_move)
        self.plotno.bind("<ButtonRelease-2>", self.on_pan_release)

    # --- Obsługa zdarzeń myszy (delegacja do trybów) ---
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

    # --- METODY DLA TRYBU RYSOWANIA ---
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

    # --- METODY DLA TRYBU EDYCJI ---
    def on_press_edytuj(self, event):
        self.ostatni_x, self.ostatni_y = self.plotno.canvasx(event.x), self.plotno.canvasy(event.y)
        obiekt_do_zaznaczenia = None
        # Konwersja współrzędnych ekranu na współrzędne płótna
        canvas_x, canvas_y = self.plotno.canvasx(event.x), self.plotno.canvasy(event.y)

        for obiekt in reversed(self.ksztalty):
            if obiekt.zawiera_punkt(canvas_x, canvas_y):
                obiekt_do_zaznaczenia = obiekt
                break
        self.zaznacz_obiekt(obiekt_do_zaznaczenia)

    def on_drag_edytuj(self, event):
        if self.zaznaczony_obiekt:
            canvas_x, canvas_y = self.plotno.canvasx(event.x), self.plotno.canvasy(event.y)
            dx = canvas_x - self.ostatni_x
            dy = canvas_y - self.ostatni_y
            self.zaznaczony_obiekt.przesun(dx, dy)
            self.zaznaczony_obiekt.rysuj(self.plotno, kolor_konturu=self.kolor_zaznaczenia)
            self.ostatni_x, self.ostatni_y = canvas_x, canvas_y
            self.aktualizuj_pola_edycji(self.zaznaczony_obiekt)

    def on_release_edytuj(self, event):
        pass  # Nic specjalnego nie trzeba robić

    # --- Metody pomocnicze trybu edycji ---
    def zaznacz_obiekt(self, obiekt):
        if self.zaznaczony_obiekt and self.zaznaczony_obiekt in self.ksztalty:
            self.zaznaczony_obiekt.rysuj(self.plotno)  # Przerysuj w normalnym kolorze

        self.zaznaczony_obiekt = obiekt

        if self.zaznaczony_obiekt:
            self.zaznaczony_obiekt.rysuj(self.plotno, kolor_konturu=self.kolor_zaznaczenia)

        self.aktualizuj_pola_edycji(obiekt)

    def aktualizuj_pola_edycji(self, obiekt):
        if obiekt:
            self.pola_edycji['x1'].delete(0, tk.END);
            self.pola_edycji['x1'].insert(0, int(obiekt.x1))
            self.pola_edycji['y1'].delete(0, tk.END);
            self.pola_edycji['y1'].insert(0, int(obiekt.y1))
            self.pola_edycji['x2'].delete(0, tk.END);
            self.pola_edycji['x2'].insert(0, int(obiekt.x2))
            self.pola_edycji['y2'].delete(0, tk.END);
            self.pola_edycji['y2'].insert(0, int(obiekt.y2))
        else:
            for pole in self.pola_edycji.values(): pole.delete(0, tk.END)

    def zastosuj_zmiany_z_pol(self):
        if not self.zaznaczony_obiekt:
            return
        try:
            nowe_wspolrzedne = [
                int(self.pola_edycji['x1'].get()), int(self.pola_edycji['y1'].get()),
                int(self.pola_edycji['x2'].get()), int(self.pola_edycji['y2'].get())
            ]
            self.zaznaczony_obiekt.aktualizuj_wspolrzedne(nowe_wspolrzedne)
            self.zaznaczony_obiekt.rysuj(self.plotno, kolor_konturu=self.kolor_zaznaczenia)
        except (ValueError, TypeError):
            messagebox.showerror("Błąd", "Wprowadź prawidłowe liczby całkowite jako współrzędne.")

    # --- SERIALIZACJA (WEKTORY - JSON) ---
    def zapisz_do_pliku_json(self):
        sciezka_pliku = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not sciezka_pliku: return
        dane_do_zapisu = [ksztalt.to_dict() for ksztalt in self.ksztalty]
        try:
            with open(sciezka_pliku, 'w') as f:
                json.dump(dane_do_zapisu, f, indent=4)
            print(f"Zapisano rysunek wektorowy do pliku {sciezka_pliku}")
        except IOError as e:
            messagebox.showerror("Błąd Zapisu", f"Nie można zapisać pliku:\n{e}")

    def wczytaj_z_pliku_json(self):
        sciezka_pliku = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not sciezka_pliku: return
        try:
            with open(sciezka_pliku, 'r') as f:
                dane_z_pliku = json.load(f)
        except FileNotFoundError:
            messagebox.showerror("Błąd Odczytu", f"Plik {sciezka_pliku} nie istnieje.");
            return
        except json.JSONDecodeError:
            messagebox.showerror("Błąd Odczytu", f"Plik {sciezka_pliku} nie jest poprawnym plikiem JSON.");
            return

        self.resetuj_widok()  # Czyści płótno i resetuje widok
        self.ksztalty.clear();
        self.zaznacz_obiekt(None)

        mapa_klas = {'linia': Linia, 'prostokat': Prostokat, 'okrag': Okrag}
        for dane_ksztaltu in dane_z_pliku:
            klasa_ksztaltu = mapa_klas.get(dane_ksztaltu.get('typ'))
            if klasa_ksztaltu:
                try:
                    nowy_ksztalt = klasa_ksztaltu.from_dict(dane_ksztaltu)
                    self.ksztalty.append(nowy_ksztalt)
                    nowy_ksztalt.rysuj(self.plotno)
                except KeyError as e:
                    print(f"Brakujący klucz w danych kształtu: {e}. Pomijanie.")
        print(f"Wczytano rysunek wektorowy z pliku {sciezka_pliku}.")

    # --- NOWE: RESET WIDOKU (ZOOM/PAN) ---

    def resetuj_widok(self):
        """Czyści płótno i przywraca domyślny widok oraz obiekty."""
        self.plotno.delete("all")
        self.zoom_level = 1.0
        self.id_obrazu_na_plotnie = None
        self.id_tekstow_rgb.clear()

        # Przerysuj obraz (jeśli jest)
        if self.obraz_oryginalny:
            self.obraz_wyswietlany = ImageTk.PhotoImage(self.obraz_oryginalny)
            self.id_obrazu_na_plotnie = self.plotno.create_image(
                0, 0, anchor=tk.NW, image=self.obraz_wyswietlany
            )

        # Przerysuj kształty wektorowe
        for ksztalt in self.ksztalty:
            ksztalt.rysuj(self.plotno)

        # Przywróć zaznaczenie, jeśli obiekt nadal istnieje
        if self.zaznaczony_obiekt in self.ksztalty:
            self.zaznaczony_obiekt.rysuj(self.plotno, kolor_konturu=self.kolor_zaznaczenia)

        # Ustaw widok płótna na pozycję 0,0
        self.plotno.xview_moveto(0.0)
        self.plotno.yview_moveto(0.0)

    # --- NOWE: WCZYTYWANIE OBRAZÓW (RASTRY) ---

    def wczytaj_obraz(self):
        """Główna funkcja wczytująca, delegująca do odpowiednich parserów."""
        sciezka_pliku = filedialog.askopenfilename(filetypes=[
            ("Obrazy", "*.ppm *.jpg *.jpeg"),
            ("Pliki PPM", "*.ppm"),
            ("Pliki JPEG", "*.jpg *.jpeg"),
            ("Wszystkie pliki", "*.*")
        ])
        if not sciezka_pliku: return

        plik_rozszerzenie = os.path.splitext(sciezka_pliku)[1].lower()
        nowy_obraz = None

        try:
            if plik_rozszerzenie == '.ppm':
                nowy_obraz = self.wczytaj_ppm(sciezka_pliku)
            elif plik_rozszerzenie in ('.jpg', '.jpeg'):
                nowy_obraz = self.wczytaj_jpeg(sciezka_pliku)
            else:
                # Spróbuj wczytać jako JPEG na wszelki wypadek (np. brak rozszerzenia)
                try:
                    nowy_obraz = self.wczytaj_jpeg(sciezka_pliku)
                except Exception:
                    # Jeśli JPEG zawiedzie, spróbuj PPM
                    try:
                        nowy_obraz = self.wczytaj_ppm(sciezka_pliku)
                    except Exception:
                        raise ValueError(f"Nieobsługiwany format pliku: {plik_rozszerzenie}")

            if nowy_obraz:
                self.resetuj_widok()  # Czyści stare dane
                self.obraz_oryginalny = nowy_obraz
                self.obraz_wyswietlany = ImageTk.PhotoImage(self.obraz_oryginalny)

                self.id_obrazu_na_plotnie = self.plotno.create_image(
                    0, 0, anchor=tk.NW, image=self.obraz_wyswietlany
                )
                # Przenieś obraz na spód (pod wektory)
                self.plotno.lower(self.id_obrazu_na_plotnie)

                # Aktywuj opcję zapisu
                self.plik_menu.entryconfig("Zapisz obraz jako JPEG...", state=tk.NORMAL)

                print(f"Wczytano obraz {sciezka_pliku} (Rozmiar: {nowy_obraz.width}x{nowy_obraz.height})")

        except Exception as e:
            messagebox.showerror("Błąd Wczytywania Obrazu", f"Nie udało się wczytać pliku:\n{e}")
            self.plik_menu.entryconfig("Zapisz obraz jako JPEG...", state=tk.DISABLED)

    def wczytaj_jpeg(self, sciezka_pliku):
        """Wczytuje obraz JPEG za pomocą Pillow."""
        if 'Image' not in globals():
            raise ImportError("Biblioteka Pillow (PIL) nie jest załadowana.")

        img = Image.open(sciezka_pliku)
        # Upewnij się, że obraz jest w trybie RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return img

    def _pomocnik_czytaj_ppm_wartosc(self, f):
        """Czyta jedną wartość (liczbę) z pliku PPM, omijając komentarze i białe znaki."""
        bajt = f.read(1)
        # Pomiń białe znaki na początku
        while bajt.isspace():
            bajt = f.read(1)

        # Pomiń komentarze
        while bajt == b'#':
            f.readline()  # Czytaj do końca linii
            bajt = f.read(1)
            while bajt.isspace():  # Pomiń białe znaki po komentarzu
                bajt = f.read(1)

        # Czytaj liczbę
        wartosc_str = b''
        while bajt and not bajt.isspace():
            wartosc_str += bajt
            bajt = f.read(1)

        if not wartosc_str:
            raise ValueError("Nieoczekiwany koniec pliku podczas czytania nagłówka PPM.")

        return int(wartosc_str)

    def wczytaj_ppm(self, sciezka_pliku):
        """Wczytuje obraz PPM (P3 lub P6) ręcznie, bez bibliotek."""
        if 'Image' not in globals():
            raise ImportError("Biblioteka Pillow (PIL) nie jest załadowana.")

        with open(sciezka_pliku, 'rb') as f:
            # 1. Magic Number (P3 lub P6)
            magic_number = f.readline().strip()
            if magic_number not in (b'P3', b'P6'):
                raise ValueError(f"Nieobsługiwany format PPM: {magic_number}. Tylko P3 i P6.")

            # 2. Wymiary (Szerokość, Wysokość) i MaxVal
            try:
                w = self._pomocnik_czytaj_ppm_wartosc(f)
                h = self._pomocnik_czytaj_ppm_wartosc(f)
                maxval = self._pomocnik_czytaj_ppm_wartosc(f)
            except Exception as e:
                raise ValueError(f"Uszkodzony nagłówek PPM: {e}")

            if maxval <= 0 or maxval > 65535:
                raise ValueError(f"Nieprawidłowa maksymalna wartość koloru: {maxval}")

            print(f"Wczytywanie PPM {magic_number.decode()}: {w}x{h}, maxval={maxval}")

            # Bufor na dane RGB (zawsze 8-bit na kanał)
            dane_rgb = bytearray(w * h * 3)

            # --- Wczytywanie P3 (ASCII) ---
            if magic_number == b'P3':
                idx = 0
                for _ in range(w * h * 3):
                    if idx >= len(dane_rgb):
                        raise ValueError("Za dużo danych pikseli w pliku P3.")
                    try:
                        wartosc_str = self._pomocnik_czytaj_ppm_wartosc(f)
                    except ValueError:
                        # Może być problem z ostatnią wartością bez białego znaku
                        f.seek(f.tell() - 1)  # Cofnij się
                        wartosc_str = f.read().split()[0]  # Czytaj resztę i weź pierwszą
                        if not wartosc_str:
                            raise ValueError("Za mało danych pikseli w pliku P3.")
                        wartosc_str = int(wartosc_str)

                    # Skalowanie liniowe kolorów
                    dane_rgb[idx] = (wartosc_str * 255) // maxval
                    idx += 1

            # --- Wczytywanie P6 (Binarny) ---
            elif magic_number == b'P6':
                # P6 zakłada 1 bajt na kanał jeśli maxval < 256
                if maxval < 256:
                    bytes_do_wczytania = w * h * 3
                    # Wydajny odczyt blokowy
                    surowe_dane = f.read(bytes_do_wczytania)
                    if len(surowe_dane) != bytes_do_wczytania:
                        raise ValueError(
                            f"Za mało danych pikseli w pliku P6. Oczekiwano {bytes_do_wczytania}, wczytano {len(surowe_dane)}")

                    if maxval == 255:
                        dane_rgb = surowe_dane  # Najszybsza ścieżka
                    else:
                        # Skalowanie liniowe kolorów
                        for i in range(bytes_do_wczytania):
                            dane_rgb[i] = (surowe_dane[i] * 255) // maxval

                # P6 zakłada 2 bajty na kanał (Big Endian) jeśli maxval >= 256
                else:
                    bytes_do_wczytania = w * h * 3 * 2
                    surowe_dane = f.read(bytes_do_wczytania)
                    if len(surowe_dane) != bytes_do_wczytania:
                        raise ValueError(
                            f"Za mało danych pikseli w pliku P6 (2-bajtowym). Oczekiwano {bytes_do_wczytania}, wczytano {len(surowe_dane)}")

                    # Skalowanie liniowe (2 bajty -> 1 bajt)
                    idx_rgb = 0
                    for i in range(0, bytes_do_wczytania, 2):
                        # Big Endian
                        wartosc_16bit = (surowe_dane[i] << 8) | surowe_dane[i + 1]
                        dane_rgb[idx_rgb] = (wartosc_16bit * 255) // maxval
                        idx_rgb += 1

            # Utwórz obraz PIL z surowych danych RGB
            img = Image.frombytes('RGB', (w, h), bytes(dane_rgb))
            return img

    # --- NOWE: ZAPISYWANIE JAKO JPEG ---

    def zapisz_jako_jpeg(self):
        """Zapisuje aktualnie wczytany obraz jako plik JPEG."""
        if not self.obraz_oryginalny:
            messagebox.showwarning("Brak Obrazu", "Nie wczytano żadnego obrazu, który można by zapisać.")
            return

        sciezka_pliku = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG files", "*.jpg *.jpeg")]
        )
        if not sciezka_pliku: return

        # Pobierz jakość z suwaka
        jakosc = self.jakosc_jpeg.get()

        try:
            # Upewniamy się, że zapisujemy jako RGB (np. jeśli oryginał miał alfę)
            self.obraz_oryginalny.convert('RGB').save(sciezka_pliku, 'JPEG', quality=jakosc)
            print(f"Zapisano obraz do {sciezka_pliku} z jakością {jakosc}")
        except IOError as e:
            messagebox.showerror("Błąd Zapisu JPEG", f"Nie można zapisać pliku:\n{e}")
        except Exception as e:
            messagebox.showerror("Błąd Zapisu JPEG", f"Wystąpił nieoczekiwany błąd:\n{e}")

    # --- NOWE: OBSŁUGA POWIĘKSZANIA (ZOOM) ---

    def on_zoom_scroll(self, event):
        """Obsługuje powiększanie kółkiem myszy."""
        # Współrzędne kursora na płótnie (nie na ekranie)
        x = self.plotno.canvasx(event.x)
        y = self.plotno.canvasy(event.y)

        # Ustalenie współczynnika powiększenia
        factor = 0.0
        if event.num == 4 or event.delta > 0:  # Przewijanie w górę (zoom in)
            factor = 1.1
        elif event.num == 5 or event.delta < 0:  # Przewijanie w dół (zoom out)
            factor = 0.9

        if factor == 0.0: return  # Nieznane zdarzenie

        new_zoom_level = self.zoom_level * factor

        # Ograniczenie zoomu
        if new_zoom_level < 0.05 or new_zoom_level > 100:
            print(f"Osiągnięto limit zoomu: {new_zoom_level:.2f}")
            return

        # --- Skalowanie Rastrowe (Obrazu) ---
        if self.obraz_oryginalny and self.id_obrazu_na_plotnie:
            # 1. Pobierz stare współrzędne obrazu
            try:
                old_coords = self.plotno.coords(self.id_obrazu_na_plotnie)
                old_x, old_y = old_coords[0], old_coords[1]
            except (tk.TclError, IndexError):
                old_x, old_y = 0, 0  # Obraz mógł zostać usunięty, załóżmy (0,0)

            # 2. Oblicz nowe współrzędne obrazu (skalowanie względem kursora)
            new_img_x = (old_x - x) * factor + x
            new_img_y = (old_y - y) * factor + y

            # 3. Oblicz nowe wymiary obrazu
            new_width = int(self.obraz_oryginalny.width * new_zoom_level)
            new_height = int(self.obraz_oryginalny.height * new_zoom_level)

            if new_width > 0 and new_height > 0:
                try:
                    # Użyj 'NEAREST' dla wydajności i zachowania pikseli
                    resized_pil_img = self.obraz_oryginalny.resize((new_width, new_height), Image.NEAREST)

                    # Zaktualizuj obraz
                    self.obraz_wyswietlany = ImageTk.PhotoImage(resized_pil_img)
                    self.plotno.delete(self.id_obrazu_na_plotnie)

                    self.id_obrazu_na_plotnie = self.plotno.create_image(
                        new_img_x, new_img_y,
                        anchor=tk.NW,
                        image=self.obraz_wyswietlany
                    )
                    self.plotno.lower(self.id_obrazu_na_plotnie)
                except Exception as e:
                    print(f"Błąd podczas skalowania obrazu: {e}")
                    # Nie przerywaj, przynajmniej wektory się przeskalują

        # --- Skalowanie Wektorowe ---
        # Skaluj tylko elementy wektorowe (po obrazie, aby nie skalować obrazu)
        self.plotno.scale("vector", x, y, factor, factor)

        # Zapisz nowy zoom
        self.zoom_level = new_zoom_level

        # Zaktualizuj wyświetlanie RGB
        self.aktualizuj_rgb_na_pikselach()

    # --- NOWE: OBSŁUGA PANORAMY (PAN) ---

    def on_pan_start(self, event):
        """Rozpoczyna przesuwanie widoku (naciśnięcie środkowego przycisku)."""
        self.plotno.scan_mark(event.x, event.y)
        self.czysc_rgb_na_pikselach()  # Ukryj tekst podczas przesuwania

    def on_pan_move(self, event):
        """Przesuwa widok płótna."""
        self.plotno.scan_dragto(event.x, event.y, gain=1)

    def on_pan_release(self, event):
        """Kończy przesuwanie i aktualizuje widok RGB."""
        self.aktualizuj_rgb_na_pikselach()

    # --- NOWE: WYŚWIETLANIE WARTOŚCI PIKSELI RGB ---

    def czysc_rgb_na_pikselach(self):
        """Usuwa stary tekst RGB z płótna."""
        for text_id in self.id_tekstow_rgb:
            self.plotno.delete(text_id)
        self.id_tekstow_rgb.clear()

    def aktualizuj_rgb_na_pikselach(self):
        """Wyświetla wartości R,G,B na pikselach przy dużym powiększeniu."""
        self.czysc_rgb_na_pikselach()

        # Wymagania: musi być wczytany obraz i musi być duże powiększenie
        if not self.obraz_oryginalny or self.zoom_level < 20 or not self.id_obrazu_na_plotnie:
            return

        # 1. Znajdź pozycję obrazu na płótnie
        try:
            img_coords = self.plotno.coords(self.id_obrazu_na_plotnie)
            img_x_on_canvas, img_y_on_canvas = img_coords[0], img_coords[1]
        except (tk.TclError, IndexError):
            print("Nie można znaleźć współrzędnych obrazu do rysowania RGB.")
            return

        # 1b. Znajdź widoczny obszar płótna
        x_min = self.plotno.canvasx(0)
        y_min = self.plotno.canvasy(0)
        x_max = self.plotno.canvasx(self.plotno.winfo_width())
        y_max = self.plotno.canvasy(self.plotno.winfo_height())

        # 2. Przelicz na współrzędne obrazu (piksele)
        # Obraz zaczyna się w (0,0) na płótnie.
        # wspolrzedna_obrazu = (wspolrzedna_plótna - pozycja_obrazu_na_plotnie) / zoom_level

        img_x_start = max(0, int((x_min - img_x_on_canvas) / self.zoom_level))
        img_y_start = max(0, int((y_min - img_y_on_canvas) / self.zoom_level))
        img_x_end = min(self.obraz_oryginalny.width, int((x_max - img_x_on_canvas) / self.zoom_level) + 1)
        img_y_end = min(self.obraz_oryginalny.height, int((y_max - img_y_on_canvas) / self.zoom_level) + 1)

        # 3. Ograniczenie wydajności: nie rysuj, jeśli widać za dużo pikseli
        liczba_pikseli = (img_x_end - img_x_start) * (img_y_end - img_y_start)
        if liczba_pikseli > 500:  # Bezpieczny limit
            print(f"Pomijanie rysowania RGB: zbyt wiele pikseli w widoku ({liczba_pikseli})")
            return

        # 4. Pobierz piksele i narysuj tekst
        # (Optymalizacja: wczytaj cały widoczny region na raz)
        try:
            widoczny_region = self.obraz_oryginalny.crop((img_x_start, img_y_start, img_x_end, img_y_end))
            piksele = widoczny_region.load()
        except Exception as e:
            print(f"Błąd przy pobieraniu pikseli: {e}")
            return

        font_size = max(1, min(6, int(self.zoom_level / 4)))
        font = ("Arial", font_size)

        for y in range(widoczny_region.height):
            for x in range(widoczny_region.width):
                img_x = img_x_start + x
                img_y = img_y_start + y

                try:
                    r, g, b = piksele[x, y]
                except IndexError:
                    continue  # Na krawędziach

                text = f"{r}\n{g}\n{b}"

                # Znajdź środek piksela na płótnie
                # pozycja_srodka_piksela_w_obrazie = (img_x + 0.5)
                # pozycja_na_plotnie = pozycja_w_obrazie * zoom + przesuniecie_obrazu
                canvas_x = (img_x + 0.5) * self.zoom_level + img_x_on_canvas
                canvas_y = (img_y + 0.5) * self.zoom_level + img_y_on_canvas

                # Stwórz tekst
                text_id = self.plotno.create_text(
                    canvas_x, canvas_y,
                    text=text,
                    font=font,
                    fill="black",
                    tags="pixel_rgb_text"
                )
                self.id_tekstow_rgb.append(text_id)


# --- URUCHOMIENIE APLIKACJI ---

def main():
    root = tk.Tk()
    app = EdytorGraficzny(root)
    root.mainloop()


if __name__ == "__main__":
    main()

