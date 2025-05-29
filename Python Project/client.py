import socket
from threading import Thread
from time import sleep
import os
import AppGui  # Python script containing GUI for client.py
import tkinter

USERNAME = ""

# PC: 10.208.244.180:1235 | RPi : 10.95.118.28:1235


# Clasa ce caracterizeaza un dispozitiv de tip client ce utilizeaza socket-uri.
class ClientSideClientDevice:

    BUFFER_SIZE = 4096
    HEADER_LENGTH = 15

    def __init__(self, username: str, family=socket.AF_INET, sock_type=socket.SOCK_STREAM):
        self.socket = socket.socket(family, sock_type)
        self.username = username
        self.family = family
        self.type = sock_type
        self.SERVER_IP = ""
        self.SERVER_PORT = None
        # Attributes characterizing the connection status of client to the server.
        self.valid_address = False
        self.is_connected = False
        self.is_connecting = False
        self.force_disconnect = True
        self.connection_attempts = 0
        # Attributes characterizing the communication for client as sender
        self.message = ""
        self.if_flash_ecu = False
        self.ft_go = True  # File Transfer Go
        self.ft_packets_left = 0
        self.ft_done = False  # File Transfer Done
        self.sending_file = False
        self.sending_message = False
        self.sending_photo = False

        # Start thread for receiving messages.
        thread_Cr = Thread(target=self.receive_message_thread, daemon=True)
        thread_Cr.start()

    # Check if IP address is valid.
    def set_address(self, ip, port):
        try:
            socket.inet_aton(ip)  # Raise socket.error if IP is invalid
            # Double check if IP address is valid
            if ip.count(".") == 3:
                self.SERVER_IP = ip
                try:
                    self.SERVER_PORT = int(port)
                    self.valid_address = True
                except ValueError:
                    self.SERVER_PORT = None
                    self.valid_address = False
        except socket.error:
            self.SERVER_IP = 0
            self.SERVER_PORT = None
            self.valid_address = False

    def connect(self):
        if self.valid_address is True:
            if self.is_connected is False:
                # If the server disconnects, client_receive thread will call connect
                # From main thread we may also press "Connect" button calling "connect()".
                # 2 threads call the same function at the same time -> Concurrency problem may occur
                # Solve concurrency problem with self.is_connecting flag.
                if self.is_connecting is False:
                    self.is_connecting = True
                    # GUI update
                    self.gui_update_constatus()  # Update GUI
                    # Close the old socket that is no longer connected to the server | Make sure it is closed
                    self.socket.close()
                    # Make a new socket with which to connect to the server.
                    self.socket = socket.socket(self.family, self.type)
                    while not self.is_connected:
                        try:
                            self.socket.connect((self.SERVER_IP, self.SERVER_PORT))
                            # Send username right after you connected to the server
                            self.send_message(self.socket, self.username)
                            self.is_connected = True  # Client is now connected to the server
                            self.is_connecting = False  # Client no longer tries to connect.
                            self.force_disconnect = False  # Client is no longer disconnected from server.
                            # GUI update
                            self.gui_update_constatus()  # Update GUI
                        except socket.error:
                            sleep(1)
                            self.connection_attempts += 1
                            if self.connection_attempts >= 3:
                                self.connection_attempts = 0
                                self.is_connecting = False
                                self.gui_update_constatus()  # Update GUI
                                break

    def connect_thread(self):
        if self.is_connecting is False:
            Thread(target=self.connect, daemon=True).start()

    def reconnect(self):
        # force_disconnect is True only if client imposed a disconnect (pressed disconnect).
        if self.force_disconnect is False:
            self.connect()

    def disconnect(self):
        if self.is_connected is True:
            self.force_disconnect = True
            self.socket.close()
            self.is_connected = False
            self.gui_update_constatus()

    """ Function used to send a message """
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

    """ Method used to receive a message."""
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

    """ 
    Receiving code must be placed in a thread because the function "receive_message" is blocking the flow of code. 
    """
    def receive_message_thread(self):
        while True:
            if self.is_connected is True:
                # Receive message from server and check if empty (if empty then we got disconnected from server).
                server_message = self.receive_message(self.socket)

                if server_message is False:
                    # If message_server is False then client_device.is_connected should be set to False.
                    self.is_connected = False
                    self.reconnect()
                    print("CE: Reconnect attempt -> Received end of stream")  # CE = Connection Error
                    continue
                # Check if message is a file packet
                if server_message['file_packet'] is False:
                    # Check if message has info about a file. If not then it is just a regular string.
                    if server_message['meta_file'] is False:
                        if server_message['ack'] is False:
                            print(f'Received message from server : {server_message["data"]}')
                            # Send acknowledgement to server that we've received his message
                            self.send_message(self.socket, server_message['data'], acknowledgement=True)
                            # GUI update.
                            AppGui.textbox_rowrite(app.textbox, f"SERVER > {server_message['data']} \n")

                        elif server_message['ack'] is True:
                            print(f"Acknowledgement from server: {server_message['ack']}")
                            # GUI update.
                            AppGui.textbox_rowrite(app.textbox, "\t | msg ACK \n")
                    # Message has important info about file. Preparing file transfer...
                    elif server_message['meta_file'] is True:
                        if server_message['ack'] is True:
                            if server_message['data'] == "RECVFULLFILE":
                                self.ft_done = True
                                AppGui.textbox_rowrite(app.textbox, "\t | file ACK \n")
                            if server_message['data'] == "SPI_ACK":
                                AppGui.textbox_rowrite(app.textbox, "Info: ECU sent SPI Flash acknowledgement.\n")
                        elif server_message['ack'] is False:
                            # Server detected we previously tried to send a file but didn't send it all
                            SEPARATOR = "<SEPARATOR>"
                            file_name, file_packet_number = server_message['data'].split(SEPARATOR)
                            self.ft_packets_left = int(file_packet_number)
                            self.ft_go = True
            elif self.is_connected is False:
                sleep(1)

    def send_msg(self, message):
        # Don't send empty messages to the server
        if message:
            self.sending_message = True
            # Send message to the server
            self.is_connected = self.send_message(self.socket, message)
            if self.is_connected is False:
                self.reconnect()
                print("Reconnect attempt -> Couldn't send message")
            self.sending_message = False
            
    
    def send_photo_thread(self, photo):
        if self.sending_message is False:
            Thread(target = self.send_photo, args = (photo,), daemon = True).start()

    def send_message_thread(self, message):
        if self.sending_message is False:
            Thread(target=self.send_msg, args=(message,), daemon=True).start()

    def send_file(self, filename, flash_ecu=False):
        self.sending_file = True
        try:
            filesize = os.path.getsize(filename)  # Number of bytes of the file.
        except FileNotFoundError:
            print(f"{filename} doesn't exist.")
            self.sending_file = False
            return False

        SEPARATOR = "<SEPARATOR>"
        fileinfo = f"{filename}{SEPARATOR}{filesize}{SEPARATOR}{flash_ecu}"
        # Send information about file t o the server.
        self.is_connected = self.send_message(self.socket, fileinfo, meta_file=True)
        # There is no reason to start file transfer if there is no connection to the server hence if statement.
        if self.is_connected:
            # Initialize data for file transfer | file_packets_left are initially all the packets that make a file.
            self.ft_packets_left = int(filesize / self.BUFFER_SIZE)
            self.ft_go = True
            self.ft_done = False
            while self.ft_done is False:
                # Send file packets until file transfer is stopped by either EOF or Connection Loss.
                if self.ft_go is True:
                    sent_bytes = filesize - (self.ft_packets_left * self.BUFFER_SIZE +
                                             (filesize - int(filesize / self.BUFFER_SIZE) * self.BUFFER_SIZE))
                    print(f"FT: Resume file transfer: {sent_bytes} sent out of {filesize} bytes")  # FT = File Transfer
                    with open(filename, "rb") as f:
                        f.read(sent_bytes)  # Read from file already sent bytes.
                        while self.ft_go is True:
                            bytes_read = f.read(self.BUFFER_SIZE)  # Bytes to send from file.
                            if not bytes_read:
                                self.ft_go = False  # Nothing left to send, file transfer stop.
                                break
                            self.is_connected = self.send_message(self.socket, bytes_read, file_packet=True)
                            if self.is_connected is False:
                                self.ft_go = False  # Can't send if not connected, file transfer stop.
                                break
                elif self.ft_go is False:
                    # Verifying a condition in a while true loop within a thread is very inefficient.
                    sleep(0.001)  # Commenting sleep will result in lag within main loop.
            print(f"FT: File fully transmitted, {filesize} sent out of {filesize} bytes")  # FT = File Transfer
        self.sending_file = False

    def send_file_thread(self, filename, flash_ecu=False):
        if self.sending_file is False:
            Thread(target=self.send_file, args=(filename, flash_ecu)).start()

    """Method used to interconnect sockets and GUI."""
    def gui_update_constatus(self):
        if self.is_connected is True:
            app.label_constatus2.configure(text="Connected")
            app.connect_animation()
        elif self.is_connected is False:
            if self.is_connecting is True:
                app.label_constatus2.configure(text="Connecting...")
                app.is_connecting_animation()
            elif self.is_connecting is False:
                app.label_constatus2.configure(text="Disconnected")
                app.disconnect_animation()


