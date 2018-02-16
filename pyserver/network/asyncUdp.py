#!/usr/bin/python
"""
@file asyncUDP.py
@author Woong Gyu La a.k.a Chris. <juhgiyo@gmail.com>
        <http://github.com/juhgiyo/pyserver>
@date March 10, 2016
@brief AsyncUDP Interface
@version 0.1

@section LICENSE

The MIT License (MIT)

Copyright (c) 2016 Woong Gyu La <juhgiyo@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

@section DESCRIPTION

AsyncUDP Class.
"""
try:
    from Queue import Queue
except ImportError:
    from queue import Queue

import asyncore
import socket
import traceback
from .callbackInterface import *
from .serverConf import *
from .asyncController import AsyncController

IP_MTU_DISCOVER = 10
IP_PMTUDISC_DONT = 0  # Never send DF frames.
IP_PMTUDISC_WANT = 1  # Use per route hints.
IP_PMTUDISC_DO = 2  # Always DF.
IP_PMTUDISC_PROBE = 3  # Ignore dst pmtu.

'''
Interfaces
variables
- callback
functions
- def send(host,port,data)
- def close() # close the socket
'''


class AsyncUDP(asyncore.dispatcher):
    def __init__(self, port, callback, bindaddress=''):
        asyncore.dispatcher.__init__(self)
        # self.lock = threading.RLock()
        self.MAX_MTU = 1500
        self.callback = None
        self.port = port
        if callback is not None and isinstance(callback, IUdpCallback):
            self.callback = callback
        else:
            raise Exception('callback is None or not an instance of IUdpCallback class')
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.set_reuse_addr()
            self.bind((bindaddress, port))
        except Exception as e:
            print(e)
            traceback.print_exc()
        self.send_queue = Queue()  # thread-safe queue
        AsyncController.instance().add(self)
        if self.callback is not None:
            self.callback.on_started(self)

    # Even though UDP is connectionless this is called when it binds to a port
    def handle_connect(self):
        pass

    # This is called everytime there is something to read
    def handle_read(self):
        try:
            data, addr = self.recvfrom(self.MAX_MTU)
            if data and self.callback is not None:
                self.callback.on_received(self, addr, data)
        except Exception as e:
            print(e)
            traceback.print_exc()

    #def writable(self):
    #    return not self.send_queue.empty()

    # This is called all the time and causes errors if you leave it out.
    def handle_write(self):
        if not self.send_queue.empty():
            send_obj = self.send_queue.get()
            state = State.SUCCESS
            try:
                sent = self.sendto(send_obj['data'], (send_obj['hostname'], send_obj['port']))
                if sent < len(send_obj['data']):
                    state = State.FAIL_SOCKET_ERROR
            except Exception as e:
                print(e)
                traceback.print_exc()
                state = State.FAIL_SOCKET_ERROR
            try:
                if self.callback is not None:
                    self.callback.on_sent(self, state, send_obj['data'])
            except Exception as e:
                print(e)
                traceback.print_exc()

    def close(self):
        self.handle_close()

    def handle_error(self):
        self.handle_close()

    def handle_close(self):
        print('asyncUdp close called')
        asyncore.dispatcher.close(self)
        AsyncController.instance().discard(self)
        try:
            if self.callback is not None:
                self.callback.on_stopped(self)
        except Exception as e:
            print(e)
            traceback.print_exc()

    # noinspection PyMethodOverriding
    def send(self, hostname, port, data):
        if len(data) <= self.MAX_MTU:
            self.send_queue.put({'hostname': hostname, 'port': port, 'data': data})
        else:
            raise ValueError("The data size is too large")

    def gethostbyname(self, arg):
        return self.socket.gethostbyname(arg)

    def gethostname(self):
        return self.socket.gethostname()

    def get_mtu_size(self):
        return self.MAX_MTU

    def check_mtu_size(self, hostname, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(hostname, port)
        s.setsockopt(socket.IPPROTO_IP, IP_MTU_DISCOVER, IP_PMTUDISC_DO)

        max_mtu = self.MAX_MTU
        try:
            s.send('#' * max_mtu)
        except socket.error:
            option = getattr(socket.IPPROTO_IP, 'IP_MTU', 14)
            max_mtu = s.getsockopt(socket.IPPROTO_IP, option)
        return max_mtu

# Echo udp server test
# def readHandle(sock,addr, data):
#   sock.send(addr[0],addr[1],data)
# server=AsyncUDP(5005,readHandle)
