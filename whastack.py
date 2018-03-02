#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""@package docstring
Yowsup connector for wxpyWha (a simple wxWidgets GUI wrapper atop yowsup).

Uses WhaLayer to build the Yowsup stack.

This is based on code from the yowsup echo example, the yowsup cli and pywhatsapp.
"""

SECONDS_RECONNECT_DELAY = 10

import sys

# from echo stack
from yowsup.stacks import YowStackBuilder
from yowsup.layers.auth import AuthError
from yowsup.layers.network import YowNetworkLayer

# from cli stack
try:
    from yowsup.layers.axolotl.props import PROP_IDENTITY_AUTOTRUST #tgalal
except ImportError as ie:
    sys.stderr.write("WARNING: PROP_IDENTITY_AUTOTRUST could not be imported from yowsup.layers.axolotl.props. Using hardcoded value instead.\n")
    PROP_IDENTITY_AUTOTRUST = "org.openwhatsapp.yowsup.prop.axolotl.INDENTITY_AUTOTRUST" #as done by jlguardi

# from cli layer
from yowsup.layers import YowLayerEvent

# from http://stackoverflow.com/questions/3702675/how-to-print-the-full-traceback-without-halting-the-program
import traceback

# from https://github.com/tgalal/yowsup/issues/1069
import logging 

import queue

from whalayer import WhaLayer

class WhaClient(object):
    def __init__(self, credentials, encryptionEnabled = True):
        stackBuilder = YowStackBuilder()
        self.stack = stackBuilder\
            .pushDefaultLayers(encryptionEnabled)\
            .push(WhaLayer)\
            .build()
        self.stack.setCredentials(credentials)
        self.stack.setProp(PROP_IDENTITY_AUTOTRUST, True) #not in jlguardi
        self.wantReconnect = True
        self.abortReconnectWait = queue.Queue()
        
    def setYowsupEventHandler(self, handler):
        interface = self.stack.getLayerInterface(WhaLayer)
        interface.enventHandler = handler

    def sendMessage(self, outgoingMessage):
        interface = self.stack.getLayerInterface(WhaLayer)
        interface.sendMessage(outgoingMessage)
        
    def disconnect(self):
        interface = self.stack.getLayerInterface(WhaLayer)
        interface.disconnect()
        
    def start(self):
        logging.basicConfig(level=logging.WARNING)
        while (self.wantReconnect):
            self.stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))
            try:
                self.stack.loop()
            except AuthError as e:
                sys.stderr.write("Authentication Error\n")
            except KeyboardInterrupt:
                # This is only relevant if this is the main module
                # TODO: disconnect cleanly
                print("\nExit")
                sys.exit(0)
            except: # catch *all* exceptions
                sys.stderr.write("Unhandled exception.\n")
                traceback.print_exc()
            # TODO: regard connection state in the GUI
            sys.stderr.write("Yowsup WhaClient exited.\nYOU ARE NOW DISCONNECTED.\n") 
            if (self.wantReconnect):
                sys.stderr.write("Auto-reconnect enabled. Waiting up to %d seconds before reconnecting...\n"%(SECONDS_RECONNECT_DELAY))
                try:
                    self.abortReconnectWait.get(timeout=SECONDS_RECONNECT_DELAY)
                except queue.Empty:
                    pass

    def setEnableReconnect(self, b = True):
        self.wantReconnect = b
        self.abortReconnectWait.put(b)

if __name__ == "__main__":
    client = WhaClient(("login","base64passwd"))
    client.start()
