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
        """
        Inicializa el servidor con la dirección, puerto y directorio
        especificados.

        Parámetros:
          - addr: dirección donde escuchar por conexiones entrantes.
          - port: puerto donde escuchar por conexiones entrantes.
          - directory: directorio donde guardar los archivos recibidos.   
        """
        print("Serving %s on %s:%s." % (directory, addr, port))
        if not os.path.isdir(directory):
            os.mkdir(directory)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((addr, port))
        self.directory = directory

    def serve(self):
        """
        Pone a escuchar al servidor por conexiones entrantes y lanza un hilo
        para atender a cada una de ellas.
        """
        self.sock.listen()
        while True:
            (clientsocket, address) = self.sock.accept()
            conn = connection.Connection(clientsocket, self.directory)
            print(f"Conectado por: {address}")
            # Se crea un hilo para atender la conexión
            t = threading.Thread(target=conn.handle)
            t.start() # Se inicia el hilo  


def main():
    """
    Función principal que parsea los argumentos de línea de comandos y
    lanza el servidor.
    """
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
