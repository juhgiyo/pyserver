#!/usr/bin/python
'''
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
'''
from struct import *

SIZE_PACKET_LENGTH = 16
preambleCode = 0x00F0F0F0F0F0F0F8


class Preamble(object):
    @staticmethod
    def toPreamblePacket(shouldReceive):
        if shouldReceive < 0:
            return None
        byteArr = pack('= Q', preambleCode)
        byteArr += pack('= I', shouldReceive)
        byteArr += pack('= I', 0)
        return byteArr

    @staticmethod
    def toShouldReceive(preamblePacket):
        preamble, shouldRecieve, dummy = unpack('= Q I I', preamblePacket)
        if preamble != preambleCode or shouldRecieve < 0:
            return -1
        return shouldRecieve

    @staticmethod
    def checkPreamble(preamblePacket):
        correctPreamble = pack('= Q', preambleCode)
        prevTrav = 0
        for prevTrav in range(len(preamblePacket)):
            contains = True
            for idx in range(len(correctPreamble)):
                if idx + prevTrav >= len(preamblePacket):
                    break;
                if correctPreamble[idx] != preamblePacket[prevTrav + idx]:
                    contains = False
                    break;
            if contains == True:
                break;
        return prevTrav
