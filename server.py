#!/usr/bin/env python
# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Revisión 2014 Carlos Bederián
# Revisión 2011 Nicolás Wolovick
# Copyright 2008-2010 Natalia Bidart y Daniel Moisset
# $Id: server.py 656 2013-03-18 23:49:11Z bc $

import connection
import optparse
import os
import socket
import sys
from constants import *
import threading

class Server(object):
    """
    El servidor, que crea y atiende el socket en la dirección y puerto
    especificados donde se reciben nuevas conexiones de clientes.
    """

    def __init__(self, addr=DEFAULT_ADDR, port=DEFAULT_PORT,
                 directory=DEFAULT_DIR):
        print("Serving %s on %s:%s." % (directory, addr, port))
        # Chequear que el directorio existe
        if not os.path.isdir(directory):
            os.mkdir(directory)
        
        # Crear un nuevo socket TCP/IP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Vincular el socket a la dirección y puerto especificados
        self.sock.bind((addr, port))
        # Guardar el directorio que se va a servir
        self.directory = directory

    def serve(self):
        """
        Loop principal del servidor. Se acepta una conexión a la vez
        y se espera a que concluya antes de seguir.
        """
        # Pone el socket en modo de escucha. Esto permite que el servidor acepte conexiones entrantes.
        self.sock.listen()
        while True:
            # Aceptar una nueva conexión
            (clientsocket, address) = self.sock.accept()
            # Crear una nueva instancia de Connection para manejar la comunicación con un cliente en especifico 
            conn = connection.Connection(clientsocket, self.directory)
            # Imprimir información sobre la conexión aceptada
            print(f"Conectado por: {address}")
            # Manejar la comunicación con el cliente en diferentes hilos
            #conn.handle()
            t = threading.Thread(target=conn.handle)
            t.start()

            #INVESTIGAR SOBRE  "límite de puertos efímeros" o el "número máximo de sockets de red" para ver el maximo de clientes que puede manejar el servidor         


def main():
    """Parsea los argumentos y lanza el server"""

    parser = optparse.OptionParser()
    parser.add_option(
        "-p", "--port",
        help="Número de puerto TCP donde escuchar", default=DEFAULT_PORT)
    parser.add_option(
        "-a", "--address",
        help="Dirección donde escuchar", default=DEFAULT_ADDR)
    parser.add_option(
        "-d", "--datadir",
        help="Directorio compartido", default=DEFAULT_DIR)

    options, args = parser.parse_args()
    if len(args) > 0:
        parser.print_help()
        sys.exit(1)
    try:
        port = int(options.port)
    except ValueError:
        sys.stderr.write(
            "Numero de puerto invalido: %s\n" % repr(options.port))
        parser.print_help()
        sys.exit(1)

    server = Server(options.address, port, options.datadir)
    server.serve()


if __name__ == '__main__':
    main()
