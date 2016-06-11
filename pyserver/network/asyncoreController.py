#!/usr/bin/python
'''
@file asyncoreController.py
@author Woong Gyu La a.k.a Chris. <juhgiyo@gmail.com>
		<http://github.com/juhgiyo/pyserver>
@date March 10, 2016
@brief AsyncoreController Interface
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

AsyncoreController Class.
'''
import asyncore
from threading import *
from inspect import isfunction
from pyserver.util.singleton import Singleton
from sets import Set
import traceback
import copy


@Singleton
class AsyncoreController(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.shouldStopEvent = Event()
        self.hasModuleEvent = Event()
        self.lock = RLock()
        self.moduleSet = Set([])
        self.timeout=0.1

        # Self start the thread
        self.start()

    def run(self):
        while not self.shouldStopEvent.is_set():
            try:
                asyncore.loop(timeout=self.timeout)
            except Exception as e:
                print e
                traceback.print_exc()
            self.hasModuleEvent.wait()
        self.hasModuleEvent.clear()
        print 'asyncore Thread exiting...'

    def stop(self):
        with self.lock:
            deleteSet = copy.copy(self.moduleSet)
            for item in deleteSet:
                try:
                    item.close()
                except Exception as e:
                    print e
                    traceback.print_exc()
            self.moduleSet = Set([])
        self.shouldStopEvent.set();
        self.hasModuleEvent.set();

    def add(self, module):
        with self.lock:
            self.moduleSet.add(module)
        self.hasModuleEvent.set();

    def clear(self):
        with self.lock:
            deleteSet = copy.copy(self.moduleSet)
            for item in deleteSet:
                try:
                    item.close()
                except Exception as e:
                    print e
                    traceback.print_exc()
            self.moduleSet = Set([])
        self.hasModuleEvent.clear()

    def discard(self, module):
        print 'asyncoreController discard called'
        with self.lock:
            self.moduleSet.discard(module)
            if len(self.moduleSet) == 0:
                self.hasModuleEvent.clear()

# foo = AsyncoreController.Instance()
