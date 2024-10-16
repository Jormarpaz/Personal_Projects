from datetime import datetime
from tkinter import ttk, messagebox
from cripto_dic import criptos
from cripto_dic_grf import criptos_grf
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import tkinter as tk
import requests
import sqlite3
import time
import pywinstyles
import sys
import sv_ttk
import threading
import queue

###
# Funciones principales
###


def conectar_db():
    # Conectar a la base de datos
    conexion = sqlite3.connect('mis_precios.db')
    return conexion


def crear_tabla():
    conexion = conectar_db()
    cursor = conexion.cursor()

    # Crear la tabla si no existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        cantidad REAL NOT NULL DEFAULT 0,
        precio_compra REAL NOT NULL,
        fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conexion.commit()
    conexion.close()


### Función para leer el valor de una criptomoneda(se ejecuta en un hilo)
def obtener_precio_binance_threading(symbol, resultado):
    threading.Thread(target=obtener_precio_binance, args=(symbol, resultado), daemon=True).start()

def obtener_precio_binance(symbol, resultado):
    try:
        if symbol is None:
            print(f"Símbolo base para '{
                  symbol}' no encontrado en el diccionario.")
            resultado.put(None)
            return 
        url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
        response = requests.get(url)
        data = response.json()
        resultado.put(float(data['price']))
    except (requests.RequestException, ValueError, KeyError):
        print(f"Error al obtener el precio de {symbol}")
        resultado.put(None)

### Función para leer el valor historico de una criptomoneda(se ejecuta en un hilo)
def obtener_precio_historico_threading(symbol, timestamp, resultado):
    threading.Thread(target=obtener_precio_historico, args=(symbol, timestamp, resultado), daemon=True).start()

def obtener_precio_historico(symbol, timestamp, resultado):
    try:
        if symbol is None:
            print(f"Símbolo base para '{
                  symbol}' no encontrado en el diccionario.")
            resultado.put(None)
            return 
        url = f'https://api.binance.com/api/v3/klines?symbol={
            symbol}&interval=1h&limit=1&startTime={timestamp}'
        response = requests.get(url)
        data = response.json()

        # El precio de cierre del intervalo es el quinto valor de los datos de la vela
        precio_cierre = float(data[0][4]) if data else None
        resultado.put(precio_cierre)
    except (requests.RequestException, ValueError, KeyError):
        print(f"Error al obtener el precio histórico de {symbol}")
        resultado.put(None)

def obtener_precio_historico_grafica(crypto_id, dias=1):
    url = f'https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart'
    params = {
        'vs_currency': 'usd',
        'days': dias,
    }
    response = requests.get(url, params=params)

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error al acceder a la API: {response.status_code} - {response.text}")

    data = response.json()

    print(data)

    if 'prices' in data:
        return data['prices']
    else:
        raise ValueError("La respuesta de la API no contiene la clave 'prices'")

###

###
# Graficar precios históricos
###

def graficar_precio(crypto_id, crypto_sym):
    precios = obtener_precio_historico_grafica(crypto_id, dias=1)
    tiempos = [datetime.fromtimestamp(p[0] / 1000) for p in precios]
    valores = [p[1] for p in precios]
    
    plt.figure(figsize=(10, 5))
    
    # Cambiar el fondo
    plt.gca().set_facecolor('black')  # Fondo del área del gráfico
    plt.gcf().patch.set_facecolor('black')  # Fondo de la figura
    
    # Graficar líneas cambiando el color
    for i in range(len(valores) - 1):
        color = 'green' if valores[i] < valores[i + 1] else 'red'
        plt.plot(tiempos[i:i + 2], valores[i:i + 2], color=color)

    plt.xlabel('Mes/Día/Hora', color='white')
    plt.ylabel('Precio (USD)', color='white')
    plt.title(f'Precio Histórico de {crypto_sym.upper()}', color='white')
    plt.grid(True, color='gray')
    # Añadir leyenda
    plt.plot([], [], color='green', label='Subiendo')  # Placeholder para la leyenda
    plt.plot([], [], color='red', label='Bajando')     # Placeholder para la leyenda
    legend = plt.legend(loc='upper right', fontsize='small', facecolor='black', edgecolor='white', framealpha=0.7)

    # Cambiar el color del texto de la leyenda a blanco
    for text in legend.get_texts():
        text.set_color('white')
    
    # Cambiar el color de los ticks
    plt.tick_params(axis='x', colors='white')
    plt.tick_params(axis='y', colors='white')
    plt.show()
    
