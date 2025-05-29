"""
SPI Bit-Banging Python v3
Raspberry PI as Master
"""
# If device is not a Raspberry Pi, do not download module RPi.
import RPi.GPIO as GPIO
from time import sleep


def get_bit(u8, bit):
    return (u8 >> bit) & 0x01


def print_bites(u8):
    if 0 <= u8 <= 255:
        for i in range(7, -1, -1):
            print(get_bit(u8, i), end="")
        print("")
    else:
        print(f"{u8} > 255")


def get_bit_gpio(u8, bit):
    return GPIO.HIGH if get_bit(u8, bit) else GPIO.LOW


class SPIMaster:
    T2_1_ADD_WIDTH_TIME = 1E-5
    TIME_INITIALIZATION = 1E-1
    """
    If messages are not transmitted correctly TIME_BETWEEN_CHAR_SEND or RECV should be increased.
    Also uncommenting sleeps in "write_nd_receive" method may also be taken into consideration if
    messages aren't transmitted accordingly.
    """
    TIME_BETWEEN_CHAR_SENT = 1E-3
    TIME_BETWEEN_CHAR_RECV = 1E-3

    def __init__(self, sck, miso, mosi, ss):
        self.SCK = sck
        self.MISO = miso
        self.MOSI = mosi
        self.SS = ss
        self.SPDR = 0xFF

        # Init Pins Purpose
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.SCK, GPIO.OUT)  # SCK output
        GPIO.setup(self.MISO, GPIO.IN)  # MISO input
        GPIO.setup(self.MOSI, GPIO.OUT)  # MOSI output
        GPIO.setup(self.SS, GPIO.OUT)  # SS output
        # Init Pins State
        GPIO.output(self.SCK, GPIO.LOW)  # SCK is active HIGH
        GPIO.output(self.MOSI, GPIO.HIGH)
        GPIO.output(self.SS, GPIO.HIGH)  # SS is active LOW

    def reinit_pins(self):
        # Init Pins Purpose
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.SCK, GPIO.OUT)  # SCK output
        GPIO.setup(self.MISO, GPIO.IN)  # MISO input
        GPIO.setup(self.MOSI, GPIO.OUT)  # MOSI output
        GPIO.setup(self.SS, GPIO.OUT)  # SS output
        # Init Pins State
        GPIO.output(self.SCK, GPIO.LOW)  # SCK is active HIGH
        GPIO.output(self.MOSI, GPIO.HIGH)
        GPIO.output(self.SS, GPIO.HIGH)  # SS is active LOW

    def write_nd_receive(self, data):
        # SS low active
        GPIO.output(self.SS, GPIO.LOW)
        self.SPDR = data
        # Set MSB MOSI
        GPIO.output(self.MOSI, get_bit_gpio(self.SPDR, 7))
        self.SPDR = (self.SPDR << 1) & 0xFF
        for i in range(8):
            # SCK HIGH -> Sample MISO
            GPIO.output(self.SCK, GPIO.HIGH)
            # Sample MISO right after clock became HIGH
            self.SPDR |= GPIO.input(self.MISO)

            # sleep(self.T2_1_ADD_WIDTH_TIME)

            # SCK LOW -> Shift MOSI
            GPIO.output(self.SCK, GPIO.LOW)
            # Shift MOSI right after clock became LOW
            GPIO.output(self.MOSI, get_bit_gpio(self.SPDR, 7))
            if i < 7:
                self.SPDR = (self.SPDR << 1) & 0xFF
            # sleep(self.T2_1_ADD_WIDTH_TIME)
        # Configure SS inactive.
        GPIO.output(self.SS, GPIO.HIGH)

    # Send a message
    def send_msg(self, msg):
        self.write_nd_receive(1)
        # print("---------------SEND_MSG--------------- Sent 1, next is first char in str.")
        for i in range(len(msg)):
            sleep(self.TIME_BETWEEN_CHAR_SENT)
            self.write_nd_receive(ord(msg[i]))
            # print(hex(self.SPDR))
        sleep(self.TIME_BETWEEN_CHAR_SENT)
        self.write_nd_receive(0)
        # print(hex(self.SPDR))
        # print("---------------END_SEND_MSG--------------- Sent 0.")

    def recv_msg(self):
        cuv = ""
        sleep(self.TIME_BETWEEN_CHAR_RECV)
        self.write_nd_receive(0xFF)
        # print(f"---------------START_RECV_MSG--------------- RECEIVED: {self.SPDR}")
        if self.SPDR == 1:
            while self.SPDR != 0:
                sleep(self.TIME_BETWEEN_CHAR_RECV)
                self.write_nd_receive(0xFF)
                if self.SPDR != 0:
                    cuv += chr(self.SPDR)
        elif self.SPDR != 1:
            return ""
        return cuv

    @staticmethod
    def end_comm():
        GPIO.cleanup()
