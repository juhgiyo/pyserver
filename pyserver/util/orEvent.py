#!/usr/bin/python
'''
@file orEvent.py
@author Woong Gyu La a.k.a Chris. <juhgiyo@gmail.com>
        <http://github.com/juhgiyo/pyserver>
@date March 10, 2016
@brief OrEvent Interface
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

Multiple Event Wait OrEvent Class.
'''
import threading
import traceback

def orSubEvent_set(self):
    self._set()
    callbacks = []
    with self.lock:
        callbacks=self.changed
    for callback in callbacks:
        try:
            callback()
        except Exception as e:
            print e
            traceback.print_exc()

def orSubEvent_clear(self):
    self._clear()
    callbacks = []
    with self.lock:
        callbacks=self.changed
    for callback in callbacks:
        try:
            callback()
        except Exception as e:
            print e
            traceback.print_exc()

def orSubEvent_remove(self,changed_callback):
    with self.lock:
        self.changed.remove(changed_callback)

def orify(e, changed_callback):
    if not hasattr(e, '_set'):
        e._set = e.set
        e._clear = e.clear
        e.set = lambda: orSubEvent_set(e)
        e.clear = lambda: orSubEvent_clear(e)
        e.remove = lambda changed: orSubEvent_remove(e,changed)
        e.lock = threading.RLock()
        with e.lock:
            e.changed=[]
    with e.lock:
        e.changed.append(changed_callback)

def or_close(self,changed_callback):
    for e in self.events:
        e.changed.remove(changed_callback)

def or_exit(self, exc_type, exc_value, traceback):
    self.close()

def or_del(self):
    self.close()


def OrEvent(*events):
    or_event = threading.Event()
    or_event.events=events
    

    def changed():
        bools = [e.is_set() for e in events]
        if any(bools):
            or_event.set()
        else:
            or_event.clear()

    or_event.close=lambda: or_close(or_event,changed)
    or_event.__exit__=lambda exc_type,exc_value,traceback: or_exit(or_event,exc_type,exc_value,traceback)
    or_event.__del__ = lambda : or_del(or_event)
    for e in events:
        orify(e, changed)
    changed()
    return or_event
