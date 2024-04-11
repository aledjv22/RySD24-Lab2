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
        #Aviso
        print("Cerrando conexion...")
        # Asignar False a self.connected
        self.connected = False
        # Cerrar el socket
        try: 
            self.socket.close()
        except socket.error:
            print(f"Error al cerrar la conexion. {socket.error}")
     
    def send(self, message: Union[bytes, str], codif="ascii"):
        """
        Este método se encarga de enviar un mensaje al cliente a través del socket.
        El mensaje puede ser de tipo bytes o str, y se puede codificar como 'ascii' o 'b64encode'.

        Parámetros:
        message: El mensaje a enviar. Puede ser de tipo bytes o str.
        codif: La codificación a utilizar para el mensaje. Por defecto es 'ascii'.
        """
        try:
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
        except BrokenPipeError:
            logging.error("Error al enviar el mensaje: BrokenPipeError")
            self.connected = False
        except ConnectionResetError:
            logging.error("Error al enviar el mensaje: ConnectionResetError")
            self.connected = False

    def quit(self):
        """
        Cierra la conexión con el cliente y envía un mensaje de despedida.
        """
        # Enviamos un mensaje de despedida al cliente.
        self.send(f"{CODE_OK} {error_messages[CODE_OK]}")
        
        self.close()
     
    def which_command(self, data_line):
        """
        Este método se encarga de determinar qué comando se ha recibido y llamar a la función correspondiente.

        Parámetros:
        data_line: El comando recibido.
        """
        try:
            command, *args = data_line.split(" ")
            # quit: Cierra la conexión con el cliente.
            if command.lower() == "quit": # .lower() para que no importe si el comando está en mayúsculas o minúsculas
                if len(args) == 0:
                    self.quit()
                else:
                    self.send(f"{INVALID_ARGUMENTS} {error_messages[INVALID_ARGUMENTS]}")
            
            # get_file_listing: Devuelve un listado de los archivos en el directorio que se está sirviendo.
            elif command.lower() == "get_file_listing":
                if len(args) == 0:
                    self.get_file_listing()
                else:
                    self.send(f"{INVALID_ARGUMENTS} {error_messages[INVALID_ARGUMENTS]}")
            
            # get_metadata: Devuelve el tamaño de un archivo (filename) en bytes.
            elif command.lower() == "get_metadata":
                if len(args) == 1:
                    self.get_metadata(args[0])
                else:
                    self.send(f"{INVALID_ARGUMENTS} {error_messages[INVALID_ARGUMENTS]}")
            
            # get_slice: Devuelve un slice o parte de un arhivo (filename) codificado en base64.
            elif command.lower() == "get_slice":
                try:
                    if len(args) == 3:
                            self.get_slice(args[0], int(args[1]), int(args[2]))
                    else:
                        self.send(f"{INVALID_ARGUMENTS} {error_messages[INVALID_ARGUMENTS]}")
                except ValueError:
                    self.send(f"{INVALID_ARGUMENTS} {error_messages[INVALID_ARGUMENTS]}")

            # corrobora que no le hayan mandado verdura en lugar de un comando
            else:
                self.send(f"{INVALID_COMMAND} {error_messages[INVALID_COMMAND]}")
 
        except Exception:
            print(f"Error en el manejo de la conexión: {Exception}")
            self.send(f"{INTERNAL_ERROR} {error_messages[INTERNAL_ERROR]}")

    def _recv(self, timeout=None):
        """
        Recibe datos y acumula en el buffer interno.

        Para uso privado del servidor.
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
        Espera datos hasta obtener una línea completa delimitada por el
        terminador del protocolo.

        Devuelve la línea, eliminando el terminador y los espacios en blanco
        al principio y al final.
        """
        # Mientras no haya un EOL en el buffer y la conexión esté activa.
        while not EOL in self.buffer and self.connected:
            self._recv() # Recibe datos y acumula en el buffer interno.
        
        # Si hay un EOL en el buffer, separamos la respuesta y el buffer
        if EOL in self.buffer:
            response, self.buffer = self.buffer.split(EOL, 1) 
            return response.strip()
        else:
            # Si no hay EOL, la conexión se cierra.
            self.connected = False 
            return ""

    def get_file_listing(self):
        """
        Devuelve un listado de los archivos en el directorio que se está sirviendo.
        """
        # Inicializamos la lista de archivos.
        print("Request: get_file_listing")
        response = ""
        # Iteramos sobre los archivos en el directorio.
        for file in os.listdir(self.directory):
            response += file + EOL
        self.send(f"{CODE_OK} {error_messages[CODE_OK]}")
        self.send(response)

    def get_metadata(self, filename: str):
        """
        Devuelve el tamaño de un archivo (filename) en bytes 
        """
        print("Request: get_metadata")
        file_path = os.path.join(self.directory, filename)
        if (not os.path.isfile(file_path)):
            self.send(f"{FILE_NOT_FOUND} {error_messages[FILE_NOT_FOUND]}")
        else:
            file_size = os.path.getsize(file_path)
            self.send(f"{CODE_OK} {error_messages[CODE_OK]}")
            self.send(str(file_size))
        #De nuevo, podriamos agregar guardas. Sobre todo para archivos vacios, mal escritos, etc (en general invalidos)  

    def get_slice(self, filename:str, offset: int, size: int):
        """
        Devuelve un slice o parte de un arhivo (filename) codificado en base64 
        Esta determinado desde offset y de tamaño size (ambos en bytes)
        """
        print("Request: get_slice")
        file_path = os.path.join(self.directory, filename)
        file_size = os.path.getsize(file_path)
        if (offset < 0 and size < 0) or offset + size > file_size: 
            self.send(f"{BAD_OFFSET}, {error_messages[BAD_OFFSET]}")
            # no estoy segura si es un fatal_status como para detener la conexion 
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
        Atiende eventos de la conexión hasta que termina.
        """
        data_line = ""
        # Mientras la conexión esté activa, esperamos comandos del cliente.
        while self.connected:
            if "\n" in data_line:
                self.send(f"{BAD_EOL} {error_messages[BAD_EOL]}")
            elif len(data_line) > 0:
                self.which_command(data_line)
            data_line = self.read_line()
            