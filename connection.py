# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import os
import socket
from base64 import b64encode
from constants import *
from typing import Union
import logging 

class Connection(object):
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta
    que termina la conexión.
    """

    # Constructor de la clase Connection. Inicializa el socket, el directorio, 
    # establece la conexión como activa y crea un buffer vacío.
    def __init__(self, socket: socket.socket, directory):
        self.directory = directory
        self.socket = socket
        self.connected = True
        self.buffer = ""


    def close(self):
        """
        Cierra la conexión y maneja posibles errores de cierre de socket.
        """
        print("Cerrando conexion...")
        self.connected = False
        try: 
            self.socket.close()
        except socket.error:
            print(f"Error al cerrar la conexion. {socket.error}")


    def send(self, message: Union[bytes, str], codif="ascii"):
        """
        Envía un mensaje al cliente y maneja posibles errores de conexión.

        Parámetros:
          - self: La instancia de la clase Connection.
          - message: El mensaje a enviar.
          - codif: La codificación a utilizar. Por defecto, "ascii".
        """
        try:
            if codif == "b64encode":
                message = b64encode(message)
            
            elif codif == "ascii":
                message = message + EOL
                message = message.encode("ascii")
            
            else:
                raise ValueError(f"Codificación no válida: {codif}")
            
            # Enviamos el mensaje al cliente mientras haya algo para enviar.
            while len(message) > 0:
                sent = self.socket.send(message)
                assert sent > 0
                message = message[sent:]
        
        except BrokenPipeError:
            logging.error("Error al enviar el mensaje: BrokenPipeError")
            self.connected = False

        except ConnectionResetError:
            logging.error("Error al enviar el mensaje: ConnectionResetError")
            self.connected = False


    def quit(self):
        """
        Cierra la conexión con el cliente y envía un mensaje de confirmación.
        """
        self.send(f"{CODE_OK} {error_messages[CODE_OK]}")
        self.close()


    def which_command(self, data_line):
        """
        Procesa los comandos recibidos del cliente y ejecuta la acción correspondiente.

        Parámetros:
          - self: La instancia de la clase Connection.
          - data_line: La línea de datos recibida del cliente.
        """
        try:
            command, *args = data_line.split(" ")
            if command.lower() == "quit": 
                if len(args) == 0:
                    self.quit()
                else:
                    self.send(f"{INVALID_ARGUMENTS} {error_messages[INVALID_ARGUMENTS]}")
            
            elif command.lower() == "get_file_listing":
                if len(args) == 0:
                    self.get_file_listing()
                else:
                    self.send(f"{INVALID_ARGUMENTS} {error_messages[INVALID_ARGUMENTS]}")
            
            elif command.lower() == "get_metadata":
                if len(args) == 1:
                    self.get_metadata(args[0])
                else:
                    self.send(f"{INVALID_ARGUMENTS} {error_messages[INVALID_ARGUMENTS]}")
            
            elif command.lower() == "get_slice":
                try:
                    if len(args) == 3:
                            self.get_slice(args[0], int(args[1]), int(args[2]))
                    else:
                        self.send(f"{INVALID_ARGUMENTS} {error_messages[INVALID_ARGUMENTS]}")
                except ValueError:
                    self.send(f"{INVALID_ARGUMENTS} {error_messages[INVALID_ARGUMENTS]}")
            
            else:
                self.send(f"{INVALID_COMMAND} {error_messages[INVALID_COMMAND]}")
 
        except Exception:
            print(f"Error en el manejo de la conexión: {Exception}")
            self.send(f"{INTERNAL_ERROR} {error_messages[INTERNAL_ERROR]}")


    def _recv(self, timeout=None):
        """
        Recibe datos del cliente y los acumula en el buffer interno.

        Parámetros:
          - self: La instancia de la clase Connection.
          - timeout: El tiempo máximo de espera para recibir datos.
        """
        try:
            data = self.socket.recv(4096).decode("ascii")
            self.buffer += data 

            if len(data) == 0:
                logging.info("El server interrumpió la conexión.")
                self.connected = False
            
            if len(self.buffer) >= 2**32:
                logging.warning("El buffer ha alcanzado su capacidad máxima.")
                self.connected = False
        
        except ConnectionResetError:
            logging.warning("No se consiguió conectar con el cliente.")
            self.connected = False

        except BrokenPipeError:
            logging.warning("Error de conexión con el cliente.")
            self.connected = False


    def read_line(self, timeout=None):
        """
        Espera a recibir una línea completa del cliente. Devuelve la línea, 
        eliminando el terminador y los espacios en blanco al principio y al final.

        Parámetros:
          - self: La instancia de la clase Connection.
          - timeout: El tiempo máximo de espera para recibir datos.
        """
        # Mientras no haya un EOL en el buffer y la conexión esté activa.
        while not EOL in self.buffer and self.connected:
            self._recv()
        
        if EOL in self.buffer:
            response, self.buffer = self.buffer.split(EOL, 1) 
            return response.strip()

        else:
            self.connected = False 
            return ""


    def get_file_listing(self):
        """
        Devuelve una lista de los archivos en el directorio que se está sirviendo.

        Parámetros:
          - self: La instancia de la clase Connection.
        """
        print("Request: get_file_listing")
        response = ""

        for file in os.listdir(self.directory):
            response += file + EOL
        self.send(f"{CODE_OK} {error_messages[CODE_OK]}")
        self.send(response)


    def get_metadata(self, filename: str):
        """
        Devuelve el tamaño de un archivo (filename) en bytes.
        
        Parámetros:
          - self: La instancia de la clase Connection.
          - filename: El nombre del archivo del que se quiere obtener la metadata.
        """
        print("Request: get_metadata")
        file_path = os.path.join(self.directory, filename)
        if (not os.path.isfile(file_path)):
            self.send(f"{FILE_NOT_FOUND} {error_messages[FILE_NOT_FOUND]}")
        else:
            file_size = os.path.getsize(file_path)
            self.send(f"{CODE_OK} {error_messages[CODE_OK]}")
            self.send(str(file_size))


    def get_slice(self, filename:str, offset: int, size: int):
        """
        Devuelve un slice del archivo especificado por filename, comenzando en el offset
        y con un tamaño size.

        Parámetros:
          - self: La instancia de la clase Connection.
          - filename: El nombre del archivo del que se quiere obtener el slice.
          - offset: La posición inicial del slice.
          - size: El tamaño del slice.
        """
        print("Request: get_slice")
        file_path = os.path.join(self.directory, filename)
        file_size = os.path.getsize(file_path)
        if (offset < 0 and size < 0) or offset + size > file_size: 
            self.send(f"{BAD_OFFSET}, {error_messages[BAD_OFFSET]}")

        else:
            self.send(f"{CODE_OK} {error_messages[CODE_OK]}")
            with open(file_path, "rb") as fn:
                fn.seek(offset)

                while size > 0:
                    slice = fn.read(size)
                    size = size - len(slice)
                    self.send(slice, codif="b64encode")
                self.send('')


    def handle(self):
        """
        Maneja la conexión con el cliente, esperando comandos y respondiendo a los mismos.

        Parámetros:
          - self: La instancia de la clase Connection.
        """
        data_line = ""
    
        while self.connected:
            if "\n" in data_line:
                self.send(f"{BAD_EOL} {error_messages[BAD_EOL]}")

            elif len(data_line) > 0:
                self.which_command(data_line)
            data_line = self.read_line()
            