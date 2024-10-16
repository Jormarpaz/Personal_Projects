import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import requests
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cripto_visualizer 

class TestCryptoProject(unittest.TestCase):

    # 1. Prueba de conexión a la base de datos
    def test_conexion_db(self):
        conexion = cripto_visualizer.conectar_db()
        self.assertIsInstance(conexion, sqlite3.Connection, "La conexión no es una instancia de sqlite3.Connection")
        conexion.close()

    # 2. Prueba de la función obtener_precio_binance con una respuesta simulada
    @patch('requests.get')  # Simula las llamadas a requests.get
    def test_obtener_precio_binance(self, mock_get):
        # Simular la respuesta de la API
        mock_response = MagicMock()
        mock_response.json.return_value = {'price': '45000.00'}
        mock_get.return_value = mock_response

        # Ejecutar la función y comprobar el resultado
        precio = cripto_visualizer.obtener_precio_y_binance('BTCUSDT')
        self.assertEqual(precio, 45000.00, "El precio de Bitcoin debería ser 45000.00")

    # 3. Prueba de la función eliminar_cripto con una base de datos simulada
    @patch('sqlite3.connect')  # Simula la conexión a la base de datos
    def test_eliminar_cripto(self, mock_connect):
        # Crear una simulación de la conexión y el cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Simular que la criptomoneda existe en la base de datos
        mock_cursor.fetchone.return_value = [1]

        # Llamar a la función eliminar_cripto
        cripto_visualizer.eliminar_cripto('bitcoin')

        # Asegurarse de que se ejecuta el DELETE
        mock_cursor.execute.assert_called_with('DELETE FROM compras WHERE nombre = ?', ('bitcoin',))
        mock_conn.commit.assert_called_once()  # Verificar que se hizo commit
        mock_conn.close.assert_called_once()  # Verificar que se cerró la conexión
    
    # 4. Prueba de la función agregar_nueva_cripto con una base de datos simulada
    @patch('sqlite3.connect')  # Simula la conexión a la base de datos
    def test_agregar_nueva_cripto(self, mock_connect):
        # Crear una simulación de la conexión y el cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Llamar a la función agregar_nueva_cripto
        cripto_visualizer.agregar_nueva_cripto('bitcoin', 45000.00, 1.0)

        # Asegurarse de que se ejecuta el INSERT
        mock_cursor.execute.assert_called_with(
            'INSERT INTO compras (nombre, precio_compra, cantidad, fecha) VALUES (?, ?, ?, ?)',
            ('bitcoin', 45000.00, 1.0, unittest.mock.ANY)
        )
        mock_conn.commit.assert_called_once()  # Verificar que se hizo commit
        mock_conn.close.assert_called_once()  # Verificar que se cerró la conexión


if __name__ == '__main__':
    unittest.main()