###

###
# Funciones para añadir y eliminar criptomonedas
###

### Función para agregar una criptomoneda a la base de datos (se ejecuta en un hilo)
def agregar_nueva_cripto_threaded(nombre, cantidad, precio_compra):
    threading.Thread(target=agregar_nueva_cripto, args=(nombre, cantidad, precio_compra), daemon=True).start()

def agregar_nueva_cripto(nombre, precio_compra, cantidad):
    conexion = conectar_db()
    cursor = conexion.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    nombre = nombre.lower()

    try:
        cursor.execute('INSERT INTO compras (nombre, precio_compra, cantidad, fecha) VALUES (?, ?, ?, ?)',
                   (nombre, precio_compra, cantidad, fecha_actual))
        conexion.commit()
        print(f"Criptomoneda {nombre} añadida correctamente.")
    except sqlite3.Error as e:
        print(f"Error al agregar la criptomoneda: {e}")
        messagebox.showerror("Error", f"No se pudo agregar la criptomoneda: {e}")
    finally:
        if conexion:
            conexion.close()


# Añadir nueva criptomoneda

def agregar_nueva_cripto_gui(tree, cripto=None):
    def agregar():
        if cripto is not None:
            nombre = cripto.lower().strip()
        else:
            nombre = nombre_entry.get().lower().strip()
        cantidad = float(cantidad_entry.get())
        precio_compra = float(precio_entry.get())

        if nombre and precio_compra and cantidad:
            try:
                cantidad = float(cantidad)
                precio_compra = float(precio_compra)

                nombre_base = nombre
                contador = 1

                while nombre_exists(nombre):
                    contador += 1
                    nombre = f"{nombre_base}_{contador}"

                agregar_nueva_cripto_threaded(nombre, precio_compra, cantidad)
                messagebox.showinfo(
                    "Éxito", "Criptomoneda añadida exitosamente.")
                mostrar_comparacion(tree)
                top.destroy()
            except ValueError:
                messagebox.showerror(
                    "Error", "El precio de compra debe ser un número.")
        else:
            messagebox.showerror(
                "Error", "El nombre, el precio de compra y/o la cantidad no pueden estar vacíos.")

    top = tk.Toplevel()
    top.title("Añadir Criptomoneda")

    if cripto is not None:
        tk.Label(top, text=f"Nombre: {cripto.capitalize()}").pack(pady=(10, 0))
    else:
        tk.Label(top, text="Nombre:").pack(pady=(10, 0))
        nombre_entry = tk.Entry(top)
        nombre_entry.pack()

    tk.Label(top, text="Cantidad:").pack()
    cantidad_entry = tk.Entry(top)
    cantidad_entry.pack()

    tk.Label(top, text="Precio de Compra:").pack()
    precio_entry = tk.Entry(top)
    precio_entry.pack()

    tk.Button(top, text="Añadir", command=agregar).pack(pady=(10, 10))

    top.geometry("300x175")


def nombre_exists(nombre):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT COUNT(*) FROM compras WHERE nombre = ?', (nombre,))
    existe = cursor.fetchone()[0] > 0
    conexion.close()
    return existe

###

# Eliminar criptomoneda

### Función para eliminar una criptomoneda (se ejecuta en un hilo)
def eliminar_cripto_threaded(nombre):
    threading.Thread(target=eliminar_cripto, args=(nombre,), daemon=True).start()


def eliminar_cripto(nombre):
    try:
        conexion = conectar_db()
        if conexion is None:
            print("Error: No se pudo conectar a la base de datos.")
            return

        cursor = conexion.cursor()
        nombre = nombre.lower().strip()

        # Verifica si la criptomoneda existe antes de intentar eliminarla
        cursor.execute(
            'SELECT COUNT(*) FROM compras WHERE nombre = ?', (nombre,))
        if cursor.fetchone()[0] == 0:
            print(f"La criptomoneda '{nombre}' no existe en la base de datos.")
            return

        cursor.execute('DELETE FROM compras WHERE nombre = ?', (nombre,))
        conexion.commit()
        print(f"Criptomoneda '{nombre}' eliminada exitosamente.")
    except (sqlite3.Error, ValueError) as e:
        print(f"Error al eliminar la criptomoneda: {e}")
        messagebox.showerror("Error", f"No se pudo eliminar la criptomoneda: {e}")
    finally:
        if conexion:
            conexion.close()


