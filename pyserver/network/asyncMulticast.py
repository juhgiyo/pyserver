#!/usr/bin/python
"""
@file asyncMulticast.py
@author Woong Gyu La a.k.a Chris. <juhgiyo@gmail.com>
        <http://github.com/juhgiyo/pyserver>
@date March 10, 2016
@brief AsyncMulticast Interface
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

AsyncMulticast Class.
"""

try:
    from Queue import Queue
except ImportError:
    from queue import Queue

import asyncore
import socket
import traceback
import threading

from .serverConf import *
from .callbackInterface import *
from .asyncController import AsyncController
# noinspection PyDeprecation

try:
    set
except NameError:
    from sets import Set as set

import copy

IP_MTU_DISCOVER = 10
IP_PMTUDISC_DONT = 0  # Never send DF frames.
IP_PMTUDISC_WANT = 1  # Use per route hints.
IP_PMTUDISC_DO = 2  # Always DF.
IP_PMTUDISC_PROBE = 3  # Ignore dst pmtu.

'''
Interfaces
variables
- callback_obj
functions
- def send(multicast_addr,port,data)
- def close() # close the socket
- def join(multicast_addr) # start receiving datagram from given multicast group
- def leave(multicast_addr) # stop receiving datagram from given multicast group
- def getgrouplist() # get group list
infos
- multicast address range: 224.0.0.0 - 239.255.255.255
- linux : route add -net 224.0.0.0 netmask 240.0.0.0 dev eth0
          to enable multicast
'''


class AsyncMulticast(asyncore.dispatcher):
    # enable_loopback : 1 enable loopback / 0 disable loopback
    # ttl: 0 - restricted to the same host
    #      1 - restricted to the same subnet
    #     32 - restricted to the same site
    #     64 - restricted to the same region
    #    128 - restricted to the same continent
    #    255 - unrestricted in scope
    def __init__(self, port, callback_obj, ttl=1, enable_loopback=False, bind_addr=''):
        asyncore.dispatcher.__init__(self)
        # self.lock = threading.RLock()
        self.MAX_MTU = 1500
        self.callback_obj = None
        self.port = port
        self.multicastSet = set([])
        self.lock = threading.RLock()
        self.ttl = ttl
        self.enable_loopback = enable_loopback
        if callback_obj is not None and isinstance(callback_obj, IUdpCallback):
            self.callback_obj = callback_obj
        else:
            raise Exception('callback_obj is None or not an instance of IUdpCallback class')
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.set_reuse_addr()
            try:
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except AttributeError:
                pass  # Some systems don't support SO_REUSEPORT

            # for both SENDER and RECEIVER to restrict the region
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)
            # for SENDER to choose whether to use loop back
            if self.enable_loopback:
                self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
            else:
                self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)

            self.bind_addr = bind_addr
            if self.bind_addr is None or self.bind_addr == '':
                self.bind_addr = socket.gethostbyname(socket.gethostname())
                # for both SENDER and RECEIVER to bind to specific network adapter
            self.socket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(self.bind_addr))

            # for RECEIVE to receive from multiple multicast groups
            self.bind(('', port))
        except Exception as e:
            print(e)
            traceback.print_exc()
        self.sendQueue = Queue()  # thread-safe queue
        AsyncController.instance().add(self)
        if self.callback_obj is not None:
            self.callback_obj.on_started(self)

    # Even though UDP is connectionless this is called when it binds to a port
    def handle_connect(self):
        pass

    # This is called everytime there is something to read
    def handle_read(self):
        try:
            data, addr = self.recvfrom(self.MAX_MTU)
            if data and self.callback_obj is not None:
                self.callback_obj.on_received(self, addr, data)
        except Exception as e:
            print(e)
            traceback.print_exc()

    #def writable(self):
    #    return not self.sendQueue.empty()

    # This is called all the time and causes errors if you leave it out.
    def handle_write(self):
        if not self.sendQueue.empty():
            send_obj = self.sendQueue.get()
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
                if self.callback_obj is not None:
                    self.callback_obj.on_sent(self, state, send_obj['data'])
            except Exception as e:
                print(e)
                traceback.print_exc()

    def close(self):
        self.handle_close()

    def handle_error(self):
        self.handle_close()

    def handle_close(self):

        try:
            delete_set = self.getgrouplist()
            for multicast_addr in delete_set:
                self.socket.setsockopt(socket.SOL_IP, socket.IP_DROP_MEMBERSHIP,
                                socket.inet_aton(multicast_addr) + socket.inet_aton('0.0.0.0'))
                if self.callback_obj is not None:
                    self.callback_obj.on_leave(self, multicast_addr)
            with self.lock:
                self.multicastSet = set([])
        except Exception as e:
            print(e)

        print('asyncUdp close called')
        asyncore.dispatcher.close(self)
        AsyncController.instance().discard(self)
        try:
            if self.callback_obj is not None:
                self.callback_obj.on_stopped(self)
        except Exception as e:
            print(e)
            traceback.print_exc()

    # noinspection PyMethodOverriding
    def send(self, hostname, port, data):
        if len(data) <= self.MAX_MTU:
            self.sendQueue.put({'hostname': hostname, 'port': port, 'data': data})
        else:
            raise ValueError("The data size is too large")

    # for RECEIVER to receive datagram from the multicast group
    def join(self, multicast_addr):
        with self.lock:
            if multicast_addr not in self.multicastSet:
                self.socket.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP,
                                socket.inet_aton(multicast_addr) + socket.inet_aton(self.bind_addr))
                self.multicastSet.add(multicast_addr)
                if self.callback_obj is not None:
                    self.callback_obj.on_join(self, multicast_addr)

    # for RECEIVER to stop receiving datagram from the multicast group
    def leave(self, multicast_addr):
        with self.lock:
            try:
                if multicast_addr in self.multicastSet:
                    self.socket.setsockopt(socket.SOL_IP, socket.IP_DROP_MEMBERSHIP,
                                    socket.inet_aton(multicast_addr) + socket.inet_aton('0.0.0.0'))
                    self.multicastSet.discard(multicast_addr)
                    if self.callback_obj is not None:
                        self.callback_obj.on_leave(self, multicast_addr)
            except Exception as e:
                print(e)

    def getgrouplist(self):
        with self.lock:
            return copy.copy(self.multicastSet)

    def gethostbyname(self, arg):
        return self.socket.gethostbyname(arg)

    def gethostname(self):
        return self.socket.gethostname()

# Echo udp server test
# def readHandle(sock,addr, data):
#   sock.send(addr[0],addr[1],data)
# server=AsyncUDP(5005,readHandle)
