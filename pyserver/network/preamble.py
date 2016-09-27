#!/usr/bin/python
"""
@file preamble.py
@author Woong Gyu La a.k.a Chris. <juhgiyo@gmail.com>
        <http://github.com/juhgiyo/pyserver>
@date March 10, 2016
@brief Preamble Interface
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

Preamble Class.
"""
from struct import *

SIZE_PACKET_LENGTH = 16
preambleCode = 0x00F0F0F0F0F0F0F8


class Preamble(object):
    @staticmethod
    def to_preamble_packet(should_receive):
        if should_receive < 0:
            return None
        byte_arr = pack('= Q', preambleCode)
        byte_arr += pack('= I', should_receive)
        byte_arr += pack('= I', 0)
        return byte_arr

    @staticmethod
    def to_should_receive(preamble_packet):
        preamble, should_receive, dummy = unpack('= Q I I', preamble_packet)
        if preamble != preambleCode or should_receive < 0:
            return -1
        return should_receive

    @staticmethod
    def check_preamble(preamble_packet):
        correct_preamble = pack('= Q', preambleCode)
        prev_trav = 0
        for prev_trav in range(len(preamble_packet)):
            contains = True
            for idx in range(len(correct_preamble)):
                if idx + prev_trav >= len(preamble_packet):
                    break
                if correct_preamble[idx] != preamble_packet[prev_trav + idx]:
                    contains = False
                    break
            if contains:
                break
        return prev_trav
