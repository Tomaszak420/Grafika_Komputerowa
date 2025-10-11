import tkinter as tk
from tkinter import ttk, colorchooser, filedialog
import json
import math


# --- DEFINICJE KLAS KSZTAŁTÓW ---

class Kształt:
    """ Klasa bazowa dla wszystkich figur geometrycznych. """

    def __init__(self):
        self.id_na_plotnie = None

    def rysuj(self, plotno):
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
            plotno.delete(self.id_na_plotnie)
        self.id_na_plotnie = plotno.create_line(
            self.x1, self.y1, self.x2, self.y2,
            fill=kolor_konturu or self.kolor, width=3
        )

    def zawiera_punkt(self, x, y):
        # Sprawdzenie, czy punkt leży blisko odcinka linii
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
            plotno.delete(self.id_na_plotnie)
        self.id_na_plotnie = plotno.create_rectangle(
            self.x1, self.y1, self.x2, self.y2,
            outline=kolor_konturu or self.kolor_konturu, fill=self.kolor_wypelnienia, width=2
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


class Okrag(Prostokat):  # Okrąg dziedziczy po prostokącie, bo ma te same atrybuty i metody
    def __init__(self, x1, y1, x2, y2, kolor_konturu='blue', kolor_wypelnienia=''):
        super().__init__(x1, y1, x2, y2, kolor_konturu, kolor_wypelnienia)
        self.typ = 'okrag'

    def rysuj(self, plotno, kolor_konturu=None):
        if self.id_na_plotnie:
            plotno.delete(self.id_na_plotnie)
        self.id_na_plotnie = plotno.create_oval(
            self.x1, self.y1, self.x2, self.y2,
            outline=kolor_konturu or self.kolor_konturu, fill=self.kolor_wypelnienia, width=2
        )


# --- GŁÓWNA KLASA APLIKACJI ---

class EdytorGraficzny:
    def __init__(self, root):
        self.root = root
        self.root.title("Prymitywny Edytor Graficzny")

        # --- Zmienne Stanu (MUSZĄ BYĆ ZDEFINIOWANE PRZED TWORZENIEM WIDŻETÓW) ---
        self.ksztalty = []
        self.tryb = tk.StringVar(value="rysuj")
        self.wybrany_typ_ksztaltu = tk.StringVar(value="linia")

        self.start_x, self.start_y = None, None
        self.ostatni_x, self.ostatni_y = 0, 0

        self.aktualny_ksztalt_rysowany = None
        self.zaznaczony_obiekt = None
        self.kolor_zaznaczenia = 'red'

        # --- Interfejs Użytkownika ---
        self.ramka_narzedzi = tk.Frame(root, relief=tk.RAISED, borderwidth=2)
        self.ramka_narzedzi.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        self.stworz_przybornik()

        self.plotno = tk.Canvas(root, bg="white", width=800, height=600)
        self.plotno.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.bind_events()

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

        # --- Sekcja Pliku ---
        ttk.Button(self.ramka_narzedzi, text="Zapisz", command=self.zapisz_do_pliku).pack(fill='x', pady=2)
        ttk.Button(self.ramka_narzedzi, text="Wczytaj", command=self.wczytaj_z_pliku).pack(fill='x', pady=2)

    def bind_events(self):
        self.plotno.bind("<ButtonPress-1>", self.on_press)
        self.plotno.bind("<B1-Motion>", self.on_drag)
        self.plotno.bind("<ButtonRelease-1>", self.on_release)

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
        self.start_x, self.start_y = event.x, event.y
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
            self.aktualny_ksztalt_rysowany.x2, self.aktualny_ksztalt_rysowany.y2 = event.x, event.y
            self.aktualny_ksztalt_rysowany.rysuj(self.plotno)

    def on_release_rysuj(self, event):
        if self.aktualny_ksztalt_rysowany:
            self.on_drag_rysuj(event)
            self.ksztalty.append(self.aktualny_ksztalt_rysowany)
            self.aktualny_ksztalt_rysowany = None

    # --- METODY DLA TRYBU EDYCJI ---
    def on_press_edytuj(self, event):
        self.ostatni_x, self.ostatni_y = event.x, event.y
        obiekt_do_zaznaczenia = None
        # Szukamy od końca, aby zaznaczyć obiekt na wierzchu
        for obiekt in reversed(self.ksztalty):
            if obiekt.zawiera_punkt(event.x, event.y):
                obiekt_do_zaznaczenia = obiekt
                break
        self.zaznacz_obiekt(obiekt_do_zaznaczenia)

    def on_drag_edytuj(self, event):
        if self.zaznaczony_obiekt:
            dx = event.x - self.ostatni_x
            dy = event.y - self.ostatni_y
            self.zaznaczony_obiekt.przesun(dx, dy)
            self.zaznaczony_obiekt.rysuj(self.plotno, kolor_konturu=self.kolor_zaznaczenia)
            self.ostatni_x, self.ostatni_y = event.x, event.y
            self.aktualizuj_pola_edycji(self.zaznaczony_obiekt)

    def on_release_edytuj(self, event):
        pass  # Nic specjalnego nie trzeba robić

    def zaznacz_obiekt(self, obiekt):
        # Odznacz poprzedni obiekt
        if self.zaznaczony_obiekt and self.zaznaczony_obiekt in self.ksztalty:
            self.zaznaczony_obiekt.rysuj(self.plotno)  # Przerysuj w normalnym kolorze

        self.zaznaczony_obiekt = obiekt

        # Zaznacz nowy obiekt
        if self.zaznaczony_obiekt:
            self.zaznaczony_obiekt.rysuj(self.plotno, kolor_konturu=self.kolor_zaznaczenia)

        self.aktualizuj_pola_edycji(obiekt)

    def aktualizuj_pola_edycji(self, obiekt):
        if obiekt:
            self.pola_edycji['x1'].delete(0, tk.END);
            self.pola_edycji['x1'].insert(0, obiekt.x1)
            self.pola_edycji['y1'].delete(0, tk.END);
            self.pola_edycji['y1'].insert(0, obiekt.y1)
            self.pola_edycji['x2'].delete(0, tk.END);
            self.pola_edycji['x2'].insert(0, obiekt.x2)
            self.pola_edycji['y2'].delete(0, tk.END);
            self.pola_edycji['y2'].insert(0, obiekt.y2)
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
            print("Błąd: Wprowadź prawidłowe liczby całkowite jako współrzędne.")

    # --- SERIALIZACJA I DESERIALIZACJA ---
    def zapisz_do_pliku(self):
        sciezka_pliku = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not sciezka_pliku: return
        dane_do_zapisu = [ksztalt.to_dict() for ksztalt in self.ksztalty]
        with open(sciezka_pliku, 'w') as f: json.dump(dane_do_zapisu, f, indent=4)
        print(f"Zapisano rysunek do pliku {sciezka_pliku}")

    def wczytaj_z_pliku(self):
        sciezka_pliku = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not sciezka_pliku: return
        try:
            with open(sciezka_pliku, 'r') as f:
                dane_z_pliku = json.load(f)
        except FileNotFoundError:
            print(f"Plik {sciezka_pliku} nie istnieje.");
            return

        self.plotno.delete("all");
        self.ksztalty.clear();
        self.zaznacz_obiekt(None)
        mapa_klas = {'linia': Linia, 'prostokat': Prostokat, 'okrag': Okrag}

        for dane_ksztaltu in dane_z_pliku:
            klasa_ksztaltu = mapa_klas.get(dane_ksztaltu['typ'])
            if klasa_ksztaltu:
                nowy_ksztalt = klasa_ksztaltu.from_dict(dane_ksztaltu)
                self.ksztalty.append(nowy_ksztalt)
                nowy_ksztalt.rysuj(self.plotno)
        print(f"Wczytano rysunek z pliku {sciezka_pliku}.")


def main():
    root = tk.Tk()
    app = EdytorGraficzny(root)
    root.mainloop()


if __name__ == "__main__":
    main()