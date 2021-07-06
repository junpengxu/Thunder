# -*- coding: utf-8 -*-
# @Time    : 2021/7/6 8:19 下午
# @Author  : xu.junpeng

import select
import traceback
from socket import *


class Server:
    def __init__(self, host='127.0.0.1', port=8080, nums=16):
        # 创建socket对象
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        # 绑定ip:port
        self.server_socket.bind((host, port))
        # 设置最大监听数
        self.server_socket.listen(nums)
        # 设置ip地址复用
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # 设置非阻塞
        self.server_socket.setblocking(False)
        # 维护连接关系
        self.fd_socket_map = {}
        # 启动epoll模式
        self.epoll = select.epoll()
        # 将自己注册到监听事件中, 个人认为这是在监听自己没有被连接到, 可以把这一行注释掉看一下效果 效果就是不能接受连接了
        # select.EPOLLIN表示监听是否能够读取信息 select.EPOLLET表示边缘触发
        self.epoll.register(self.server_socket.fileno(), select.EPOLLIN | select.EPOLLET)

    def close(self):
        self.server_socket.close()

    def registe_conn(self):
        # 第一次连接，会走到这一行。需要携带自己的信息，才能注册成功
        conn, addr = self.server_socket.accept()  # 获取连接的socket
        self.fd_socket_map[conn.fileno()] = conn
        # 向 epoll 中注册 连接 socket 的 可读 事件
        self.epoll.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)
        print("new conn {}".format(conn.fileno()))

    def receive(self, fd):
        conn = self.fd_socket_map[fd]
        recv_data = conn.recv(1024)
        print("recv data is {}".format(recv_data))
        # 判断是否要断开连接
        if "close" in recv_data.decode():
            self.close_conn(fd)

    def start(self):
        try:
            while True:
                events = self.epoll.poll()
                for fd, event in events:  # 遍历每一个活跃事件
                    # 如果是新的连 表示有客户端连接了服务器套接字
                    if fd == self.server_socket.fileno():
                        self.registe_conn()
                    elif event == select.EPOLLIN:
                        self.receive(fd)
        except Exception as e:
            print(traceback.print_exc())
        finally:
            print("close server")
            self.close()

    def close_conn(self, fd):
        print("close conn")
        self.fd_socket_map[fd].close()
        del self.fd_socket_map[fd]


if __name__ == '__main__':
    s = Server()
    s.start()
