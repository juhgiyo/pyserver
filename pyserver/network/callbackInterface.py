#!/usr/bin/python
"""
@file callbackInterface.py
@author Woong Gyu La a.k.a Chris. <juhgiyo@gmail.com>
        <http://github.com/juhgiyo/pyserver>
@date March 10, 2016
@brief Callback Interfaces
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

Interfaces for Callback Class.
"""


# UDP related callback object
class IUdpCallback(object):
    def on_started(self, server):
        # raise NotImplementedError("Should have implemented this")
        pass

    def on_stopped(self, server):
        pass

    def on_received(self, server, addr, data):
        pass

    def on_sent(self, server, status, data):
        pass

    # For Multicast Only
    def on_join(self, server, multicast_addr):
        pass

    # For Multicast Only
    def on_leave(self, server, multicast_addr):
        pass


# TCP related callback object
class ITcpSocketCallback(object):
    def on_newconnection(self, sock, err):
        pass

    def on_disconnect(self, sock):
        pass

    def on_received(self, sock, data):
        pass

    def on_sent(self, sock, status, data):
        pass


class ITcpServerCallback(object):
    def on_started(self, server):
        pass

    def on_accepted(self, server, sock):
        pass

    def on_stopped(self, server):
        pass


class IAcceptor(object):
    # requires return True or False
    def on_accept(self, server, addr):
        raise NotImplementedError("Should have implemented this")

    # requires return socket callback object
    def get_socket_callback(self):
        raise NotImplementedError("Should have implemented this")
