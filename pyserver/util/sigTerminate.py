#!/usr/bin/python
'''
@file sigTerminate.py
@author Woong Gyu La a.k.a Chris. <juhgiyo@gmail.com>
		<http://github.com/juhgiyo/pyserver>
@date March 10, 2016
@brief SIGINT Terminate Interface
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

call setSigTerminate() to terminate the python with Ctrl+C
'''
import signal
import sys
import os
from threading import *
from pyserver.network.asyncoreController import AsyncoreController
import subprocess
import traceback
from subProcController import *


def setSigTerminate(signalEvent=None, shouldAbort=False):
    # Setting console ctrl+c exit
    def handler(signum, frame):
        print 'Ctrl+C detected!'
        AsyncoreController.Instance().stop()
        AsyncoreController.Instance().join()
        SubProcController.Instance().killAll()
        
        if signalEvent is not None:
            print 'You pressed Ctrl+C! Signaling event...'
            signalEvent.set()
        if shouldAbort:
            print 'You pressed Ctrl+C! Exiting...'
            os._exit(1)

    signal.signal(signal.SIGINT, handler)
