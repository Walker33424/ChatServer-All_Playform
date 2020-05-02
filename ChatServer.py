# -*- coding:UTF-8 -*-
import threading as t
import socket as s
from random import random
from time import *
import sys
import bz2
from copy import *
# from typing import Any, Tuple
import tkinter.messagebox as m
from time import sleep
import time


class ChatServer:
    def __init__(self, port, address, server_name, max_file_size, log_file_route, transfer_ip=None,
                 transfer_port=None, enable_transfer=False, get_info=False, share_port=None, enable_broadcast=True):
        # enable_transfer:是否从转发至其他服务器
        # get_info:从其他服务器获取信息？
        self.connect_number = 0
        self.port = port
        self.transfer_ip = transfer_ip
        self.get_info = get_info
        self.enable_broadcast = enable_broadcast
        self.base_transfer = s.socket()
        self.share_connects = []
        self.get_info_sock = s.socket()
        self.get_info_state = False
        self.transfer_port = transfer_port
        self.share_port = share_port
        try:
            if enable_transfer and get_info:
                self.base_transfer.bind(("0.0.0.0", share_port))
                self.base_transfer.listen(5)
                self.get_info_sock.connect((transfer_ip, transfer_port))
            elif enable_transfer:
                self.base_transfer.bind(("0.0.0.0", share_port))
                self.base_transfer.listen(5)
            elif get_info:
                self.get_info_sock.connect((transfer_ip, transfer_port))
            else:
                pass
        except ConnectionError:
            self.get_info = False
            self.get_info_state = False
        else:
            self.get_info_state = True
        self.max_file_size = max_file_size
        self.thread_number = 0
        self.log_file_route = log_file_route
        self.files = []
        self.state = False
        self.file = open("ChatMessages.txt", "a+", encoding="utf-8")
        self.get_file_sock = s.socket()
        self.get_file_sock.bind(("0.0.0.0", self.port + 1))
        self.get_file_sock.listen(75)
        self.check_sock = s.socket()
        self.transfers = []
        self.send_message_state = []
        self.users = []
        self.baned_ip = []
        self._file_lock = t.Lock()
        self.ban_ip = None
        self._lock = t.Lock()
        self.server_name = server_name
        self.used_name = []
        self.address = address
        self.enable_transfer = enable_transfer
        self.new_message = None
        self.cmd = {"IP": "", "cmd": ""}
        self._number = 0
        self.old_message = None
        self.log_error = False
        if self.log_file_route:
            self.writer = self.log_writer(file_route=self.log_file_route)
        else:
            self.writer = self.log_writer()
        next(self.writer)
        self.writer.send("Server opened")

    def log_writer(self, file_route="Server log.log"):
        file = None
        if not self.log_error:
            try:
                file = open(file_route, encoding="utf-8", mode="a+")
            except (FileNotFoundError, OSError) as error_data:
                m.showerror("Log Write ERROR", (repr(type(error_data) + str(error_data))))
                self.log_error = True
        else:
            file = open("Client log.log", "a+", encoding="utf-8")
        while True:
            content = yield None
            file.write(ctime() + ":" + content + "\n")
            file.flush()

    def check_connect_timeout(self, sock):
        time.sleep(10)
        if self.state:
            return
        else:
            sock[0].close()
            return

    def file_send(self):
        while True:
            self.state = False
            sock = self.get_file_sock.accept()
            if sock[1][0] in self.baned_ip:
                sock[0].send("ERROR:你已被封禁".encode())
                sock[0].close()
                continue
            self.writer.send("New file transmission connect" + sock[1][0])
            print("New file transmission connect")
            t.Thread(target=self.check_connect_timeout, args=(sock,)).start()
            try:
                filename = sock[0].recv(102400)
            except OSError:
                print("time out")
                continue
            self.state = True
            print("filename.split(b':')[1]:", filename.split(b":")[1])
            print(filename.split(b":")[0])
            try:
                if filename[:8] == b"REQUEST:":
                    try:
                        data = open("data/" + filename[8:].decode(), "rb").read()
                    except FileNotFoundError:
                        sock[0].send(b"ERROR not found")
                        self.writer.send(sock[1][0] + "Request File:" + filename[8:].decode() + ", Not found")
                    else:
                        self.writer.send(sock[1][0] + "Successfully request file:" + filename[8:].decode())
                        sock[0].sendall(data + b"-!end!-")
                        sock[0].close()
                        continue
                elif filename.split(b"!:!:", 3)[1] == b"UPLOAD":
                    filename = filename.split(b"!:!:")
                    self.writer.send(sock[1][0] + "Upload file:" + filename[1].decode())
                    if int(filename[2]) > self.max_file_size:
                        self.writer.send(sock[1][0] + ":Upload File size too big")
                        for x in range(6):
                            sock[0].send(b"ERROR File size must > " + str(self.max_file_size).encode() + b"B")
                            sock[0].close()
                            continue
                    file_data = filename[3]
                    self.writer.send(sock[1][0] + "Successfully upload file")
                    for x in range(6):
                        sock[0].send(b"Uploaded")
                    if b"-!end of file!-" not in file_data:
                        print("data has more")
                        while True:
                            file_data += sock[0].recv(1024000)
                            if b"-!end of file!-" in file_data:
                                print("break")
                                break
                    print("processing data")
                    message = (time.ctime() + " " + filename[0].decode() + "(" + sock[1][0] + ")" + "." + filename[0].
                               decode().split(".")[-1]).strip() + "File"
                    message = message.strip()
                    message = message.replace(":", " ")
                    message = message.replace("(", "I")
                    message = message.replace(")", "P")
                    message = message.replace(" ", "")
                    file = open("data/0" + message[:-4], "wb")
                    file.write(file_data[:-15])
                    file.close()
                    print("send message")
                    self._lock.acquire()
                    self.new_message = deepcopy(message + "\n")
                    self._lock.release()
                else:
                    self.writer.send(sock[1][0] + ":Dont know how to continue:" + filename.decode())
                    sock[0].send(b"ERROR403")
                    sock[0].close()
                    continue
            except Exception as error_data:
                print(type(error_data)(str(error_data)))

    def transfer(self):
        # 把数据向右传播
        old_message = ""
        while True:
            sleep(0.1)
            if self.old_message != self.new_message and old_message != self.new_message:
                for sock_right in self.transfers:
                    for x in range(6):
                        sock_right.send(bz2.compress(self.new_message.encode("utf-32")))
                old_message = deepcopy(self.old_message)

    def transfer_base(self):
        # 监听要来共享数据的服务器
        while True:
            client, address = self.base_transfer.accept()
            self.transfers.append(client)
            self.share_connects.append(repr(address))
            # 为未来同时处理多个服务器做准备
            self.writer.send("Share information:" + address[0])

    def transfer_connect(self):
        # 监听来自左边的消息
        while True:
            information = self.get_info_sock.recv(102400)
            if not information:
                self.get_info_sock.close()
                self.get_info_sock = s.socket()
                self.get_info_state = False
                m.showerror("ERROR!", "Base server " + self.get_info_sock.getsockname()[0] + " Connect Lost!")
            print("share information", information)
            self._lock.acquire()
            self.new_message = deepcopy(information)
            self._lock.release()

    def check_message_send(self):
        while True:
            if self._lock.locked():
                sleep(2.5)
                self._lock.release()
            if not all(self.send_message_state):
                self._lock.acquire()
                sleep(5)
            else:
                self._lock.release()

    def enter_command(self):
        while True:
            command = input("Command:")
            comm = command.split(maxsplit=2)
            if comm and comm[0] in ["ban", "un_ban", "show_baned", "cmd", "connect_other", "disconnection"]:
                if comm[0] == "ban":
                    self.ban_ip = comm[1]
                    self.baned_ip.append(comm[1])
                elif comm[0] == "un_ban":
                    self.ban_ip = None
                    try:
                        self.baned_ip.remove(comm[1])
                    except (IndexError, ValueError):
                        print("IP isn't in baned ip")
                elif comm[0] == "show_baned":
                    print(self.baned_ip)
                # elif comm[0] == "cmd":
                #   self.cmd["IP"] = comm[1]
                #   self.cmd["cmd"] = comm[2]
                elif comm[0] == "connect_other":
                    self.get_info = True
                    self.get_info_sock.connect((comm[1], int(comm[2])))
                elif comm[0] == "disconnection":
                    self.get_info = False
                    self.get_info_state = False
                    self.get_info_sock.close()
                    self.get_info_sock = s.socket()
                    t.Thread(target=self.file_send).start()

            else:
                print("Unknown command")
                self.writer.send("Enter Unknown Command:" + command)
                continue
            self.writer.send("Enter command:" + command)

    def processing_communication(self, socket_, name1):
        """Broadcasting information to users
        user <- data <- server

        """
        index = None
        self.thread_number += 1
        while True:
            if name1 == "RENAME FAILED":
                ran = random()
                if ran in self.used_name:
                    continue
                else:
                    break
            else:
                break
        self.send_message_state.append(name1)
        try:
            index = self.send_message_state.index(name1)
        except ValueError:
            self.writer.send(socket_[1][0] + "Connect Error")
            socket_[0].send(bz2.compress("你的连接存在错误, 请重新连接(connect wrong happen, please try again)"))
            socket_[0].close()
        self.connect_number += 1
        # active count return active count(len(t.enumerate()))
        self.new_message = ""
        self.old_message = ""
        while True:
            self.send_message_state[index] = False
            try:
                if self.new_message.strip() != self.old_message.strip():
                    for q1 in range(6):
                        socket_[0].send(bz2.compress((self.new_message + "-!seq!-").encode("UTF-32")))
                    self.old_message = deepcopy(self.new_message)
                    self.send_message_state[index] = True
                    # 释放 Global Interpreter Lock
                    self._lock.acquire()
                    self._lock.release()
                if socket_[1][0] == self.ban_ip:
                    try:
                        print(socket_[1][0] + " thread2 closed")
                        for q1 in range(6):
                            socket_[0].send(bz2.compress("友好的中文提示:你已被踢出服务器, 并且在管理员没有取消封杀的情况下无法再次加入".encode("utf-32")))
                        socket_[0].close()
                        self.writer.send("Baned IP:" + socket_[1][0] + ", Disconnected")
                    except OSError:
                        self.connect_number -= 1
                        self.send_message_state[index] = True
                        return
                    return
                # elif self.cmd["IP"] == socket_[1][0]:
                #   socket_[0].send(bz2.compress(("Command:" + self.cmd["cmd"]).encode("utf-32")))
                #   self.cmd = {"IP": "", "cmd": ""}
            except ConnectionResetError:
                self.writer.send("Disconnected from " + socket_[1][0])
                self.send_message_state[index] = True
                self.connect_number -= 1
                return

    def radio_broadcast(self):
        sock = s.socket(type=s.SOCK_DGRAM)
        sock.setsockopt(s.SOL_SOCKET, s.SO_BROADCAST, 1)
        sock.bind(("0.0.0.0", 18500))
        print("Start sending broadcast packets")
        self.writer.send("Start sending broadcast packets")
        if self.get_info:
            transfer = "Transfer Server(并联服务器, 与" + self.transfer_ip + "共享信息)"
        else:
            transfer = ""
        while True:
            sock.sendto(("Server:" + self.server_name + transfer + ", Port:" + str() +
                         ", Sub servers: " + ",".join(self.share_connects)).encode(), (self.address, 13365))
            sleep(5)

    def file_request_reset(self):
        while True:
            try:
                client, address = self.get_file_sock.accept()
                client.send(("reset " + self.transfer_ip + " " + str(self.transfer_port)).encode())
                client.close()
            except ConnectionError:
                if not self.get_info_state:
                    return
                continue

    def processing_communication2(self, socket_):
        message1 = ""
        """

        user -> data -> server

        """
        self.connect_number += 1
        while True:
            try:
                if socket_[1][0] == self.ban_ip:
                    print(socket_[1][0] + " thread1 closed")
                    self.connect_number -= 1
                    socket_[0].close()
                    return
                message1 = socket_[0].recv(102400)
                message1 = bz2.decompress(message1).decode("utf-32")
                if not message1:
                    self.connect_number -= 1
                    return
                if message1.startswith("Command Response:"):
                    response = deepcopy(message1)
                    print(socket_[1][0] + response)
                    continue
                message = message1.split("-!seq!-")
                if len(message) >= 2:
                    if message[0] == message[1]:
                        message = message[0]
                    else:
                        message = message[0]
                else:
                    message = message[0]
                message += ("(" + socket_[1][0] + ")\n")
            except OSError:
                self.connect_number -= 1
                print("INFO:recv the wrong message,from" + socket_[1][0])
                print("The wrong message is:", message1[:20] + "..." + message1[-20:])
                self.writer.send(
                    "Method 'recv':wrong message:" + message1[:20] + "..." + message1[-20:] + ", from " + socket_[1][0])
                self.writer.send(socket_[1][0] + "Closed")
                return
            except ConnectionResetError:
                self.connect_number -= 1
                print(socket_[1][0] + "Closed")
                return
            except Exception as error_data:
                print(type(error_data), str(error_data))
                self.connect_number -= 1
                return
            self._lock.acquire()
            self.new_message = deepcopy(message)
            self._lock.release()
            self._file_lock.acquire()
            self.file.write(message)
            self.file.flush()
            self._file_lock.release()

    def processing_connections(self):
        server = s.socket()
        conn_num = int(input("please input max connects(1-999999999, enter for 5):" or "5"))
        t.Thread(target=self.enter_command).start()
        if self.enable_broadcast:
            t.Thread(target=self.radio_broadcast).start()
        t.Thread(target=self.file_send).start()
        if self.enable_transfer:
            t.Thread(target=self.transfer_base).start()
        t.Thread(target=self.transfer).start()
        if self.get_info:
            t.Thread(target=self.transfer_connect).start()
        while True:
            try:
                print("No connection".center(79, "*"))
                server.bind(("0.0.0.0", self.port))
                server.listen(conn_num)
            except OSError:
                self.writer.send("Error in line 298:Port is using")
                print("Error:Port is using")
                input()
                sys.exit()
            except Exception as error_data:
                print(type(error_data), error_data)
            else:
                break

        while True:
            try:
                data_socket = server.accept()
                if data_socket[1][0] in self.baned_ip:
                    self.writer.send("baned IP" + data_socket[1][0] + "try connect to server.")
                    data_socket[0].send(bz2.compress("You Can't join us".encode("utf-32")))
                    data_socket[0].close()
                    self.writer.send("Disconnected baned IP" + data_socket[1][0])
                    del data_socket
                    continue
                if self.connect_number > conn_num:
                    data_socket[0].send(bz2.compress("满员了这位客官。。。。".encode("utf-32")))
                    data_socket[0].close()
                    continue
                self.writer.send("New connect:" + data_socket[1][0] + ",Port" + str(data_socket[1][1]))
                print("INFO:Connect from:" + data_socket[1][0] + ", port:" + str(data_socket[1][1]))
                self.users.append(data_socket[1])
                ran1 = str(random())
                if ran1 not in self.used_name:
                    ran = deepcopy(ran1)
                else:
                    ran = "RENAME FAILED"
                print(1)
                t.Thread(target=self.processing_communication, args=(data_socket, ran)).start()
                print(2)
                t.Thread(target=self.processing_communication2, args=(data_socket,)).start()
                print(3)
            except (TypeError, ValueError):
                self.writer.send("Error in line 355-379:TypeError or ValueError")
                print("please input again")
                continue
            self.users.append(data_socket[1][0])
            print("New connect:", data_socket[1][0])
            print("Connection Number:", self.connect_number // 2)
            t.Thread(target=self.processing_communication, args=(data_socket, ran)).start()
            t.Thread(target=self.processing_communication2, args=(data_socket,)).start()


def main():
    transfer_port = None
    transfer_ip = None
    radio_address = input("Please enter radio broadcast address:")
    sn = input("Please enter the server name:")[:30]
    file_size = int(input("Please input max upload file size(B):"))
    log_file_route = input("Please enter the log file save route:")
    enable_broadcast = eval(input("Enable radio broadcast?True/False:"))
    enable_transfer = eval(input("Share information to other server?True/False:"))
    get_info = eval(input("Get information from other server?True/False:"))
    if enable_transfer:
        port = int(input("Please enter the information share port:"))
        if get_info:
            transfer_port = int(input("Please enter the transfer server port:"))
            transfer_ip = input("Please enter the transfer server IP:")
        base_port = int(input("Enter your base port(file transmission port is base port + 1 eg:base port = 8600, "
                              "file transmission port will be 8601):"))
        server = ChatServer(base_port, radio_address, sn, file_size, log_file_route, enable_transfer=enable_transfer,
                            get_info=get_info, transfer_ip=transfer_ip,
                            transfer_port=transfer_port, share_port=port, enable_broadcast=enable_broadcast)
    else:
        if get_info:
            transfer_port = int(input("Please enter the transfer server port:"))
            transfer_ip = input("Please enter the transfer server IP:")
        server = ChatServer(8505, radio_address, sn, file_size, log_file_route,
                            enable_transfer=enable_transfer, get_info=get_info,
                            transfer_ip=transfer_ip, transfer_port=transfer_port, enable_broadcast=enable_broadcast)

    server.processing_connections()


if __name__ == '__main__':
    main()
