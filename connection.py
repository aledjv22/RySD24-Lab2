# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import os
import socket
from base64 import b64encode
from constants import *
from typing import Union

class Connection(object):
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta
    que termina la conexión.
    """

    def __init__(self, socket: socket.socket, directory):
        # Asignar la ruta del directorio que se está sirviendo a self.directory
        self.directory = directory
        # Asignar el socket del cliente a self.socket
        self.socket = socket
        # Asignar True a self.connected
        self.connected = True
        # Asignar "" a self.buffer
        self.buffer = ""

    def close(self):
        """
        Cierra la conexión con el cliente.
        """
        # Asignar False a self.connected
        self.connected = False
        # Cerrar el socket
        self.socket.close()

    def send(self, message: Union[bytes, str], codif="ascii"):
        """
        Este método se encarga de enviar un mensaje al cliente a través del socket.
        El mensaje puede ser de tipo bytes o str, y se puede codificar como 'ascii' o 'b64encode'.

        Parámetros:
        message: El mensaje a enviar. Puede ser de tipo bytes o str.
        codif: La codificación a utilizar para el mensaje. Por defecto es 'ascii'.
        """
        # Si la codificación es 'b64encode', codificamos el mensaje con base64.
        if codif == "b64encode":
            message = b64encode(message)
        # Si la codificación es 'ascii', añadimos un fin de línea al mensaje y lo codificamos en 'ascii'.
        elif codif == "ascii":
            message = message + EOL
            message = message.encode("ascii")
        # Si la codificación no es ninguna de las anteriores, lanzamos un error.
        else:
            raise ValueError(f"Codificación no válida: {codif}")
        # Mientras el mensaje tenga contenido, seguimos enviándolo.
        while len(message) > 0:
            # Enviamos el mensaje a través del socket y guardamos la cantidad de bytes enviados.
            sent = self.socket.send(message)
            # Aseguramos que se haya enviado al menos un byte.
            assert sent > 0
            # Actualizamos el mensaje quitando los bytes que ya se han enviado.
            message = message[sent:]

    def quit(self):
        """
        Cierra la conexión con el cliente y envía un mensaje de despedida.
        """
        # Enviamos un mensaje de despedida al cliente.
        self.send("0 OK")
        # Cerramos la conexión con el cliente.
        self.close()

    def get_file_listing(self):
        """
        Devuelve un listado de los archivos en el directorio que se está sirviendo.
        """
        # Inicializamos la lista de archivos.
        files = ""
        # Iteramos sobre los archivos en el directorio.
        for file in os.listdir(self.directory):
            files += file + EOL
        self.send(str(files))
        self.send("Test de respuesta")

    def handle(self):
        """
        Atiende eventos de la conexión hasta que termina.
        """
        while self.connected:
            # Recibir datos del cliente
            data = self.socket.recv(1024).decode("ascii").strip()
            # Si el comando es 'quit', llamar a la función quit()
            if data.lower() == "quit":
                self.quit()
            # Si el comando es 'get_file_listing', llamar a la función get_file_listing()
            elif data.lower() == "get_file_listing":
                self.get_file_listing()
