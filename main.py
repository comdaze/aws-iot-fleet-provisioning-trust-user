#!/usr/bin/python env
# coding:utf-8
import socket

ip_port = ('0.0.0.0', 8080)
back_log = 10
buffer_size = 1024


def main():
    webserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    webserver.bind(ip_port)
    webserver.listen(back_log)

    while True:
        conn, addr = webserver.accept()
        print(addr)
        recvdata = conn.recv(buffer_size)

        with open("./index.html","rb") as f:
             data = f.read()
             conn.sendall(bytes("HTTP/1.1 201 OK\r\n\r\n", "utf-8"))  
             conn.sendall(data)

        conn.close()


if __name__ == '__main__':
    main()