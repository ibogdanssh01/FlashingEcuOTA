import socket
import select
from threading import Thread
from threading import Event
from time import sleep
import os
import subprocess

# RpiSpi module is used only when server is a Raspberry Pi that uses SPI.
try:
    import RpiSpi
except ImportError:
    RpiSpi = False
    print("Server is either not a Raspberry Pi or module for SPI couldn't be found | SPI Disabled.")
RPI_SPI_EN = bool(RpiSpi)  # Only true if import was done without an error.


# PC: 10.208.244.180 | RPi : 10.95.118.28
IP = socket.gethostbyname(socket.gethostname())  # WLAN IP
PORT = 1235


class ServerSideServerDevice:

    HEADER_LENGTH = 15
    BUFFER_SIZE = 4096

    def __init__(self, ip, port):
        self.IP = ip
        self.PORT = port
        self.server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.IP, self.PORT))
        self.server_socket.listen()

        # Create a list in which to store all socket object we will work with.
        self.sockets_list = [self.server_socket]
        # Create a dictionary in which to store clients usernames.
        self.clients_dict = {}

        # File receiving variables
        self.file_sr = True  # file_successfully_received
        self.remaining_packets = True
        self.metapack = True
        self.file_dict = {'username': "",
                          'name': "",
                          'size': 0,
                          'packets_recv': 0,
                          'critical': "",
                          'flash': False}
        self.AVR_FLASH_STATE = False
        self.AVR_FLASH_client_socket = None

        # When event_Ss is set, you want to send data to a known client.
        self.event_Ss = Event()  # Event Send Socket
        # When there is at least 1 client socket in socket_list, set this event. Otherwise Clear.
        # set&clear from thread_SaSr. thread_Ss waits for this event.
        self.event_Vsl = Event()  # Event Verify Sockets List
        thread_SaSr = Thread(target=self.server_accept_and_receive, daemon=True)
        thread_SaSr.start()  # Thread Server Accept, Server Receive
        self.user_to_send = ""
        self.message_to_send = ""
        thread_Ss = Thread(target=self.server_send, daemon=True)
        thread_Ss.start()  # Thread Server Send

        print(f'Listening for connections on {IP} : {PORT}...')

    # Function used to send a message
    def send_message(self, client_socket, msg, encoding="utf-8", acknowledgement: bool = False,
                     meta_file: bool = False, file_packet: bool = False):
        # Ex: full_msg = '5_1_0_0   Motor'  |  Min length message is HEADER+MSG = 10+0 = 10
        # Header contains message length
        header = str(len(msg))
        # Header contains an acknowledgement flag
        if acknowledgement:
            header += "_1"
        elif not acknowledgement:
            header += "_0"
        # Header contains meta about file
        if meta_file:
            header += "_1"
        elif not meta_file:
            header += "_0"
        # Header contains critical file flag
        if file_packet:
            header += "_1"
        elif not file_packet:
            header += "_0"

        # full_msg is the message we send(HEADER + MESSAGE).
        if file_packet is False:
            full_msg = f'{header:<{self.HEADER_LENGTH}}' + msg
        else:
            full_msg = bytes(f'{header:<{self.HEADER_LENGTH}}', "utf-8") + msg

        try:
            if file_packet is False:
                client_socket.send(full_msg.encode(encoding))
            elif file_packet is True:
                client_socket.send(full_msg)
            # If we send a message but server has been closed in the meanwhile, a socket.error will be raised.
        except socket.error as e:
            # print(f'{e} - There is no endpoint to send the message. client_socket.send exception')
            # If message hasn't been successfully sent, return False.
            return False
        # If message has been successfully sent, return True.
        return True

    # Reference: https://stackoverflow.com/questions/17667903/python-socket-receive-large-amount-of-data
    @staticmethod
    def recvall(sock, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    # Method used to receive a message.
    def receive_message(self, client_socket, encoding='utf-8'):
        try:
            # Ex: message_header = '15_1_0_0  ' (codat in octeti utf-8)
            message_header = self.recvall(client_socket, self.HEADER_LENGTH)
            # Client-ul s-a deconectat => Low-level nu se mai trimite nimic => In python message_header = "".
            if not len(message_header):
                return False

            # header_infolist[0] = Length of the message | header_infolist[1] = Acknowledgement Status ...
            header_infolist = message_header.decode(encoding).split("_")
            # Extract message_length from header as integer
            message_length = int(header_infolist[0])
            # Extract message acknowledgement status as boolean
            message_ack = bool(int(header_infolist[1]))
            # Extract message isfile status as boolean
            message_meta_file = bool(int(header_infolist[2]))
            # Extract message critical_file status as boolean
            message_file_packet = bool(int(header_infolist[3]))

            # Receive useful data
            # message_data = client_socket.recv(message_length)
            message_data = self.recvall(client_socket, message_length)
            return {'header': message_header.decode(encoding),
                    'ack': message_ack,
                    'meta_file': message_meta_file,
                    'file_packet': message_file_packet,
                    'data': message_data if message_file_packet else message_data.decode(encoding)}
        except:
            # Something went wrong like empty message or client exited abruptly.
            return False

    @staticmethod
    def save_packet(filename, recv_bytes):
        # Write packet on disk
        with open(filename, "ab") as f:
            f.write(recv_bytes)

    # File Transfer Check
    # Check if client has been previously connected to the server. If it was, then check if he tried to send a file to
    # the server. If he did, check if he sent the whole file. If not, return the number of the last packet received.\
    def ft_check(self, username, client_socket):
        # Check if the client that just connected was the one trying to send a file.
        if username == self.file_dict['username']:
            # Check if there are still file bytes to receive from client.
            if self.file_dict['size'] > 0:
                # Get number of last packet received by the server.
                packet_number = int(self.file_dict['size']/self.BUFFER_SIZE)
                # Send info about current state of the file transfer to the client.
                SEPARATOR = "<SEPARATOR>"
                file_info = f"{self.file_dict['name']}{SEPARATOR}{packet_number}"
                self.send_message(client_socket, file_info, acknowledgement=False, meta_file=True)

    # server_accept_and_receive is a thread. select.select is blocking. receive_message is blocking.
    # Accept clients that request to connect to server. Read messages from clients. Receive files from clients.
    def server_accept_and_receive(self):
        while True:
            # select.select returns list of sockets that we can read from or sockets that raise an exeption.
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
            for notified_socket in read_sockets:
                # If server_socket is in read_sockets, it means a client has requested to connect.
                if notified_socket == self.server_socket:
                    client_socket, client_address = self.server_socket.accept()
                    # Get client username
                    client_username = self.receive_message(client_socket)

                    # Verifica daca conexiunea s-a sfarsit inainte de a se trimite username-ul.
                    if client_username is False:
                        continue

                    # Adauga client in lista pentru a-i citi mesajele ulterioare
                    self.sockets_list.append(client_socket)
                    self.clients_dict[client_socket] = client_username['data']
                    print(f'Accepted new connection from {client_address[0]}:{client_address[1]}')

                    # Seteaza Event-ul "Verify Sockets List" deoarece acum avem minim 1 client in lista.
                    if not self.event_Vsl.is_set():
                        self.event_Vsl.set()

                    # Verify whether client has been connected in the past and if he was sending a file.
                    self.ft_check(client_username['data'], client_socket)

                elif notified_socket != self.server_socket:
                    # Receive message from client
                    message = self.receive_message(notified_socket)

                    # Check if message has been successfully received
                    if message is False:
                        print(f'Closed connection from {self.clients_dict[notified_socket]}:')
                        self.sockets_list.remove(notified_socket)
                        self.clients_dict.pop(notified_socket)
                        # If we only have server_socket in sockets_list, then clear Vsl event.
                        if len(self.sockets_list) < 2:
                            self.event_Vsl.clear()
                        continue

                    # Check if message is a file packet.
                    if message['file_packet'] is False:
                        # Check if message have important info about a file. If not then it's just a regular message
                        if message['meta_file'] is False:
                            if message['ack'] is False:
                                print(f'Received msg from > {self.clients_dict[notified_socket]} : {message["data"]}')
                                self.send_message(notified_socket, message['data'], acknowledgement=True)
                            elif message['ack'] is True:
                                print(f'Acknowledgement from > {self.clients_dict[notified_socket]} : {message["ack"]}')
                        elif message['meta_file'] is True:
                            SEPARATOR = "<SEPARATOR>"
                            file_list = message['data'].split(SEPARATOR)
                            self.file_dict['username'] = self.clients_dict[notified_socket]
                            self.file_dict['name'] = "a" + os.path.basename(file_list[0])
                            self.file_dict['size'] = int(file_list[1])
                            self.file_dict['flash'] = True if file_list[2] == "True" else False
                            if os.path.isfile(self.file_dict['name']):
                                os.remove(self.file_dict['name'])
                            print(self.file_dict)
                    elif message['file_packet'] is True:
                        self.save_packet(self.file_dict['name'], message['data'])
                        # Tell client you've received the whole file.
                        self.file_dict['size'] -= self.BUFFER_SIZE
                        if self.file_dict['size'] <= 0:
                            self.send_message(notified_socket, "RECVFULLFILE", acknowledgement=True, meta_file=True)
                            # If client intent was to flash the file, do it after receiving it all.
                            if self.file_dict['flash'] is True:
                                print("Flashing ECU...")
                                self.AVR_FLASH_STATE = True
                                self.AVR_FLASH_client_socket = notified_socket

            for notified_socket in exception_sockets:
                print("notified_socket in exception_sockets? What happeneed?")
                self.sockets_list.remove(notified_socket)
                self.clients_dict.pop(notified_socket)

    # server_send is a thread. event.wait() is a blocking function thus thread is a good use.
    # To send a message you need to assign username global variable from ANOTHER Thread, and
    # execute event_Ss.set().
    def server_send(self):
        while True:
            # Wait for clients to join the server <=> sockets_list to contain client sockets.
            self.event_Vsl.wait()
            # Wait for username to be set from another Thread thus event will be set.
            self.event_Ss.wait()
            # Refresh username list in case a new user has been added
            username_list = list(self.clients_dict.values())
            # Check if the username is connected to the server(Are un client_socket asociat).
            if self.user_to_send in username_list:
                # Get the client socket that you want to send a message from socket:username dict.
                username_index = username_list.index(self.user_to_send)
                client_socket = list(self.clients_dict.keys())[username_index]

                # Don't send empty strings
                if self.message_to_send:
                    self.send_message(client_socket, self.message_to_send)
            # Clear event to prepare for another request from another thread to send a messages.
            self.event_Ss.clear()

    def send_to_client(self, username, message):
        self.user_to_send = username
        self.message_to_send = message
        self.event_Ss.set()  # Event set, ready to send.


server_device = ServerSideServerDevice(IP, PORT)

if __name__ == "__main__":

    # If device is Raspberry Pi, initialize SPI.
    if RPI_SPI_EN:
        raspberry_spi = RpiSpi.SPIMaster(24, 18, 23, 16)
    else:
        raspberry_spi = None

    while True:
        sleep(0.5)
        # server_device.send_to_client("user1", input("SERVER> "))
        # If device is Raspberry Pi and SPI is enabled, try to communicate with AVR through SPI.

        # Check if we need to flash a file we've received.
        if server_device.AVR_FLASH_STATE is True:
            server_device.AVR_FLASH_STATE = False
            # subprocess.run is a blocking method. Wait until command for flash ECU is executed.
            x = subprocess.run(
                ['sudo', 'avrdude', '-p', 'atmega328', '-C', '/home/pi/avrdude_gpio.conf', '-c',
                 'pi_1', '-v', '-U', f'flash:w:{os.path.basename(server_device.file_dict["name"])}:i'])
            # Check if ECU flashed successfully.
            if x.returncode == 0:
                # Check if SPI is activated.
                if RPI_SPI_EN:
                    sleep(raspberry_spi.TIME_INITIALIZATION)  # Wait init time for ATMEGA's SPI.
                    try:
                        raspberry_spi.reinit_pins()
                        print("SPI: Try start SPI Comm")
                        raspberry_spi.send_msg("FLASH")
                        spi_msg = raspberry_spi.recv_msg()
                        raspberry_spi.end_comm()
                        # Tell Client, ECU acknowledged flash through SPI Communcation
                        if spi_msg == "ACK_FLASH":
                            print("SPI: Successfully received acknowledgement from ECU.")
                            server_device.send_message(server_device.AVR_FLASH_client_socket,
                                                       "SPI_ACK", acknowledgement=True, meta_file=True)
                        else:
                            print("SPI:ECU may still be flashed but there is no acknowledgement through SPI")

                    except AttributeError as e:
                        print(f"SPI: RPI_SPI Error: {e}")
                else:
                    print("SPI: ECU Flashed correctly but SPI Comm is not activated.")
