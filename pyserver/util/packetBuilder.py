#!/usr/bin/python
'''
@file packetBuilder.py
@author Woong Gyu La a.k.a Chris. <juhgiyo@gmail.com>
        <http://github.com/juhgiyo/pyserver>
@date March 10, 2016
@brief Packet Builder Interface
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

Definitions for Packet Builder Class.
'''

import sys
from struct import *
import inspect
import importlib

'''
format
    None: n
    bool: ?
    int: q
    float: d
    str: s

    list: a
    dict: m
    tuple: u
    class: o (class must be a subclass of Packable class)

NOT SUPPORTED:
    x / p / P
'''


def str_to_class(moduleName, className):
    m = importlib.import_module(moduleName)
    c = getattr(m, className)


class Packable(object):
    '''
    this function must return the packed data of the class
    '''

    def pack(self):
        raise NotImplementedError()

    '''
    data can be longer than it is needed,
    so you must provide way to unpack the data with extra bytes.
    Also this function must return the tuple of object and size, it has used 
    example: return (object,size)
    '''

    def unpack(self, data):
        raise NotImplementedError()


class PacketBuilder(object):
    @staticmethod
    def pack(*arg):
        data = ''
        fmt = pack('= I', len(arg))
        for item in arg:
            if item == None:
                fmt += 'n'
            elif type(item) == bool:
                data += pack('= ?', item)
                fmt += '?'
            elif type(item) == int:
                data += pack('= q', item)
                fmt += 'q'
            elif type(item) == float:
                data += pack('= d', item)
                fmt += 'd'
            elif type(item) == str:
                data += pack('= I %ds' % (len(item),), len(item), item)
                fmt += 's'
            elif type(item) == list:
                fmt += 'a'
                data += PacketBuilder.pack(*item)
            elif type(item) == tuple:
                fmt += 'u'
                data += PacketBuilder.pack(*item)
            elif type(item) == dict:
                fmt += 'm'
                dictList = []
                for key, value in item.iteritems():
                    dictList.append(key)
                    dictList.append(value)
                data += PacketBuilder.pack(*item)
            elif issubclass(type(item), Packable):
                fmt += 'o'
                data += pack('= I %ds I %ds' % (len(item.__module__), len(item.__class__.__name__)),
                             len(item.__module__), item.__module__, len(item.__class__.__name__),
                             item.__class__.__name__)
                data += item.pack()
            else:
                raise Exception('Unpackable object inserted: %s' % (item,))
        return fmt + data

    @staticmethod
    def unpack(data):
        (retTuple, usedSize) = PacketBuilder._unpack(data)
        return retTuple

    @staticmethod
    def _unpack(data):
        usedSize = 0
        (formatLen,), data = unpack('= I', data[:4]), data[4:]
        usedSize += 4
        fmt, data = data[:formatLen], data[formatLen:]
        usedSize += formatLen
        retList = []

        for i in range(formatLen):
            if fmt[i] == 'n':
                retList.append(None)
            elif fmt[i] == '?':
                (retData,), data = unpack('= ?', data[:1]), data[1:]
                usedSize += 1
                retList.append(retData)

            elif fmt[i] == 'q':
                (retData,), data = unpack('= q', data[:8]), data[8:]
                usedSize += 8
                retList.append(retData)

            elif fmt[i] == 'd':
                (retData,), data = unpack('= d', data[:8]), data[8:]
                usedSize += 8
                retList.append(retData)

            elif fmt[i] == 's':
                (strLen,), data = unpack('= I', data[:4]), data[4:]
                usedSize += 4
                retList.append(data[:strLen])
                data = data[strLen:]
                usedSize += strLen

            elif fmt[i] == 'a':
                (retTuple, size) = PacketBuilder._unpack(data)
                usedSize += size
                retList.append(list(retTuple))

            elif fmt[i] == 'u':
                (retTuple, size) = PacketBuilder._unpack(data)
                usedSize += size
                retList.append(retTuple)

            elif fmt[i] == 'm':
                (retTuple, size) = PacketBuilder._unpack(data)
                retList = list(retTuple)
                retMap = {}
                for i in xrange(0, len(retList), 2):
                    retMap[retList[i]] = retList[i + 1]
                usedSize += size
                retList.append(retMap)

            elif fmt[i] == 'o':
                (moduleNameLen,), data = unpack('= I', data[:4]), data[4:]
                usedSize += 4
                moduleName, data = data[:moduleNameLen], data[moduleNameLen:]
                usedSize += moduleNameLen
                (classNameLen,), data = unpack('= I', data[:4]), data[4:]
                usedSize += 4
                className, data = data[:classNameLen], data[classNameLen:]
                usedSize += classNameLen

                m = importlib.import_module(moduleName)
                c = getattr(m, className)

                info = inspect.getargspec(c.__init__)
                args = ()
                for i in range(len(info.args) - 1 - len(info.defaults)):
                    args += (None,)

                (retObject, size) = c(*args).unpack(data)
                data = data[size:]
                usedSize += size
                retList.append(retObject)

            elif fmt[i] == 'c':
                (retData,), data = unpack('= c', data[:1]), data[1:]
                usedSize += 1
                retList.append(retData)
            elif fmt[i] == 'b':
                (retData,), data = unpack('= b', data[:1]), data[1:]
                usedSize += 1
                retList.append(retData)
            elif fmt[i] == 'B':
                (retData,), data = unpack('= B', data[:1]), data[1:]
                usedSize += 1
                retList.append(retData)
            elif fmt[i] == 'h':
                (retData,), data = unpack('= h', data[:2]), data[2:]
                usedSize += 2
                retList.append(retData)
            elif fmt[i] == 'H':
                (retData,), data = unpack('= H', data[:2]), data[2:]
                usedSize += 2
                retList.append(retData)
            elif fmt[i] == 'i':
                (retData,), data = unpack('= i', data[:4]), data[4:]
                usedSize += 4
                retList.append(retData)
            elif fmt[i] == 'I':
                (retData,), data = unpack('= I', data[:4]), data[4:]
                usedSize += 4
                retList.append(retData)
            elif fmt[i] == 'l':
                (retData,), data = unpack('= l', data[:4]), data[4:]
                usedSize += 4
                retList.append(retData)
            elif fmt[i] == 'L':
                (retData,), data = unpack('= L', data[:4]), data[4:]
                usedSize += 4
                retList.append(retData)
            elif fmt[i] == 'Q':
                (retData,), data = unpack('= Q', data[:8]), data[8:]
                usedSize += 8
                retList.append(retData)
            elif fmt[i] == 'f':
                (retData,), data = unpack('= f', data[:4]), data[4:]
                usedSize += 4
                retList.append(retData)
            elif fmt[i] == 'x':
                raise Exception("x is not a supported format")
            elif fmt[i] == 'p':
                raise Exception("p is not a supported format")
            elif fmt[i] == 'P':
                raise Exception("P is not a supported format")
        return (tuple(retList), usedSize)
