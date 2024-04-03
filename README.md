# Laboratorio 2: Aplicación Servidor
<p style="color:gray; font-size: 16px;">
  Cátedra de Redes y Sistemas Distribuidos
</p>

## Objetivos
- Aplicar la comunicación cliente/servidor por medio de la programación de sockets, desde la perspectiva del servidor.
- Familiarizarse con un protocolo de aplicación diseñado en casa.
- Comprender, diseñar e implementar un programa servidor de archivos en Python.

## Protocolo HFTP
Llamaremos *Home-made File Transfer Protocol* (HFTP) a un protocolo de transferencia de archivos caseros, creado por nosotros específicamente para este laboratorio.

HFTP es un protocolo de capa de aplicación que usa TCP como protocolo de transporte. TCP garantiza una entrega segura, libre de errores y en orden de todas las transacciones hechas con HFTP. Un servidor de HFTP escucha perdidos en el puerto TCP 19500.

### Comandos y Respuestas
El cliente HFTP inicia el intercambio de mensajes mediante pedidos o **comandos** al servidor. 
El servidor envía una **respuesta** a cada uno antes de procesar el siguiente hasta que el cliente envía un comando de fin de conexión. En caso de que el cliente envíe varios pedidos consecutivos, el servidor HTFP los responde en el orden en que se enviaron. El protocolo HTFP es un protocolo ASCII, no binario, por lo que lo enviado (incluso archivos binarios) será legible por humanos como stings.
- **Comandos:** consisten en una cadena de caracteres compuesta por elementos separados por un único espacio y terminadas con un fin de línea estilo DOS (\r\n)¹. El primer elemento del comando define el tipo de acción esperada por el comando y los elementos que siguen son argumentos necesarios para realizar la acción.
- **Respuestas:** comienzan con una cadena terminada en `\r\n`, y pueden tener una continuación dependiendo el comando que las origina. La cadena inicial comienza con una secuencia de dígitos (código de respuesta), seguida de un espacio, seguido de un texto describiendo el resultado de la operación. Por ejemplo, una cadena indicando un resultado exitoso tiene código 0 y con su texto descriptivo podría ser **`0 OK`**.

> ¹Ver End of Line (EOL) en  https://en.wikipedia.org/wiki/Newline:

> \r = CR (Carriage Return) Usado como un carácter de una línea en Mac OS.

> \n = LF (Line Feed) Usando como un carácter de nueva línea en Unix/Mac OS X.

> \r\n = CR + LF Usando como un carácter de nueva línea en Windows/DOS y varios protocolos.

<table>
  <tr>
    <th>Comandos</th>
    <th>Descripción y Respuesta</th>
  </tr>
  <tr>
    <td>get_file_listing</td>
    <td>
      <p>Este comando no recibe argumentos y busca obtener la lista de <br/>
      archivos que están actualmente disponibles. El servidor responde <br/>
      con una secuencia de líneas terminadas en \r\n, cada una con el <br/> 
      nombre de uno de los archivos disponible. Una línea sin texto <br/>
      indica el fin de la lista.</p>
      <p>Respuesta: </p>
      <ul>
        <li>0 OK\r\n</li>
        <li>archivo1.txt\r\n</li>
        <li>archivo2.jpg\r\n</li>
        <li>\r\n</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td>get_metadata<br/>FILENAME</td>
    <td>
      <p>Este comando recibe un comando FILENAME especificando un</p>
      <p>nombre de archivo del cual se pretende averiguar el tamaño². El</p>
      <p>servidor responde con una cadena indicando su valor en bytes.</p>
      <p>Comando: get_metadata archivo1.txt</p>
      <p>Respuesta: </p>
      <ul>
        <li>0 OK\r\n</li>
        <li>3199\r\n</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td>get_slice FILENAME<br/>OFFSET SIZE</td>
    <td>
      <p>Este comando recibe en el argumento FILENAME el nombre de<br/>
      un archivo del que se pretende obtener un slice o parte. La parte se<br/>
      especifica con un OFFSET (byte al inicio) y un SIZE (tamaño de la <br/>
      parte esperada, en bytes), ambos negativos³. El servidor<br/>
      responde con el fragmento de un archivo pedido codificado en<br>
      <a href='https://es.wikipedia.org/wiki/Base64'>base64</a> y un \r\n.</p>
      <img src="https://i.ibb.co/93g6ZTX/Captura-desde-2024-04-02-11-00-31.png"
      alt="tabla"/>
    </td>
  </tr>
  <tr>
    <td>quit</td>
    <td>
      <p>
        Este comando no recibe argumentos y busca terminar la <br/>
        conexión. El servidor responde con un resultado exitoso <br/>
        (0 OK) y luego cierra la conexión.
      </p>
    </td>
  </tr>
  <tr>
  </tr>
</table>