def obtener_criptos_activos():
    """Obtener una lista de criptomonedas activas de la base de datos."""
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT nombre FROM compras')
    criptos = cursor.fetchall()
    conexion.close()
    return [cripto[0].capitalize() for cripto in criptos]


def eliminar_cripto_gui(tree):
    def eliminar():
        seleccion = listbox.curselection()
        if seleccion:
            try:
                if messagebox.askyesno("Confirmar", "¿Estás seguro de que deseas eliminar esta cripto?"):
                    nombre = listbox.get(seleccion[0]).strip()
                    try:
                        eliminar_cripto_threaded(nombre)
                        messagebox.showinfo(
                            "Éxito", "Criptomoneda eliminada exitosamente.")
                    except Exception as e:
                        print(f"Error al eliminar la criptomoneda: {e}")
                    mostrar_comparacion(tree)
                    top.destroy()
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Error al eliminar la criptomoneda: {e}")
        else:
            messagebox.showerror(
                "Error", "Debes seleccionar una criptomoneda para eliminar.")

    top = tk.Toplevel()
    top.title("Eliminar Criptomoneda")

    tk.Label(top, text="Selecciona una criptomoneda para eliminar:").pack(
        pady=(10, 0))

    # Obtener las criptomonedas activas con sufijos
    criptos_activos = obtener_criptos_activos()
    conteo_nombres = {}

    # Preparar nombres con sufijos
    nombres_con_sufijos = []
    for cripto in criptos_activos:
        nombre = cripto.lower()
        if nombre not in conteo_nombres:
            conteo_nombres[nombre] = 0
        conteo_nombres[nombre] += 1
        nombre_con_sufijo = f"{nombre}_{
            conteo_nombres[nombre]}" if conteo_nombres[nombre] > 1 else nombre
        nombres_con_sufijos.append(nombre_con_sufijo.capitalize())

    # Crear y configurar el Listbox
    listbox = tk.Listbox(top, selectmode=tk.SINGLE)
    for nombre_con_sufijo in nombres_con_sufijos:
        listbox.insert(tk.END, nombre_con_sufijo)
    listbox.pack(pady=(5, 10), padx=10, fill=tk.BOTH, expand=True)

    tk.Button(top, text="Eliminar", command=eliminar).pack(pady=(10, 10))
    top.geometry("300x300")  # Ajuste de tamaño para acomodar el Listbox

###

# Vaciar la base de datos


def vaciar_base_datos():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM compras')
    conexion.commit()
    conexion.close()


def vaciar_base_datos_gui(tree):
    if messagebox.askyesno("Confirmar", "¿Estás seguro de que deseas vaciar la base de datos?"):
        vaciar_base_datos()
        messagebox.showinfo("Éxito", "Base de datos vaciada exitosamente.")
        mostrar_comparacion(tree)


###

# Mostrar lista de criptomonedas

def mostrar_lista_criptos_gui(tree):
    def on_item_click(event):
        selected_item = tree_lista.selection()
        if selected_item:
            cripto = tree_lista.item(selected_item[0], 'values')[0]
            agregar_nueva_cripto_gui(tree, cripto)
            lista.destroy()

    lista = tk.Toplevel()
    lista.title("Lista de Criptomonedas")

    # Crear un marco (Frame) para contener el Treeview y la barra de desplazamiento
    frame = ttk.Frame(lista)
    frame.pack(expand=True, fill='both')

    tree_lista = ttk.Treeview(frame, columns=(
        "Criptomoneda", "Símbolo"), show='headings')
    tree_lista.heading("Criptomoneda", text="Criptomoneda")
    tree_lista.heading("Símbolo", text="Símbolo")

    tree_lista.column("Criptomoneda", width=200, anchor='center')
    tree_lista.column("Símbolo", width=100, anchor='center')

    # Crear una barra de desplazamiento vertical
    scrollbar = ttk.Scrollbar(frame, orient="vertical",
                              command=tree_lista.yview)

    # Configurar el Treeview para usar la barra de desplazamiento
    tree_lista.configure(yscrollcommand=scrollbar.set)

    # Posicionar el Treeview y la barra de desplazamiento en el Frame
    tree_lista.grid(row=0, column=0, sticky='nsew')
    # Barra de desplazamiento a la derecha
    scrollbar.grid(row=0, column=1, sticky='ns')

    # Configurar el redimensionamiento del Frame para que los elementos internos se ajusten
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    for cripto in sorted(criptos):
        simbolo = criptos[cripto]
        if simbolo == "BTCUSDT":
            simbolo_limpio = "BTC"  # Mantener BTC tal cual
        elif simbolo == "USDTUSDT":
            simbolo_limpio = "USDT"  # Mantener USDT tal cual
        else:
            simbolo_limpio = simbolo.replace("USDT", "").replace(
                "BTC", "")  # Limpiar para las demás criptos

        tree_lista.insert("", 'end', values=[
                          cripto.capitalize(), simbolo_limpio])

    tree_lista.bind("<ButtonRelease-1>", on_item_click)

    lista.geometry("400x300")

