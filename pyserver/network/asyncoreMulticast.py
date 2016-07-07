#!/usr/bin/python
'''
@file asyncoreMulticast.py
@author Woong Gyu La a.k.a Chris. <juhgiyo@gmail.com>
        <http://github.com/juhgiyo/pyserver>
@date March 10, 2016
@brief AsyncoreMulticast Interface
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

AsyncoreMulticast Class.
'''
import asyncore, socket
from threading import *
import sys
import Queue
from asyncoreController import AsyncoreController
from inspect import isfunction
from pyserver.network import *
import traceback
from sets import Set
import copy

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
- def send(multicastAddress,port,data)
- def close() # close the socket
- def join(multicastAddress) # start receiving datagram from given multicast group
- def leave(multicastAddress) # stop receiving datagram from given multicast group
- def getGroupList() # get group list
infos
- multicast address range: 224.0.0.0 - 239.255.255.255
- linux : route add -net 224.0.0.0 netmask 240.0.0.0 dev eth0 
          to enable multicast
'''


class AsyncoreMulticast(asyncore.dispatcher):
    # loop : 1 enable loopback / 0 disable loopback
    # ttl: 0 - restricted to the same host
    #      1 - restricted to the same subnet
    #     32 - restricted to the same site
    #     64 - restricted to the same region
    #    128 - restricted to the same continent
    #    255 - unrestricted in scope
    def __init__(self, port, callbackObj, ttl=1, loop=1, bindAddress=''):
        asyncore.dispatcher.__init__(self)
        # self.lock = threading.RLock()
        self.MAX_MTU = 1500
        self.callbackObj = None
        self.port = port
        self.multicastSet = Set([])
        self.lock = RLock()
        self.ttl = ttl
        self.loop = loop
        if callbackObj is not None and isinstance(callbackObj, IUdpCallback):
            self.callbackObj = callbackObj
        else:
            raise Exception('callbackObj is None or not an instance of IUdpCallback class')
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.set_reuse_addr()
            try:
                socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except AttributeError:
                pass # Some systems don't support SO_REUSEPORT
            
            # for both SENDER and RECEIVER to restrict the region
            self.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)
            # for SENDER to choose whether to use loop back
            self.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, self.loop)

            self.bindAddress=bindAddress
            if self.bindAddress is None or self.bindAddress == '':
                self.bindAddress= socket.gethostbyname(socket.gethostname())
                # for both SENDER and RECEIVER to bind to specific network adapter
            self.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(self.bindAddress))

                # for RECEIVE to receive from multiple multicast groups
            self.bind(('', port))
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

        try:
            deleteSet = self.getGroupList()
            for multicastAddress in deleteSet:
                self.setsockopt(socket.SOL_IP, socket.IP_DROP_MEMBERSHIP,
                                socket.inet_aton(multicastAddress) + socket.inet_aton('0.0.0.0'))
                if self.callbackObj != None:
                    self.callbackObj.onLeave(self,multicastAddress)
            with self.lock:
                self.multicastSet = Set([])
        except Exception as e:
            print e

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

    # for RECEIVER to receive datagram from the multicast group
    def join(self, multicastAddress):
        with self.lock:
            if multicastAddress not in self.multicastSet:
                self.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP,
                                socket.inet_aton(multicastAddress) + socket.inet_aton(self.bindAddress))
                self.multicastSet.add(multicastAddress)
                if self.callbackObj != None:
                    self.callbackObj.onJoin(self,multicastAddress)

    # for RECEIVER to stop receiving datagram from the multicast group
    def leave(self, multicastAddress):
        with self.lock:
            try:
                if multicastAddress in self.multicastSet:
                    self.setsockopt(socket.SOL_IP, socket.IP_DROP_MEMBERSHIP,
                                    socket.inet_aton(multicastAddress) + socket.inet_aton('0.0.0.0'))
                    self.multicastSet.discard(multicastAddress)
                    if self.callbackObj != None:
                        self.callbackObj.onLeave(self,multicastAddress)
            except Exception as e:
                print e

    def getGroupList(self):
        with self.lock:
            return copy.copy(self.multicastSet)

    def gethostbyname(self, arg):
        return self.socket.gethostbyname(arg)

    def gethostname():
        return self.socket.gethostname()

# Echo udp server test
# def readHandle(sock,addr, data):
#   sock.send(addr[0],addr[1],data)
# server=AsyncoreUDP(5005,readHandle)
