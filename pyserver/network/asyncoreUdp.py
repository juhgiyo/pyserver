#!/usr/bin/python
'''
@file asyncoreUDP.py
@author Woong Gyu La a.k.a Chris. <juhgiyo@gmail.com>
		<http://github.com/juhgiyo/pyserver>
@date March 10, 2016
@brief AsyncoreUDP Interface
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

AsyncoreUDP Class.
'''
import asyncore, socket, threading
import sys
import Queue
from asyncoreController import AsyncoreController
from inspect import isfunction
from network import *
import traceback

IP_MTU_DISCOVER = 10
IP_PMTUDISC_DONT = 0  # Never send DF frames.
IP_PMTUDISC_WANT = 1  # Use per route hints.
IP_PMTUDISC_DO = 2  # Always DF.
IP_PMTUDISC_PROBE = 3  # Ignore dst pmtu.

'''
Interfaces
variables
- callbackObj
functions
- def send(host,port,data)
- def close() # close the socket
'''

class AsyncoreUDP(asyncore.dispatcher):
    def __init__(self, port, callbackObj, bindaddress=''):
        asyncore.dispatcher.__init__(self)
        # self.lock = threading.RLock()
        self.MAX_MTU = 1500
        self.callbackObj = None
        self.port = port
        if callbackObj is not None and isinstance(callbackObj, IUdpCallback):
            self.callbackObj = callbackObj
        else:
            raise Exception('callbackObj is None or not an instance of IUdpCallback class')
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.set_reuse_addr()
            self.bind((bindaddress, port))
        except Exception as e:
            print e
            traceback.print_exc()
        self.sendQueue = Queue.Queue()  # thread-safe queue
        AsyncoreController.Instance().add(self)
        if self.callbackObj != None:
            self.callbackObj.onStarted(self)

    # Even though UDP is connectionless this is called when it binds to a port
    def handle_connect(self):
        pass

    # This is called everytime there is something to read
    def handle_read(self):
        try:
            data, addr = self.recvfrom(self.MAX_MTU)
            if data and self.callbackObj != None:
                self.callbackObj.onReceived(self, addr, data)
        except Exception as e:
            print e
            traceback.print_exc()

    def writable(self):
        return not self.sendQueue.empty()

    # This is called all the time and causes errors if you leave it out.
    def handle_write(self):
        if not self.sendQueue.empty():
            sendObj = self.sendQueue.get()
            state = State.SUCCESS
            try:
                sent = self.sendto(sendObj['data'], (sendObj['hostname'], sendObj['port']))
                if sent < len(sendObj['data']):
                    state = State.FAIL_SOCKET_ERROR
            except Exception as e:
                print e
                traceback.print_exc()
                state = State.FAIL_SOCKET_ERROR
            try:
                if self.callbackObj != None:
                    self.callbackObj.onSent(self, state, sendObj['data'])
            except Exception as e:
                print e
                traceback.print_exc()

    def close(self):
        self.handle_close()

    def handle_error(self):
        self.handle_close()

    def handle_close(self):
        print 'asyncoreUdp close called'
        asyncore.dispatcher.close(self)
        AsyncoreController.Instance().discard(self)
        try:
            if self.callbackObj != None:
                self.callbackObj.onStopped(self)
        except Exception as e:
            print e
            traceback.print_exc()

    def send(self, hostname, port, data):
        if len(data) <= self.MAX_MTU:
            self.sendQueue.put({'hostname': hostname, 'port': port, 'data': data})
        else:
            raise ValueError("The data size is too large")

    def gethostbyname(self, arg):
        return self.socket.gethostbyname(arg)

    def gethostname():
        return self.socket.gethostname()

    def getMTUSize(self):
        return self.MAX_MTU

    def checkMTUSize(self, hostname, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(hostname, port)
        s.setsockopt(socket.IPPROTO_IP, IP_MTU_DISCOVER, IP_PMTUDISC_DO)

        maxMTU = self.MAX_MTU
        try:
            s.send('#' * maxMTU)
        except socket.error:
            option = getattr(socket.IPPROTO_IP, 'IP_MTU', 14)
            maxMTU = s.getsockopt(socket.IPPROTO_IP, option)
        return maxMTU

# Echo udp server test
# def readHandle(sock,addr, data):
#   sock.send(addr[0],addr[1],data)
# server=AsyncoreUDP(5005,readHandle)