###


# Funciones para consultar y mostrar los precios
###

def obtener_precio_hace_X_horas(cripto, horas):
    try:
        # Obtener el timestamp actual y restarle X horas (X*60*60 segundos)
        timestamp_X_horas_atras = int(
            time.time() * 1000) - (horas * 60 * 60 * 1000)

        # Llamar a la función para obtener el precio histórico
        return obtener_precio_y_historico(
            cripto, timestamp_X_horas_atras)

    except Exception as e:
        print(f"Error al obtener el precio de hace {
              horas} horas para {cripto}: {e}")
        return None


def obtener_precio_hace_X_minutos(cripto, minutos):
    try:
        # Obtener el timestamp actual y restarle X minutos (X*60 segundos)
        timestamp_X_minutos_atras = int(
            time.time() * 1000) - (minutos * 60 * 1000)

        # Llamar a la función para obtener el precio histórico
        return obtener_precio_y_historico(
            cripto, timestamp_X_minutos_atras)

    except Exception as e:
        print(f"Error al obtener el precio de hace {
              minutos} minutos para {cripto}: {e}")
        return None


def consultar_precios_compra():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute('SELECT nombre, precio_compra, cantidad FROM compras')
    compras = cursor.fetchall()

    conexion.close()
    return compras

def obtener_precio_y_binance(symbol):
        result_queue = queue.Queue()

        # Obtener precio actual
        obtener_precio_binance_threading(symbol, result_queue)

        # Esperar los resultados
        precio_actual = result_queue.get()

        return precio_actual
    
def obtener_precio_y_historico(symbol, timestamp):
    result_queue = queue.Queue()

    # Obtener precio histórico
    obtener_precio_historico_threading(symbol, timestamp, result_queue)

    # Esperar los resultados
    precio_historico = result_queue.get()

    return precio_historico


def mostrar_comparacion(tree):

    bitcoin_precio = None

    compras = consultar_precios_compra()
    comparaciones = []

    conteo_nombres = {}

    for compra in compras:
        nombre = compra[0].lower()
        precio_compra = compra[1]
        cantidad_cripto = compra[2]

        nombre_base = nombre.split('_')[0].lower()

        precio_actual = None
        precio_anterior_6_hrs = None
        precio_anterior_3_hrs = None

        # Contar cuántas veces aparece el nombre en la lista de criptos activas
        if nombre_base in conteo_nombres:
            conteo_nombres[nombre_base] += 1
        else:
            conteo_nombres[nombre_base] = 1

        # Obtener el número de ocurrencias actual
        n = conteo_nombres[nombre_base]
        nombre_mostrado = f"{nombre_base.capitalize()}_{
            n}" if n > 1 else nombre.capitalize()

        # Comprobamos si la cripto está en el diccionario
        if nombre_base in criptos:
            symbol = criptos[nombre_base]

            # Caso especial para Binance Coin
            if symbol.endswith("BTC"):
                if bitcoin_precio is None:
                    # Obtenemos el precio de Bitcoin actual y hace unas horas
                    bitcoin_precio = obtener_precio_y_binance("BTCUSDT")
                    bitcoin_precio_6_hrs = obtener_precio_hace_X_horas(
                        "BTCUSDT", 6)
                    bitcoin_precio_3_hrs = obtener_precio_hace_X_horas(
                        "BTCUSDT", 3)
                precio_actual = obtener_precio_y_binance(symbol) * bitcoin_precio
                precio_anterior_6_hrs = obtener_precio_hace_X_horas(
                    symbol, 6) * bitcoin_precio_6_hrs
                precio_anterior_3_hrs = obtener_precio_hace_X_horas(
                    symbol, 3) * bitcoin_precio_3_hrs
            else:
                # Obtener el precio directamente del símbolo
                precio_actual = obtener_precio_y_binance(symbol)
                precio_anterior_6_hrs = obtener_precio_hace_X_horas(symbol, 6)
                precio_anterior_3_hrs = obtener_precio_hace_X_horas(symbol, 3)

        # Calcular la diferencia de precios
        if precio_actual is not None and precio_anterior_6_hrs is not None and precio_anterior_3_hrs is not None:
            diferencia = (precio_actual*cantidad_cripto) - \
                (precio_compra*cantidad_cripto)
            valor_activo = precio_actual * cantidad_cripto
            comparaciones.append([
                nombre_mostrado,
                f"{precio_compra:.6f}",
                f"{cantidad_cripto:.9f}",
                f"{valor_activo:.6f}",
                f"{precio_anterior_6_hrs:.6f}",
                f"{precio_anterior_3_hrs:.6f}",
                f"{precio_actual:.6f}",
                f"{diferencia:.6f}"])
        else:
            print(f"No se pudo obtener el precio de {nombre.capitalize()}")

    for row in tree.get_children():
        tree.delete(row)

    for fila in comparaciones:
        precio_6_hrs = float(fila[4])
        precio_1_hr = float(fila[5])
        precio_actual = float(fila[6])

        if precio_actual > precio_6_hrs and precio_actual > precio_1_hr:
            color = "green"
        elif precio_actual > precio_6_hrs and precio_actual < precio_1_hr:
            color = "yellow"
        else:
            color = "red"

        # Define una etiqueta única para cada fila basada en el nombre o algún identificador
        tag_name = f"color_{fila[0]}"

        # Inserta la fila en el Treeview con la etiqueta
        tree.insert("", 'end', values=fila, tags=(tag_name,))

        # Configura la etiqueta para aplicar el color
        tree.tag_configure(tag_name, foreground=color)

