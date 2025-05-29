import os
import tkinter
from tkinter import filedialog
import customtkinter
from PIL import Image, ImageTk


def _from_rgb(rgb):
    """translates an rgb tuple of int to a tkinter friendly color code
    """
    return "#%02x%02x%02x" % rgb


customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):

    WIDTH = 920
    HEIGHT = 550

    DEFAULT_INFO = "Unknown"
    DEFAULT_CONNECTION_INFO = "Disconnected"

    WIDGET_FGCOLOR = _from_rgb((188, 121, 20))  # "sienna4"
    LABEL_FONT = "Bahnschrift SemiCondensed"
    ENTRY_FONT = "Bahnschrift SemiCondensed"
    TEXTBOX_FONT = "Bahnschrift SemiCondensed"
    BUTTON_FONT = "Bahnschrift SemiCondensed"

    ANIMATION_COUNTER1 = 0
    ANIMATION_ID = 0

    ANIMATION_COUNTER2 = 1
    ANIMATION_ID2 = 0

    def __init__(self):
        super().__init__()
        self.title("Client")
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed

        # ============ create two frames ============

        # configure grid layout (2x1)
        self.grid_columnconfigure(1, weight=1)  # Col1 expands to fill the screen
        self.grid_rowconfigure(0, weight=1)  # Row0 expands to fill the screen

        # Left frame minimum width is 100.
        self.frame_left = customtkinter.CTkFrame(master=self,
                                                 width=100,
                                                 corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nswe")

        self.frame_right = customtkinter.CTkFrame(master=self)
        self.frame_right.grid(row=0, column=1, sticky="nswe", padx=20, pady=10)

        # ===================================== frame_left =======================================================
        self.frame_left.grid_rowconfigure(0, minsize=10)  # empty row with minsize as spacing4
        self.frame_left.grid_rowconfigure(5, weight=1)
        self.frame_left.grid_rowconfigure(7, minsize=20)

        # --- Title Row 1 ---
        self.label_title_1 = customtkinter.CTkLabel(master=self.frame_left,
                                                    text="Client",
                                                    font=(self.LABEL_FONT, -45, "bold"))
        # Obs: Fara padx = 10, se strica marginea din dreapta
        self.label_title_1.grid(row=1, column=0, padx=5, pady=5)

        # --- frame_username Row 2 ---
        self.frame_username = customtkinter.CTkFrame(master=self.frame_left,
                                                     height=50,
                                                     width=50)
        self.frame_username.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        # Obs: frame_address occupies more width than frame_username thus make sure frame_username
        # can expand it's width in order to fill the gaps.
        self.frame_username.grid_columnconfigure(0, weight=1)

        self.label_username_1 = customtkinter.CTkLabel(master=self.frame_username,
                                                       text="Username:",
                                                       font=(self.LABEL_FONT, -22))
        # Obs: label_username_1 overlays frame_username if we don't set a padding when we grid the label.
        # Obs: Give label a fg_color attribute to highlight the effect of overlaying.
        self.label_username_1.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        self.label_username_2 = customtkinter.CTkLabel(master=self.frame_username,
                                                       text=self.DEFAULT_INFO,
                                                       font=(self.LABEL_FONT, -18),
                                                       fg_color=("white", self.WIDGET_FGCOLOR),
                                                       corner_radius=5)
        self.label_username_2.grid(row=2, column=0, sticky="ew", padx=2, pady=(2, 5))

        # --- frame_address  Row 3 ---
        self.frame_address = customtkinter.CTkFrame(master=self.frame_left)
        self.frame_address.grid(row=3, column=0, sticky="new", padx=5, pady=5)
        self.frame_address.grid_columnconfigure(0, weight=1)

        self.label_address_1 = customtkinter.CTkLabel(master=self.frame_address,
                                                      text="Server Address:",
                                                      font=(self.LABEL_FONT, -22))
        self.label_address_1.grid(row=0, column=0, columnspan=2, padx=2, pady=2)

        self.frame_IP = customtkinter.CTkFrame(master=self.frame_address,
                                               fg_color=("white", self.WIDGET_FGCOLOR))
        self.frame_IP.grid(row=1, column=0, padx=2, pady=2, sticky="we")

        self.label_IP_1 = customtkinter.CTkLabel(master=self.frame_IP,
                                                 text="IP:",
                                                 width=50,  # Change width from defaut
                                                 font=(self.LABEL_FONT, -18))
        self.label_IP_1.grid(row=0, column=0, padx=(5, 0), pady=2)

        self.label_IP_2 = customtkinter.CTkLabel(master=self.frame_IP,
                                                 text=self.DEFAULT_INFO,
                                                 font=(self.LABEL_FONT, -18))
        self.label_IP_2.grid(row=0, column=1, padx=(0, 2), pady=(0, 2))

        self.frame_PORT = customtkinter.CTkFrame(master=self.frame_address,
                                                 fg_color=("white", self.WIDGET_FGCOLOR))
        self.frame_PORT.grid(row=2, column=0, padx=2, pady=(2, 5), sticky="we")
        self.label_PORT_1 = customtkinter.CTkLabel(master=self.frame_PORT,
                                                   text="PORT:",
                                                   width=50,
                                                   font=(self.LABEL_FONT, -18))
        self.label_PORT_1.grid(row=0, column=0, padx=(5, 0), pady=2)
        self.label_PORT_2 = customtkinter.CTkLabel(master=self.frame_PORT,
                                                   text=self.DEFAULT_INFO,
                                                   font=(self.LABEL_FONT, -18))
        self.label_PORT_2.grid(row=0, column=1, padx=(0, 2), pady=2)

        # --- frame_constatus Row 4 ---
        self.frame_constatus = customtkinter.CTkFrame(master=self.frame_left)
        self.frame_constatus.grid_columnconfigure(0, weight=1)
        self.frame_constatus.grid(row=4, column=0, sticky="new", padx=5, pady=5)
        self.label_constatus1 = customtkinter.CTkLabel(master=self.frame_constatus,
                                                       text="Connection Status:",
                                                       font=(self.LABEL_FONT, -22))
        self.label_constatus1.grid(row=0, column=0, padx=2, pady=2)
        self.label_constatus2 = customtkinter.CTkLabel(master=self.frame_constatus,
                                                       text=self.DEFAULT_CONNECTION_INFO,
                                                       font=(self.LABEL_FONT, -18),
                                                       fg_color=("white", self.WIDGET_FGCOLOR),
                                                       corner_radius=5)
        self.label_constatus2.grid(row=1, column=0, sticky="ew", padx=2, pady=(2, 5))
        # --- Row5 is spacing ---
        # --- Image label Row 6 ---

        # self.img = Image.open("GUImages/tuiasi.png").resize((190, 180))
        # self.image_wifi = ImageTk.PhotoImage(self.img)

        # self.labelimg = customtkinter.CTkLabel(master=self.frame_left,
        #                                        image=self.image_wifi)
        # self.labelimg.grid(row=5, column=0, sticky="sew")
        # --- Row7 is spacing ---

        # ================================== frame_right ========================================================
        self.frame_right.rowconfigure(0, minsize=10)
        self.frame_right.rowconfigure(2, minsize=5)
        self.frame_right.rowconfigure(4, minsize=5)
        self.frame_right.rowconfigure(6, minsize=5)
        self.frame_right.columnconfigure(0, weight=1)
        self.frame_right.rowconfigure(3, weight=1)

        # --- Row0 is spacing ---
        # --- frame_set_address Row 1 ---
        self.frame_configure_address = customtkinter.CTkFrame(master=self.frame_right,
                                                              height=50)
        self.frame_configure_address.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")
        self.frame_configure_address.columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.frame_configure_address.rowconfigure(1, weight=1)
        self.label_configure_address = customtkinter.CTkLabel(master=self.frame_configure_address,
                                                              text="Configurare Rețea",
                                                              font=(self.LABEL_FONT, -26))
        self.label_configure_address.grid(row=0, column=0, columnspan=5, padx=2, pady=2, sticky="new")

        self.entry_configure_address = customtkinter.CTkEntry(master=self.frame_configure_address,
                                                              font=(self.ENTRY_FONT, -17),
                                                              text_color="gray60")
        self.entry_configure_address.grid(row=1, column=0, columnspan=5, padx=10, pady=2, sticky="ew")
        self.entry_configure_address.insert(0, "Input server's IP:PORT | Ex: 10.95.0.1:1234")
        self.entry_configure_address.bind("<1>", self.click_entry_netconfig)

        self.button_configure_address = customtkinter.CTkButton(master=self.frame_configure_address,
                                                                text="Configure Address",
                                                                font=(self.BUTTON_FONT, -19))
        self.button_configure_address.grid(row=2, column=0, padx=(10, 2), pady=(2, 7), sticky="sw")
        self.label_configure_address_button_separator = customtkinter.CTkLabel(master=self.frame_configure_address,
                                                                               text="|",
                                                                               font=(self.LABEL_FONT, -20),
                                                                               width=50)
        self.label_configure_address_button_separator.grid(row=2, column=1, pady=(2, 7), sticky="sew")
        self.button_connect = customtkinter.CTkButton(master=self.frame_configure_address,
                                                      text="Connect",
                                                      font=(self.BUTTON_FONT, -19),
                                                      state="disabled")
        self.button_connect.grid(row=2, column=2, padx=2, pady=(2, 7), sticky="s")

        self.label_configure_address_button_separator2 = customtkinter.CTkLabel(master=self.frame_configure_address,
                                                                                text="|",
                                                                                font=(self.LABEL_FONT, -20),
                                                                                width=50)
        self.label_configure_address_button_separator2.grid(row=2, column=3, pady=(2, 7), sticky="sew")

        self.button_disconnect = customtkinter.CTkButton(master=self.frame_configure_address,
                                                         text="Disconnect",
                                                         font=(self.BUTTON_FONT, -19),
                                                         state="disabled")
        self.button_disconnect.grid(row=2, column=4, padx=(2, 10), pady=(2, 7), sticky="se")

        # --- Row2 spacing ---
        # --- frame_messagebox Row 3 ---
        self.frame_messagebox = customtkinter.CTkFrame(master=self.frame_right)
        self.frame_messagebox.grid(row=3, column=0, padx=15, pady=5, sticky="nsew")
        self.frame_messagebox.grid_columnconfigure(0, weight=1)
        self.frame_messagebox.grid_rowconfigure(1, weight=1)
        self.label_send = customtkinter.CTkLabel(master=self.frame_messagebox,
                                                 text="Send messages to the server",
                                                 font=(self.LABEL_FONT, -26))
        self.label_send.grid(row=0, column=0, columnspan=2, padx=2, pady=(5, 0))

        self.textbox = customtkinter.CTkTextbox(master=self.frame_messagebox,
                                                font=(self.TEXTBOX_FONT, -20),
                                                state='disabled',
                                                height=100)
        self.textbox.grid(row=1, column=0, columnspan=2, padx=2, pady=2, sticky="nsew")

        self.entry_send_msg = customtkinter.CTkEntry(master=self.frame_messagebox,
                                                     font=(self.ENTRY_FONT, -17))
        self.entry_send_msg.grid(row=2, column=0, padx=(10, 2), pady=(2, 7), sticky="ew")

        self.button_send_message = customtkinter.CTkButton(master=self.frame_messagebox,
                                                           text="Send Message",
                                                           font=(self.BUTTON_FONT, -19))
        self.button_send_message.grid(row=2, column=1, padx=(2, 10), pady=(2, 7))
        # --- Row4 spacing
        # --- frame_files Row 5---
        self.frame_files = customtkinter.CTkFrame(master=self.frame_right)
        self.frame_files.grid(row=5, column=0, padx=15, pady=5, sticky="nsew")
        self.frame_files.grid_columnconfigure(0, weight=1)
        self.label_files = customtkinter.CTkLabel(master=self.frame_files,
                                                  text="Send files to the server",
                                                  font=(self.LABEL_FONT, -26))
        self.label_files.grid(row=0, column=0, columnspan=4, padx=2, pady=(5, 0))

        self.entry_browse_file = customtkinter.CTkEntry(master=self.frame_files,
                                                        font=(self.ENTRY_FONT, -17))
        self.entry_browse_file.grid(row=1, column=0, columnspan=3, padx=(10, 2), pady=(2, 2), sticky="ew")
        self.button_browse_file = customtkinter.CTkButton(master=self.frame_files,
                                                          text="Browse File",
                                                          font=(self.BUTTON_FONT, -19),
                                                          command=self.browse_file)
        self.button_browse_file.grid(row=1, column=3, columnspan=1, padx=(2, 10), pady=(2, 2))

        self.frame_label_file_purpose = customtkinter.CTkFrame(master=self.frame_files,
                                                               fg_color=("white", "#343638"))
        self.frame_label_file_purpose.grid(row=2, column=0, padx=(10, 2), pady=(2, 7), sticky="w")
        self.label_file_purpose = customtkinter.CTkLabel(master=self.frame_label_file_purpose,
                                                         text="Flash ECU with file",
                                                         font=(self.LABEL_FONT, -19))
        self.label_file_purpose.grid(row=0, column=0, padx=2, pady=(2, 0), stick="w")
        self.label_file_purpose_description = customtkinter.CTkLabel(master=self.frame_label_file_purpose,
                                                                     text="Decide whether to send a file or to flash\n"
                                                                          "the ECU connected to the server",
                                                                     font=(self.LABEL_FONT, -14),
                                                                     text_color="gray60",
                                                                     width=50,
                                                                     justify=tkinter.LEFT)
        self.label_file_purpose_description.grid(row=1, column=0, padx=2, pady=(0, 2), sticky="nw")

        self.label_file_purpose_separator = customtkinter.CTkLabel(master=self.frame_files,
                                                                   text="|",
                                                                   font=(self.LABEL_FONT, -20),
                                                                   width=15)
        self.label_file_purpose_separator.grid(row=2, column=1, pady=(2, 7))

        self.switch_file_purpose = customtkinter.CTkSwitch(master=self.frame_files,
                                                           text="",
                                                           height=24,
                                                           width=44)
        self.switch_file_purpose.grid(row=2, column=2, padx=2, pady=(2, 7))

        self.button_send_file = customtkinter.CTkButton(master=self.frame_files,
                                                        text="Send File",
                                                        font=(self.BUTTON_FONT, -19))
        self.button_send_file.grid(row=2, column=3, padx=(2, 10), pady=(2, 7))
        # --- Row6 spacing ---

    def on_closing(self, event=0):
        self.destroy()

    def set_username(self, username):
        self.label_username_2.configure(text=username)

    def click_entry_netconfig(self, event):
        if self.entry_configure_address.text_color == "gray60":
            self.entry_configure_address.delete(0, tkinter.END)
            self.entry_configure_address.configure(text_color="gray85")

    def browse_file(self):
        filetypes = (("All files", "*.*"), ("hex files", "*.hex"))
        filename = filedialog.askopenfilename(title="Open a file",
                                              initialdir=os.getcwd(),
                                              filetypes=filetypes)
        self.entry_browse_file.delete(0, tkinter.END)
        self.entry_browse_file.insert(0, filename)

    def animation_textcolor_pulse(self, ctk_element, c1, c2, n=10):
        if self.ANIMATION_COUNTER1 < n:
            # Compute the color to assign to CTk Element
            c = [c1[j] + int((float(self.ANIMATION_COUNTER1 / n)) * (c2[j] - c1[j])) for j in range(3)]
            # Recall function after 100ms
            tt1 = self.ANIMATION_COUNTER1 ** 2   # Transition Time 1
            self.ANIMATION_ID = self.after(tt1,
                                           lambda x=ctk_element, y=c1, z=c2: self.animation_textcolor_pulse(x, y, z))
            # Configure CTk Element
            ctk_element.configure(text_color=(_from_rgb(tuple(c))))
            self.ANIMATION_COUNTER1 += 1
        elif n <= self.ANIMATION_COUNTER1 < 2*(n-1)+1:
            c = [c1[j] + int((float((2*(n-1)-self.ANIMATION_COUNTER1) / n)) * (c2[j] - c1[j])) for j in range(3)]
            tt2 = (2*(n-1)-self.ANIMATION_COUNTER1) ** 2  # Transition Time 2
            self.ANIMATION_ID = self.after(tt2,
                                           lambda x=ctk_element, y=c1, z=c2: self.animation_textcolor_pulse(x, y, z))
            ctk_element.configure(text_color=(_from_rgb(tuple(c))))
            self.ANIMATION_COUNTER1 += 1
        else:
            # Prepare to restart process
            self.ANIMATION_COUNTER1 = 0

    def connect_animation(self):
        if self.label_constatus2.text_color[1] != "#DCE4EE":
            self.after_cancel(self.ANIMATION_ID)
            self.ANIMATION_COUNTER1 = 0
        self.animation_textcolor_pulse(self.label_constatus2, [220, 228, 238], [25, 150, 72])

    def disconnect_animation(self):
        if self.label_constatus2.text_color[1] != "#DCE4EE":
            self.after_cancel(self.ANIMATION_ID)
            self.ANIMATION_COUNTER1 = 0
        self.animation_textcolor_pulse(self.label_constatus2, [220, 228, 238], [221, 0, 0])

    def is_connecting_animation(self):
        if self.label_constatus2.text.rstrip('.') == "Connecting":
            self.label_constatus2.configure(text=f"Connecting{'.'*self.ANIMATION_COUNTER2}")
            self.ANIMATION_COUNTER2 += 1
            if self.ANIMATION_COUNTER2 >= 4:
                self.ANIMATION_COUNTER2 = 1
            self.ANIMATION_ID2 = self.after(500, self.is_connecting_animation)


# Write inside a readonly textbox
def textbox_rowrite(textbox, message):
    textbox.configure(state="normal")
    textbox.insert("insert", message)
    textbox.configure(state="disabled")
    textbox.yview(tkinter.END)

