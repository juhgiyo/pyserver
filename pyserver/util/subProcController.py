#!/usr/bin/python
"""
@file subProcController.py
@author Woong Gyu La a.k.a Chris. <juhgiyo@gmail.com>
        <http://github.com/juhgiyo/pyserver>
@date March 10, 2016
@brief SubProcController Interface
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

SubProcController Class.
"""
import threading

from singleton import Singleton
# noinspection PyDeprecation
import traceback
import copy
import subprocess
import os


@Singleton
class SubProcController(object):
    def __init__(self):
        self.lock = threading.RLock()
        self.sub_proc_map = {}

    def kill_all(self):
        with self.lock:
            delete_set = copy.copy(self.sub_proc_map)
            for key in delete_set:
                try:
                    self.sub_proc_map[key].terminate()
                    print key, ' terminating...'
                except Exception as e:
                    print e
                    traceback.print_exc()
            self.sub_proc_map = {}

    def create_subprocess(self, proc_name, arg):
        proc = None
        with self.lock:
            if proc_name in self.sub_proc_map:
                raise Exception('proc_name already exists!')
            try:
                def preexec_function():
                    os.setpgrp()

                proc = subprocess.Popen(arg
                                        , preexec_fn=preexec_function
                                        )
                self.sub_proc_map[proc_name] = proc
            except Exception as e:
                print e
                traceback.print_exc()
        return proc

    def kill(self, proc_name):
        print 'subProcController kill called'
        with self.lock:
            try:
                if isinstance(proc_name, str):
                    if proc_name in self.sub_proc_map:
                        self.sub_proc_map[proc_name].terminate()
                        del self.sub_proc_map[proc_name]
                else:
                    delete_key = None
                    for key in self.sub_proc_map:
                        if self.sub_proc_map[key] == proc_name:
                            self.sub_proc_map[key].terminate()
                            delete_key = key
                            break
                    if delete_key is not None:
                        del self.sub_proc_map[delete_key]
            except Exception as e:
                print e
                traceback.print_exc()

# foo = SubProcController.instance()
