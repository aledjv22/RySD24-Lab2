# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import os
import socket
from constants import *
from base64 import b64encode

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

    def send(self, message: bytes | str, codif="ascii"):
        if codif == "b64encode":
            message = b64encode(message)
        elif codif == "ascii":
            message = message + EOL
            message = message.encode("ascii")
        else:
            raise ValueError(f"Codificación no válida: {codif}")
        
        while len(message) > 0:
            sent = self.socket.send(message)
            assert sent > 0
            message = message[sent:]

    def handle(self):
        """
        Atiende eventos de la conexión hasta que termina.
        """
        pass