def obtener_id_de_grf(symbol):
    # Limpiar el símbolo
    if symbol == "BTCUSDT":
        simbolo_limpio = "BTC"  # Mantener BTC tal cual
    elif symbol == "USDTUSDT":
        simbolo_limpio = "USDT"  # Mantener USDT tal cual
    else:
        simbolo_limpio = symbol.replace("USDT", "").replace("BTC", "")  # Limpiar para las demás criptos

    # Buscar el ID en criptos_grf
    for cripto in criptos_grf:
        if cripto["symbol"] == simbolo_limpio.lower():
            return cripto["id"]

    return None  # Devuelve None si no se encuentra el ID

def obtener_sym_de_grf(symbol):
    # Limpiar el símbolo
    if symbol == "BTCUSDT":
        simbolo_limpio = "BTC"  # Mantener BTC tal cual
    elif symbol == "USDTUSDT":
        simbolo_limpio = "USDT"  # Mantener USDT tal cual
    else:
        simbolo_limpio = symbol.replace("USDT", "").replace("BTC", "")  # Limpiar para las demás criptos

    # Buscar el ID en criptos_grf
    for cripto in criptos_grf:
        if cripto["symbol"] == simbolo_limpio.lower():
            return cripto["symbol"]

    return None  # Devuelve None si no se encuentra el ID

# Función para mostrar gráfico al hacer clic en la fila
def on_tree_select(event, tree):
    selected_item = tree.selection()
    if selected_item:
        item = tree.item(selected_item)
        crypto_name = item['values'][0].lower()  # Suponiendo que el nombre de la cripto está en la primera columna
        crypto_key = criptos.get(crypto_name)  # Obtener el símbolo de la cripto

        if crypto_key:
            crypto_id = obtener_id_de_grf(crypto_key)  # Obtener el ID correspondiente
            crypto_sym = obtener_sym_de_grf(crypto_key)  # Obtener el símbolo correspondiente

            if crypto_id:
                try:
                    graficar_precio(crypto_id, crypto_sym)  # Graficar los precios
                except Exception as e:
                    messagebox.showerror("Error", str(e))
            else:
                messagebox.showerror("Error", f"No se pudo encontrar el ID para el símbolo {crypto_key}")
        else:
            messagebox.showerror("Error", f"No se pudo encontrar el símbolo para {crypto_name.capitalize()}")



# Función para ejecutar en un hilo y obtener los precios
def actualizar_precios_threaded(tree, root):
    threading.Thread(target=actualizar_tabla, args=(
        tree, root), daemon=True).start()


