import tkinter as tk  # Import modułu do tworzenia interfejsu graficznego
from itertools import product  # Import funkcji do generowania kombinacji elementów
import random  # Import modułu do generowania losowych liczb i operacji losowych
import os  # Import modułu do operacji na systemie plików
from PIL import Image, ImageDraw  # Import modułów do generowania i manipulacji obrazami
import matplotlib.pyplot as plt  # Import modułu do tworzenia wykresów
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # Import modułu do renderowania wykresów w Tkinter

# Generowanie punktów reprezentujących bogatych i biednych mieszkańców
def generate_rich_poor_points(num_points):
    # Utworzenie listy wszystkich możliwych punktów na planszy 40x40
    all_points = list(product(range(40), range(40)))
    # Sprawdzenie, czy liczba punktów nie przekracza maksymalnej liczby miejsc
    if num_points > len(all_points):
        raise ValueError("Liczba punktów przekracza liczbę dostępnych miejsc na planszy.")
    random.shuffle(all_points)
    # Podział punktów na dwie grupy: bogatych i biednych
    rich_points = set(all_points[:num_points // 2])
    poor_points = set(all_points[num_points // 2:num_points])
    # Utworzenie zbioru pustych miejsc
    empty_spots = set(all_points) - rich_points - poor_points
    return rich_points, poor_points, empty_spots

# Liczenie sąsiadów danego punktu
def count_neighbors(point, points_set):
    # Obliczanie pozycji sąsiadujących punktów
    x, y = point
    neighbors = [(x + i, y + j) for i in range(-1, 2) for j in range(-1, 2)
                 if (i != 0 or j != 0) and (0 <= x + i < 40) and (0 <= y + j < 40)]
    # Zliczanie sąsiadów należących do podanego zbioru punktów
    return sum(neighbor in points_set for neighbor in neighbors)

# Sprawdzanie tolerancji mieszkańców względem sąsiadów
def check_tolerance(point, rich_points, poor_points, tolerance, is_rich):
    x, y = point
    total_neighbors = 8  # Maksymalna liczba sąsiadów dla każdego punktu
    num_rich_neighbors = count_neighbors(point, rich_points)
    num_poor_neighbors = count_neighbors(point, poor_points)

    # Uwzględnienie brakujących sąsiadów, jeśli punkt jest na krawędzi lub w rogu
    num_neighbors = num_rich_neighbors + num_poor_neighbors
    if num_neighbors < total_neighbors:
        if is_rich:
            num_rich_neighbors += total_neighbors - num_neighbors
        else:
            num_poor_neighbors += total_neighbors - num_neighbors

    # Obliczanie procentu niepodobnych sąsiadów i sprawdzenie tolerancji
    percent_unlike_neighbors = (num_poor_neighbors if is_rich else num_rich_neighbors) / total_neighbors
    return percent_unlike_neighbors <= tolerance

# Przemieszczanie punktów na podstawie ich tolerancji
def move_points(rich_points, poor_points, empty_spots, tolerance_rich, tolerance_poor):
    moved = False
    for point_set, tolerance, is_rich in [(rich_points, tolerance_rich, True), (poor_points, tolerance_poor, False)]:
        for point in list(point_set):
            if not check_tolerance(point, rich_points, poor_points, tolerance, is_rich):
                best_new_point = None
                best_new_tolerance = float('inf')
                lowest_opposite_neighbors = float('inf')

                # Sprawdzanie wolnych miejsc w pobliżu
                nearby_empty_spots = [p for p in empty_spots if is_nearby(p, point)]
                for new_point in nearby_empty_spots:
                    point_set.add(new_point)
                    empty_spots.remove(new_point)

                    # Sprawdzanie liczby sąsiadów przeciwnej grupy
                    opposite_neighbors = count_neighbors(new_point, poor_points if is_rich else rich_points)
                    if opposite_neighbors < lowest_opposite_neighbors:
                        if best_new_point:
                            point_set.remove(best_new_point)
                            empty_spots.add(best_new_point)
                        best_new_point = new_point
                        lowest_opposite_neighbors = opposite_neighbors
                    else:
                        point_set.remove(new_point)
                        empty_spots.add(new_point)

                # Aktualizacja punktu, jeśli znaleziono lepsze miejsce
                if best_new_point:
                    point_set.remove(point)
                    empty_spots.add(point)
                    moved = True
                else:
                    point_set.add(point)  # Przywrócenie pierwotnego punktu, jeśli nie znaleziono lepszego miejsca
    return moved

# Sprawdzanie, czy dwa punkty są w pobliżu siebie
def is_nearby(point1, point2, distance=5):
    # Obliczanie odległości pomiędzy dwoma punktami
    x1, y1 = point1
    x2, y2 = point2
    return abs(x1 - x2) <= distance and abs(y1 - y2) <= distance

# Rysowanie planszy z aktualnym rozmieszczeniem mieszkańców
def draw_grid(window, rich_points, poor_points):
    # Czyszczenie poprzednich elementów w oknie
    for widget in window.winfo_children():
        widget.destroy()
    # Rysowanie komórek reprezentujących mieszkańców
    for i in range(40):
        for j in range(40):
            color = 'white'  # Domyślny kolor dla pustych miejsc
            if (i, j) in rich_points:
                color = 'green'  # Kolor dla bogatych mieszkańców
            elif (i, j) in poor_points:
                color = 'red'    # Kolor dla biednych mieszkańców
            frame = tk.Frame(window, bg=color, width=20, height=20)
            frame.grid(row=i, column=j)

# Zapisywanie obrazu planszy z aktualnym rozmieszczeniem mieszkańców
def save_image(rich_points, poor_points, num_points, tolerance_rich, tolerance_poor, image_num):
    image_size = 40
    cell_size = image_size // 40
    img = Image.new('RGB', (image_size, image_size), color='white')
    draw = ImageDraw.Draw(img)

    for i in range(40):
        for j in range(40):
            if (i, j) in rich_points:
                color = 'green'
            elif (i, j) in poor_points:
                color = 'red'
            else:
                color = 'white'
            # Rysowanie prostokąta na obrazie reprezentującego mapę miasta.  Współrzędne prostokąta są obliczane na podstawie indeksów pętli (i, j) i rozmiaru komórki (cell_size).
            draw.rectangle([i * cell_size, j * cell_size, (i + 1) * cell_size, (j + 1) * cell_size], fill=color)

    # Zapisywanie obrazu na pulpicie użytkownika w odpowiednim folderze
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    os.makedirs(os.path.join(desktop_path, 'generated_images'), exist_ok=True)
    filename = f'image_{num_points}_rich{tolerance_rich}_poor{tolerance_poor}_num{image_num}.png'
    img.save(os.path.join(desktop_path, 'generated_images', filename))

# Funkcja do generowania serii obrazów dla różnych parametrów
def batch_generate_images():
    for num_points in range(800, 1401, 150):
        for tolerance in [i / 8 for i in range(1, 9)]:
            for image_num in range(500):
                rich_points, poor_points, empty_spots = generate_rich_poor_points(num_points)
                max_iterations = 50
                for _ in range(max_iterations):
                    if not move_points(rich_points, poor_points, empty_spots, tolerance, tolerance):
                        break
                save_image(rich_points, poor_points, num_points, tolerance, tolerance, image_num)

# Funkcja do zapisywania animacji jako pliku GIF
def save_gif(frames, filename):
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    city_gif_path = os.path.join(desktop_path, 'city-gif')
    os.makedirs(city_gif_path, exist_ok=True)
    frames[0].save(os.path.join(city_gif_path, filename), format='GIF',
                   append_images=frames[1:], save_all=True, duration=300, loop=0)

# Rysowanie planszy jako obrazu PIL
def draw_grid_to_image(rich_points, poor_points):
    image_size = 800
    cell_size = image_size // 40
    img = Image.new('RGB', (image_size, image_size), color='white')
    draw = ImageDraw.Draw(img)

    for i in range(40):
        for j in range(40):
            color = 'white'
            if (i, j) in rich_points:
                color = 'green'
            elif (i, j) in poor_points:
                color = 'red'
            # Rysowanie prostokąta na obrazie reprezentującego mapę miasta.  Współrzędne prostokąta są obliczane na podstawie indeksów pętli (i, j) i rozmiaru komórki (cell_size).
            draw.rectangle([i * cell_size, j * cell_size, (i + 1) * cell_size, (j + 1) * cell_size], fill=color)

    return img

# Obliczanie procentowego zadowolenia grupy mieszkańców
def calculate_satisfaction(points_set, rich_points, poor_points, tolerance, is_rich):
    satisfied = sum(check_tolerance(point, rich_points, poor_points, tolerance, is_rich) for point in points_set)
    satisfaction_percent = (satisfied / len(points_set) * 100) if points_set else 0
    return round(satisfaction_percent)  # Zaokrąglenie do najbliższej liczby całkowitej

# Funkcja do animowania przemieszczania się mieszkańców
def animate_movement(rich_points, poor_points, empty_spots, tolerance_rich, tolerance_poor, animation_window, chart_fig, chart_ax):
    max_iterations = 100
    frames = []  # Lista do przechowywania klatek do GIFa
    satisfaction_data = [[], [], []]  # Lista do przechowywania danych wykresu

    for iteration in range(max_iterations):
        moved = move_points(rich_points, poor_points, empty_spots, tolerance_rich, tolerance_poor)
        draw_grid(animation_window, rich_points, poor_points)
        frame = draw_grid_to_image(rich_points, poor_points)
        frames.append(frame)
        animation_window.update_idletasks()
        animation_window.update()

        # Obliczanie zadowolenia dla każdej grupy
        rich_satisfaction = calculate_satisfaction(rich_points, rich_points, poor_points, tolerance_rich, True)
        poor_satisfaction = calculate_satisfaction(poor_points, rich_points, poor_points, tolerance_poor, False)

        satisfaction_data[0].append(iteration)
        satisfaction_data[1].append(rich_satisfaction)
        satisfaction_data[2].append(poor_satisfaction)

        chart_ax.clear()
        chart_ax.plot(satisfaction_data[0], satisfaction_data[1], label='Zadowolenie Bogatych (%)')
        chart_ax.plot(satisfaction_data[0], satisfaction_data[2], label='Zadowolenie Biednych (%)')
        chart_ax.set_xlabel('Iteracja')
        chart_ax.set_ylabel('Zadowolenie (%)')
        chart_ax.legend()
        chart_fig.canvas.draw()

        if not moved:
            break

    return frames, satisfaction_data

# Funkcja do tworzenia okna animacji i modyfikacji wykresu miasta
def create_animation_window(num_points, tolerance_rich_entry, tolerance_poor_entry):
    global rich_points, poor_points, empty_spots, animation_window

    # Tworzenie okna animacji
    animation_window = tk.Toplevel()
    animation_window.title("Animacja Ruchu Punktów")

    # Tworzenie okna z wykresem
    chart_window = tk.Toplevel()
    chart_window.title("Wykres Tolerancji")

    # Inicjalizacja wykresu
    chart_fig, chart_ax = plt.subplots()
    canvas = FigureCanvasTkAgg(chart_fig, master=chart_window)
    canvas.get_tk_widget().pack()

    # Tworzenie ramki pod wykresem z przyciskami do dodawania/usuwania mieszkańców
    button_frame = tk.Frame(chart_window)
    button_frame.pack()

    # Generowanie początkowego rozmieszczenia bogatych, biednych i pustych miejsc
    rich_points, poor_points, empty_spots = generate_rich_poor_points(num_points)

    # Pobieranie wartości tolerancji z pól Entry i konwersja na float
    tolerance_rich = float(tolerance_rich_entry.get())
    tolerance_poor = float(tolerance_poor_entry.get())

    # Rozpoczęcie animacji i zapis do pliku GIF
    frames, satisfaction_data = animate_movement(rich_points, poor_points, empty_spots, tolerance_rich, tolerance_poor,
                                                 animation_window, chart_fig, chart_ax)
    gif_filename = f'animation_{num_points}_rich{tolerance_rich}_poor{tolerance_poor}.gif'
    save_gif(frames, gif_filename)

    # Dodawanie przycisków do interakcji z mieszkańcami (dodawanie/usuwanie)
    add_rich_button = tk.Button(button_frame, text="Dodaj Bogatego", command=lambda: add_remove_resident('add', 'rich'))
    add_rich_button.pack(side='left')

    remove_rich_button = tk.Button(button_frame, text="Usuń Bogatego",
                                   command=lambda: add_remove_resident('remove', 'rich'))
    remove_rich_button.pack(side='left')

    add_poor_button = tk.Button(button_frame, text="Dodaj Biednego", command=lambda: add_remove_resident('add', 'poor'))
    add_poor_button.pack(side='right')

    remove_poor_button = tk.Button(button_frame, text="Usuń Biednego",
                                   command=lambda: add_remove_resident('remove', 'poor'))
    remove_poor_button.pack(side='right')

    animation_window.mainloop()

# Funkcja do dodawania i usuwania mieszkańców z symulacji
def add_remove_resident(action, group):
    global rich_points, poor_points, empty_spots

    if action == 'add' and empty_spots:
        point = random.choice(list(empty_spots))
        empty_spots.remove(point)
        if group == 'rich':
            rich_points.add(point)
        else:
            poor_points.add(point)

    elif action == 'remove':
        if group == 'rich' and rich_points:
            point = random.choice(list(rich_points))
            rich_points.remove(point)
            empty_spots.add(point)
        elif group == 'poor' and poor_points:
            point = random.choice(list(poor_points))
            poor_points.remove(point)
            empty_spots.add(point)

    # Ponowne sprawdzenie tolerancji i aktualizacja planszy
    move_points(rich_points, poor_points, empty_spots, float(tolerance_rich_entry.get()),
                float(tolerance_poor_entry.get()))
    draw_grid(animation_window, rich_points, poor_points)


# Funkcja do inicjalizacji okna głównego aplikacji
def create_grid():
    num_points = int(num_points_entry.get())
    tolerance_rich = float(tolerance_rich_entry.get())
    tolerance_poor = float(tolerance_poor_entry.get())

    create_animation_window(num_points, tolerance_rich_entry, tolerance_poor_entry)

# Tworzenie głównego okna aplikacji
root = tk.Tk()
root.title("Mapa miasta")

# Tworzenie etykiety i pola do wprowadzenia liczby mieszkańców
tk.Label(root, text="Liczba mieszkańców:").grid(row=0, column=0)
num_points_entry = tk.Entry(root)
num_points_entry.grid(row=0, column=1)
num_points_entry.insert(0, "1200")  # Wartość domyślna

# Tworzenie etykiety i pola do wprowadzenia tolerancji bogatych mieszkańców
tk.Label(root, text="Tolerancja bogatych:").grid(row=1, column=0)
tolerance_rich_entry = tk.Entry(root)
tolerance_rich_entry.grid(row=1, column=1)
tolerance_rich_entry.insert(0, "0.5")  # Wartość domyślna

# Tworzenie etykiety i pola do wprowadzenia tolerancji biednych mieszkańców
tk.Label(root, text="Tolerancja biednych:").grid(row=2, column=0)
tolerance_poor_entry = tk.Entry(root)
tolerance_poor_entry.grid(row=2, column=1)
tolerance_poor_entry.insert(0, "0.5")  # Wartość domyślna

# Tworzenie przycisku do generowania wykresu na podstawie wprowadzonych danych
generate_button = tk.Button(root, text="Generuj wykres", command=create_grid)
generate_button.grid(row=3, column=0, columnspan=2)

# Tworzenie przycisku do generowania obrazów w trybie wsadowym
batch_generate_button = tk.Button(root, text="Generuj obrazy", command=batch_generate_images)
batch_generate_button.grid(row=5, column=0, columnspan=2)

# Rozpoczęcie głównej pętli aplikacji
root.mainloop()