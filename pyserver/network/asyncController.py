#!/usr/bin/python
"""
@file asyncController.py
@author Woong Gyu La a.k.a Chris. <juhgiyo@gmail.com>
        <http://github.com/juhgiyo/pyserver>
@date March 10, 2016
@brief AsyncController Interface
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

AsyncController Class.
"""
import asyncore
import threading

from pyserver.util.singleton import Singleton
# noinspection PyDeprecation
try:
    set
except:
    from sets import Set as set

import traceback
import copy


@Singleton
class AsyncController(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.should_stop_event = threading.Event()
        self.has_module_event = threading.Event()
        self.lock = threading.RLock()
        self.module_set = set([])
        self.timeout = 0.01

        # Self start the thread
        self.start()

    def run(self):
        while not self.should_stop_event.is_set():
            try:
                asyncore.loop(timeout=self.timeout)
                #asyncore.loop()
            except Exception as e:
                print(e)
                traceback.print_exc()
            self.has_module_event.wait()
        self.has_module_event.clear()
        print('async Thread exiting...')

    def stop(self):
        with self.lock:
            delete_set = copy.copy(self.module_set)
            for item in delete_set:
                try:
                    item.close()
                except Exception as e:
                    print(e)
                    traceback.print_exc()
            self.module_set = set([])
        self.should_stop_event.set()
        self.has_module_event.set()

    def add(self, module):
        with self.lock:
            self.module_set.add(module)
        self.has_module_event.set()

    def clear(self):
        with self.lock:
            delete_set = copy.copy(self.module_set)
            for item in delete_set:
                try:
                    item.close()
                except Exception as e:
                    print(e)
                    traceback.print_exc()
            self.module_set = set([])
        if not self.should_stop_event.is_set():
            self.has_module_event.clear()

    def discard(self, module):
        print('asyncController discard called')
        with self.lock:
            self.module_set.discard(module)
            if len(self.module_set) == 0 and not self.should_stop_event.is_set():
                self.has_module_event.clear()

# foo = AsyncController.instance()