client_device = ClientSideClientDevice(USERNAME)


# GUI Functions dependent of client.py instances
def gui_config_address():
    entry_input = app.entry_configure_address.get()
    address = entry_input.split(":", 1)
    address[0] = address[0].strip()  # Get rid of unwanted free spaces
    address[1] = address[1].strip()  # Get rid of unwanted free spaces

    # Check if IP address is valid.
    try:
        client_device.set_address(address[0], address[1])
    except IndexError:
        client_device.valid_address = False

    if client_device.valid_address is True:
        app.label_IP_2.configure(text=client_device.SERVER_IP)
        app.label_PORT_2.configure(text=client_device.SERVER_PORT)
        app.button_connect.configure(state="normal")
        app.button_disconnect.configure(state="normal")
    else:
        app.label_IP_2.configure(text="Invalid")
        app.label_PORT_2.configure(text="Invalid")
        app.button_connect.configure(state="disabled")
        app.button_disconnect.configure(state="disabled")


def gui_connect():
    # self.connect is a method that may block the flow of the main thread, thus the need of running it in a
    # secondary thread. If client can't find the server at specified address, it will retry until it can.
    client_device.connect_thread()


def gui_disconnect():
    client_device.disconnect()


def gui_send_message():
    message = app.entry_send_msg.get()
    app.entry_send_msg.delete(0, tkinter.END)
    if message:
        client_device.send_message_thread(message)
        AppGui.textbox_rowrite(app.textbox, client_device.username + " > " + message)


