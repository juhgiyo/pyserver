#!/usr/bin/python
'''
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
'''
import asyncore
from threading import *
from inspect import isfunction
from util.singleton import Singleton
from sets import Set
import traceback
import copy
import subprocess
import os


@Singleton
class SubProcController(object):
    def __init__(self):
        self.lock = RLock()
        self.subProcDict = {}

    def killAll(self):
        with self.lock:
            deleteSet = copy.copy(self.subProcDict)
            for key in deleteSet:
                try:
                    self.subProcDict[key].terminate()
                    print key, ' terminating...'
                except Exception as e:
                    print e
                    traceback.print_exc()
            self.subProcDict = {}

    def createSubProcess(self, procName, arg):
        proc = None
        with self.lock:
            if procName in self.subProcDict:
                raise Exception('procName already exists!')
            try:
                def preexec_function():
                    os.setpgrp()

                proc = subprocess.Popen(arg
                                        , preexec_fn=preexec_function
                                        )
                self.subProcDict[procName] = proc
            except Exception as e:
                print e
                traceback.print_exc()
        return proc

    def kill(self, procName):
        print 'subProcController kill called'
        with self.lock:
            try:
                if isinstance(procName, str):
                    if procName in self.subProcDict:
                        self.subProcDict[procName].terminate()
                        del self.subProcDict[procName]
                else:
                    deleteKey = None
                    for key in self.subProcDict:
                        if self.subProcDict[key] == procName:
                            self.subProcDict[key].terminate()
                            deleteKey = key
                            break;
                    if deleteKey is not None:
                        del self.subProcDict[deleteKey]
            except Exception as e:
                print e
                traceback.print_exc()

# foo = SubProcController.Instance()