# Función para actualizar la tabla y evitar que bloquee la interfaz gráfica
def actualizar_tabla(tree, root):
    mostrar_comparacion(tree)
    root.after(10000, actualizar_precios_threaded, tree, root)


def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()

    if version.major == 10 and version.build >= 22000:
        # Set the title bar color to the background color on Windows 11 for better appearance
        pywinstyles.change_header_color(
            root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(
            root, "dark" if sv_ttk.get_theme() == "dark" else "normal")

        # A hacky way to update the title bar's color on Windows 10 (it doesn't update instantly like on Windows 11)
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)


def iniciar_interfaz():

    root = tk.Tk()
    root.title("Seguimiento Crypto")

    # Estilo de la interfaz

    style = ttk.Style(root)
    sv_ttk.set_theme("dark")
    apply_theme_to_titlebar(root)
    style.configure('Treeview', font=('Arial', 12), rowheight=25)
    style.configure('Treeview.Heading', font=('Arial', 14, 'bold'))
    style.configure('TButton', font=('Arial', 12, 'bold'))

    ###

    main_frame = ttk.Frame(root)
    main_frame.pack(expand=True, fill='both')

    # Canvas para permitir desplazamiento horizontal y vertical
    canvas = tk.Canvas(main_frame)
    canvas.pack(side='left', fill='both', expand=True)

    # Barra de desplazamiento horizontal
    scrollbar_horizontal = ttk.Scrollbar(
        root, orient="horizontal", command=canvas.xview)
    scrollbar_horizontal.pack(side="bottom", fill="x")

    # Configurar Canvas para usar las barras de desplazamiento
    canvas.configure(xscrollcommand=scrollbar_horizontal.set)

    # Frame interior del Canvas que contendrá el contenido desplazable
    content_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=content_frame, anchor="nw")

    # Configurar eventos para ajustar el scroll
    def on_configure(event):
        canvas.config(scrollregion=canvas.bbox("all"))

    content_frame.bind("<Configure>", on_configure)

    # Frame para contener el Treeview (lista de criptos) con scroll vertical
    table_frame = ttk.Frame(content_frame)
    table_frame.pack(fill='both', expand=True)

    # Barra de desplazamiento vertical exclusiva para el Treeview
    scrollbar_vertical = ttk.Scrollbar(table_frame, orient="vertical")
    scrollbar_vertical.pack(side="right", fill="y")

    columns = ("Crypto", "Precio Compra", "Cantidad", "Valor Activo",
               "Precio 6hrs", "Precio 3hrs", "Precio Actual", "Ganancias/Perdidas")
    tree = ttk.Treeview(table_frame, columns=columns, show='headings')
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor='center')
    tree.pack(expand=True, fill='both')

    # Conectar el scroll vertical con el Treeview
    scrollbar_vertical.config(command=tree.yview)

    button_frame = ttk.Frame(content_frame)
    button_frame.pack(pady=10)

    # Agregar el evento para seleccionar una fila
    tree.bind("<ButtonRelease-1>", lambda event: on_tree_select(event, tree))

    # Distribuir botones en la interfaz usando grid
    btn_lista = tk.Button(button_frame, text="Lista de Criptos",
                          command=lambda: mostrar_lista_criptos_gui(tree), width=20)
    btn_lista.grid(row=0, column=0, padx=5, pady=5)

    btn_agregar = tk.Button(button_frame, text="Añadir Criptomoneda",
                            command=lambda: agregar_nueva_cripto_gui(tree), width=20)
    btn_agregar.grid(row=0, column=1, padx=5, pady=5)

    btn_eliminar = tk.Button(button_frame, text="Eliminar Criptomoneda",
                             command=lambda: eliminar_cripto_gui(tree), width=20)
    btn_eliminar.grid(row=1, column=0, padx=5, pady=5)

    btn_vaciar = tk.Button(button_frame, text="Vaciar Base de Datos",
                           command=lambda: vaciar_base_datos_gui(tree), width=20)
    btn_vaciar.grid(row=1, column=1, padx=5, pady=5)

    btn_mostrar = tk.Button(button_frame, text="Actualizar",
                            command=lambda: actualizar_precios_threaded(tree, root), width=20)
    btn_mostrar.grid(row=2, column=0, columnspan=2,
                     padx=5, pady=5, sticky='ew')

    threading.Thread(target=crear_tabla, daemon=True).start()
    actualizar_precios_threaded(tree, root)

    root.geometry("1500x500")
    root.mainloop()


if __name__ == "__main__":
    iniciar_interfaz()