def gui_send_file():
    # Get "Flash ECU" switch status
    switch_flash = app.switch_file_purpose.get()

    # Get file path from the entry then clear the entry
    filename = app.entry_browse_file.get()

    if switch_flash:  # Flash file to ECU
        client_device.send_file_thread(filename, flash_ecu=True)
        AppGui.textbox_rowrite(app.textbox, client_device.username + " > " +
                               f'Flash file "{os.path.basename(filename)}" into ECU')
    elif not switch_flash:  # Don't flash, just send file
        client_device.send_file_thread(filename)
        AppGui.textbox_rowrite(app.textbox, client_device.username + " > " +
                               f'Send file "{os.path.basename(filename)}"')


def gui_press_enter_entry(event):
    gui_send_message()
# End of GUI Functions.


if __name__ == "__main__":
    # Start GUI
    app = AppGui.App()
    # Configure GUI buttons.
    app.button_configure_address.configure(command=gui_config_address)
    app.button_connect.configure(command=gui_connect)
    app.button_disconnect.configure(command=gui_disconnect)
    app.button_send_message.configure(command=gui_send_message)
    app.button_send_file.configure(command=gui_send_file)
    # Configure GUI Entries
    app.entry_send_msg.bind("<Return>", gui_press_enter_entry)
    app.set_username(client_device.username)

    # Get GUI going...
    app.mainloop()
