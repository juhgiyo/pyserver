#!/usr/bin/python
"""
@file async_tcp_client.py
@author Woong Gyu La a.k.a Chris. <juhgiyo@gmail.com>
        <http://github.com/juhgiyo/pyserver>
@date March 10, 2016
@brief AsyncTcpClient Interface
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

AsyncTcpClient Class.
"""
import asyncore
import socket
from collections import deque
import threading

from .async_controller import AsyncController
from .callback_interface import *
from .server_conf import *
# noinspection PyDeprecation
from .preamble import *
import traceback
'''
Interfaces
variables
- hostname
- port
- addr = (hostname,port)
- callback
functions
- def send(data)
- def close() # close the socket
'''


class AsyncTcpClient(asyncore.dispatcher):
    def __init__(self, hostname, port, callback, no_delay=True):
        asyncore.dispatcher.__init__(self)
        self.is_closing = False
        self.callback = None
        if callback is not None and isinstance(callback, ITcpSocketCallback):
            self.callback = callback
        else:
            raise Exception('callback is None or not an instance of ITcpSocketCallback class')
        self.hostname = hostname
        self.port = port
        self.addr = (hostname, port)
        self.send_queue = deque()  # thread-safe dequeue
        self.transport = {'packet': None, 'type': PacketType.SIZE, 'size': SIZE_PACKET_LENGTH, 'offset': 0}

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        if no_delay:
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.set_reuse_addr()
        err = None
        try:
            self.connect((hostname, port))
            AsyncController.instance().add(self)
        except Exception as e:
            err = e
        finally:
            def callback_connection():
                if self.callback is not None:
                    self.callback.on_newconnection(self, err)

            thread = threading.Thread(target=callback_connection)
            thread.start()

    def handle_connect(self):
        pass

    def handle_read(self):
        try:
            data = self.recv(self.transport['size'])
            if data is None or len(data) == 0:
                return
            if self.transport['packet'] is None:
                self.transport['packet'] = data
            else:
                self.transport['packet'] += data
            read_size = len(data)
            if read_size < self.transport['size']:
                self.transport['offset'] += read_size
                self.transport['size'] -= read_size
            else:
                if self.transport['type'] == PacketType.SIZE:
                    should_receive = Preamble.to_should_receive(self.transport['packet'])
                    if should_receive < 0:
                        preamble_offset = Preamble.check_preamble(self.transport['packet'])
                        self.transport['offset'] = len(self.transport['packet']) - preamble_offset
                        self.transport['size'] = preamble_offset
                        # self.transport['packet'] = self.transport['packet'][
                        #                           len(self.transport['packet']) - preamble_offset:]
                        self.transport['packet'] = self.transport['packet'][preamble_offset:]
                        return
                    self.transport = {'packet': None, 'type': PacketType.DATA, 'size': should_receive, 'offset': 0}
                else:
                    receive_packet = self.transport
                    self.transport = {'packet': None, 'type': PacketType.SIZE, 'size': SIZE_PACKET_LENGTH, 'offset': 0}
                    self.callback.on_received(self, receive_packet['packet'])
        except Exception as e:
            print(e)
            traceback.print_exc()

    #def writable(self):
    #    return len(self.send_queue) != 0

    def handle_write(self):
        if len(self.send_queue) != 0:
            send_obj = self.send_queue.popleft()
            state = State.SUCCESS
            try:
                sent = asyncore.dispatcher.send(self, send_obj['data'][send_obj['offset']:])
                if sent < len(send_obj['data']):
                    send_obj['offset'] = send_obj['offset'] + sent
                    self.send_queue.appendleft(send_obj)
                    return
            except Exception as e:
                print(e)
                traceback.print_exc()
                state = State.FAIL_SOCKET_ERROR
            try:
                if self.callback is not None:
                    self.callback.on_sent(self, state, send_obj['data'][SIZE_PACKET_LENGTH:])
            except Exception as e:
                print(e)
                traceback.print_exc()

    def close(self):
        if not self.is_closing:
            self.handle_close()

    def handle_error(self):
        if not self.is_closing:
            self.handle_close()

    def handle_close(self):
        try:
            self.is_closing = True
            asyncore.dispatcher.close(self)
            AsyncController.instance().discard(self)
            if self.callback is not None:
                self.callback.on_disconnect(self)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def send(self, data):
        self.send_queue.append({'data': Preamble.to_preamble_packet(len(data)) + data, 'offset': 0})

    def gethostbyname(self, arg):
        return self.socket.gethostbyname(arg)

    def gethostname(self):
        return self.socket.gethostname()
