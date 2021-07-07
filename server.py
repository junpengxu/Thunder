# -*- coding: utf-8 -*-
# @Time    : 2021/7/6 8:19 下午
# @Author  : xu.junpeng

import select
import traceback
from socket import *
import json


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
        # 启动epoll模式
        self.epoll = select.epoll()
        # 将自己注册到监听事件中, 个人认为这是在监听自己没有被连接到, 可以把这一行注释掉看一下效果 效果就是不能接受连接了
        # select.EPOLLIN表示监听是否能够读取信息 select.EPOLLET表示边缘触发
        self.epoll.register(self.server_socket.fileno(), select.EPOLLIN | select.EPOLLET)
        # 维护连接关系
        self.fd_socket_map = {}
        # 维护用户关系
        self.user_fd_map = {}

    def close(self):
        self.server_socket.close()

    def close_conn(self, fd):
        print("close conn")
        self.fd_socket_map[fd].close()
        self.response(fd, "close connect")
        del self.fd_socket_map[fd]

    def registe_conn(self):
        # 第一次连接，会走到这一行。需要携带自己的信息，才能注册成功
        conn, addr = self.server_socket.accept()  # 获取连接的socket
        self.fd_socket_map[conn.fileno()] = conn
        # 向 epoll 中注册 连接 socket 的 可读 事件
        self.epoll.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)
        print("new conn {}".format(conn.fileno()))

    def receive(self, fd):
        conn = self.fd_socket_map[fd]
        # 先约定最长的数据为1024个长度
        recv_data = conn.recv(1024)
        print("recv data is {}".format(recv_data))
        return recv_data

    def response(self, fd, msg):
        conn = self.fd_socket_map[fd]
        conn.sendall(msg.encode("utf-8"))

    def analyse_msg(self, data):
        try:
            data = json.loads(data.decode(encoding="utf-8"))
            user_id = data["user_id"]
            target_id = data["target_id"]
            msg = data["msg"]
            return user_id, target_id, msg
        except Exception as e:
            raise Exception(e)

    def handle(self, fd, msg):
        try:
            user_id, target_id, msg = self.analyse_msg(msg)
        except Exception as e:
            return self.response(fd, "数据解析失败")
            # self.close_conn(fd)
        # 判断用户的绑定关系, 这里不应该每次都判断
        self.user_fd_map[user_id] = fd
        # 进行消息转发
        target_fd = self.user_fd_map.get(target_id)
        if not target_fd:
            return self.response(fd, "对话用户未层连接")
        # 组装消息
        data = {"uesr_id": user_id, "msg": msg}
        # 发送消息
        self.response(target_fd, json.dumps(data))

    def start(self):
        try:
            while True:
                print("user_fd: {}".format(self.user_fd_map))
                print("fd_conn: {}".format(self.fd_socket_map))
                events = self.epoll.poll()
                for fd, event in events:  # 遍历每一个活跃事件
                    # 如果是新的连 表示有客户端连接了服务器套接字
                    if fd == self.server_socket.fileno():
                        self.registe_conn()
                    elif event == select.EPOLLIN:
                        msg = self.receive(fd)
                        if not msg:
                            self.close_conn(fd)
                        else:
                            self.handle(fd, msg)

        except Exception as e:
            print(traceback.print_exc())
        finally:
            print("close server")
            self.close()


if __name__ == '__main__':
    s = Server()
    s.start()
