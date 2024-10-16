# Crypto Visualizer

>python program to track crypto prices

[![License](https://img.shields.io/badge/license-MIT-lightgreen?logo=balance-scale)](https://opensource.org/licenses/MIT)

Aplicación de escritorio hecha en Python que permite rastrear, visualizar y gestionar precios de criptomonedas utilizando APIs y una base de datos SQLite.

Desktop application developed in Python that allows you to track, visualize, and manage cryptocurrency prices using APIs and an SQLite database.

## Installation

```bash
git clone https://github.com/Jormarpaz/Personal_Projects.git
cd Crypto_Visualizer
pip install -r requirements.txt
```

## Usage example

### Using Command-Line

```bash
python cripto_visualizer.py
```

(or)

```bash
python3 cripto_visualizer.py
```

### Using .exe

```bash
cd dist
./cripto_visualizer.exe
```

## Disclaimer

Por el momento sólo he podido comprobar su funcionamiento en la 3.12.X, de ahí para abajo es terreno desconocido.

At the moment, I have only been able to verify its functionality on 3.12.X, anything below that is uncharted territory.

## Contenido

### Archivos

Por un lado, los diccionarios de donde la app obtiene las referencias para las criptos:

```bash
cripto_dic_grf.py

cripto_dic.py
```

Por otro, el código principal:

```bash
cripto_visualizer.py
```

Código de testeo:

```bash
## Para usarlo, acceder al directorio del test y emplear `pytest` en la consola ##

cd tests
test_project.py
```

### Algunas funciones

```bash
## Función para obtener el precio de una cripto en directo ##

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
```

```bash
## Función para obtener el precio de una cripto hace X horas ##

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
```

```bash
## Función para obtener el gráfico del valor de la cripto en un cierto tiempo ##

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
```

```bash
## Función para obtener la lista de criptos que se están siguiendo ##

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
```

#### As I'm still learning about GitHub, feel free to contact me or fork and pull a request if needed. Thanks for your attention