> ²Los nombres de archivos no deberán contener espacios, de lo contrario, el protocolo no puede diferenciar si un espacio corresponde al nombre del archivo o al comienzo de un argumento.

> ³Atención que de acuerdo a la codificación [ASCII](https://es.wikipedia.org/wiki/ASCII), algunos caracteres fuera del lenguaje inglés se representan con dos Bytes. En el archivo del ejemplo, de haber usado ¡ en lugar de ! al comienzo de la frase, la respuesta hubiese sido "calor que hace hoy," (con espacio al principio en luhar de al final) ya que el caracter ¡ ocupa dos bytes.

> ⁴Esta es la codificación base64 de “calor que hace hoy, ”. El sentido de utilizar base64 es que al enviar el archivo posiblemente binario, se codifica en una cadena ASCII.

### Manejo de Errores
En caso de algún error, el servidor responderá con códigos de respuestas diferentes a 0, más algún texto descriptivo a definir por el implementador. En particular:
- 0	La operación se realizó con éxito.
- 100	Se encontró un carácter \n fuera de un terminador de pedido \r\n.
- 101	Alguna malformación del pedido impidió procesarlo⁵.
- 199	El servidor tuvo algún fallo interno al intentar procesar el pedido.
- 200	El comando no está en la lista de comandos aceptados.
- 201	La cantidad de argumentos no corresponde o no tienen la forma correcta.
- 202	El pedido se refiere a un archivo inexistente.
- 203	El pedido se refiere a una posición inexistente en un archivo⁶.

Los errores con código iniciado en 1 son considerados fatales y derivan en el cierre de la conexión una vez reportados por el servidor. Los errores que inician con 2 permiten continuar con la conexión y recibir pedidos posteriores.

> ⁵A difrerencia de los errores no fatales 200 y 201, este error es producto de alguna malformación crítica a criterio del implementador. Por ejemplo, un comando malintencionado, de gran longitud, podría provocar un [DoS](https://es.wikipedia.org/wiki/Ataque_de_denegaci%C3%B3n_de_servicio) o disminución de performance en el server y podría ser intervenido por un error fatal de este tipo.

> ⁶Se aplica particularmente al comando `get_slice` y debe generarse cuando no se cumple la condicion `OFFSET + SIZE <= filesize`.

## Tarea
Deberán diseñar e implementar un servidor de archivos en Python 3 que soporte **completamente** un protocolo de transferencia de archivos HFTP. El servidor debe ser robusto y tolerar comandos intencional o maliciosamente incorrectos.

1. Descargar el kickstarter del laboratorio desde el aula virtual. Descomprimir con: `tar -xvzf kickstart_lab2.tar.gz`. El kickstarter provee una estructura para el servidor que se deberá completar (`server.py y connection.py`), un archivo con las constantes a utilizar (`constants.py`), el cliente HFTP funcionando y un archivo de testeo [server-tets.py](./server-test.py) para correr junto con el servidor. 
2. Armar un entorno virtual de python con python 3.6 según [esta nota](https://stackoverflow.com/questions/70422866/how-to-create-a-venv-with-a-different-python-version).
3. Ejecutar el laboratorio como está.
4. Modificar el archivo server para que acepte conexiones y con esa conexion cree un objeto connection, testearlo con telnet.
5. Implementar los distintos comandos empezando por el `quit`, después testear cada comando con telnet. (usar el archivo [client.py](./client.py) para sacar ideas de cómo manejar las conexiones).
6. Una vez implementados los comandos , probar el funcionamiento con el cliente que se le entrega en el kickstarter ([client.py](./client.py)).
7. Una vez que funcione el cliente ejecutar el test para probar los casos **“no felices”**.
8. Implementar múltiples clientes utilizando hilos.
9. **(Punto estrella)** Implementar múltiples clientes con `poll` (https://stackoverflow.com/questions/27494629/how-can-i-use-poll-to-accept-multiple-clients-tcp-server-c https://betterprogramming.pub/how-to-poll-sockets-using-python-3e1af3b047).

El cliente y el servidor a desarrollar prodrán estar corriendo en máquinas distintas (sobre la misma red) y el servidor será capaz de manejar varias conexiones a la vez.

![](https://i.ibb.co/0nDdQ01/Captura-desde-2024-04-02-12-03-49.png)

A continuación se muestra un ejemplo de ejecución del servidor atendiendo a un único cliente.
```bash
caro@victoria:~/Ayudantia/Redes$ python server.py
Running File Server on port 19500.
Connected by: ('127.0.0.1', 44639)
Request: get_file_listing
Request: get_metadata client.py
Request: get_slice client.py 0 1868
Closing connection...
```

El servidor debe aceptar en la línea de comandos las opciones:
- `-d directory` para indicarle donde están  los archivos que va a publicar.
- `-p port` para indicarle en que puerto escuchar. Si se omite usará el valor por defecto.
- Deben utilizar el comando `telnet <dir IP> <num Port>` para enviar comandos mal formados o mal intencionados y probar la robustez del servidor.

### Preguntas
1. ¿Qué estrategias existen para poder implementar este mismo servidor pero con capacidad de atender *múltiples clientes simultáneamente*? Investigue y responda brevemente qué cambios serían necesarios en el diseño del código.
2. Pruebe ejecutar el servidor en una máquina del laboratorio, mientras utiliza el cliente desde otra, hacia la ip de la máquina del servidor. ¿Qué diferencia hay si se corre el servidor desde la IP "localhost", "127.0.0.1" o la ip "0.0.0.0"?

## Tarea Estrella
En caso de *implementar* el servidor capacidad de atender *múltiples clientes simultáneamente con poll*, se otorgarán puntos extras. De acuerdo al funcionamiento del mismo y capacidad del alumno de explicar lo realizado en la evaluación oral, se podrán dar hasta 2 puntos extras en la 1er evaluación de la defensa de los laboratorios.

## Requisitos de la entrega
- Las entregas serán a través del repositorio Git provisto por la Facultad para la Cátedra, con **fecha límite indicada en el cronograma del aula virtual**.
- Junto con el código deberá entregar una presentación (tipo powerpoint) y un video de 10 +/-1 minutos. Les damos una estructura de base como idea, pero pueden modificarla/ampliarla.
  
1. **Introducción al proyecto:**
   1. Presenta brevemente el contexto del proyecto y sus objetivos.
   2. Explica la importancia de desarrollar un Protocolo de transferencia de datos.
2. **Responder preguntas como:**
   1. ¿Cómo funciona el paradigma cliente/servidor? ¿Cómo se ve esto en la programación con socket?
   2. ¿Cuál es la diferencia entre Stream (TCP) y Datagram (UDP), desde la perspectiva del socket?
   3. ¿Qué es el protocolo FTP? ¿Para qué sirve?
   4. ¿Qué es base64? ¿Para qué la usamos en el laboratorio?
   5. ¿Qué pasa si queremos enviar un archivo contiene los caracteres \r\n? ¿Cómo lo soluciona esto su código?
3. **Explicar el desarrollo de las funciones principales del servidor.**
4. **Errores y dificultades enfrentadas y cómo se resolvieron.**
5. **Conclusiones:**
   1. Deben agregar un apartado importante aquí mencionando la relación de este lab con el lab anterior de APIS.

- Se deberá entregar código con estilo PEP8.
- El trabajo es grupal. Todos los integrantes del grupo deberán ser capaces de explicar el código presentado.
- No está permitido compartir código entre grupos.

## RECOMENDACIONES
El laboratorio indica que se debe utilizar la versión 3.6 de python para armar un entorno virtual, en este caso utilizaremos **[python3.6.15](https://www.python.org/downloads/release/python-3615/)**. Para hacer un buen manejo de las versiones de python se recomienda instalar **[pyenv](https://github.com/pyenv/pyenv)**. Para instalarlo se debe ejecutar los siguientes comandos:
```bash
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev \
libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git
```

```bash
curl https://pyenv.run | bash
```

Posteriormente deben agregar las siguientes líneas al archivo `.bashrc` o `.zshrc`:
```bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"
```

> Pueden acceder al archivo `.bashrc` o `.zshrc` con el comando `nano ~/.bashrc` o `nano ~/.zshrc`.

Luego se debe cerrar y volver a abrir la terminal para seguir con los siguientes pasos:

- Intalar la versión de python 3.6.15:
  ```bash
  pyenv install 3.6.15 # Instalar Python 3.6.15
  ```
- Establecer la version de python 3.6.15 como la versión local en su directorio actual:
  ```bash
  pyenv local 3.6.15 # Establecer Python 3.6.15 como la versión local
  ```
- Verificar que la versión de python sea la correcta:
  ```bash
  python3 --version # Debe mostrar Python 3.6.15
  ```
- Crear un entorno virtual con la versión de python 3.6.15:
  ```bash
  virtualenv -p /home/{user}/.pyenv/versions/3.6.15/bin/python3.6 .venv # Debe reemplazar {user} por su nombre de usuario
  ```
- Activar el entorno virtual:
  ```bash
  source .venv/bin/activate
  ```

Si se desea establecer una versión global (la que ya tenia u otra) debe instalar la versión de python deseada y luego establecerla como global, por ejemplo la 3.12.2
```bash
pyenv install 3.12.2
pyenv global 3.12.2
```

Con eso conseguiremos que todos los directorios excepto aquellos en los que hayamos establecido una versión local, utilicen la versión global de python que hemos establecido.
Recordar que podemos verificar la versión de python con `python3 --version`.
