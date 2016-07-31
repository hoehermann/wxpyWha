#!/usr/bin/python
# -*- coding: utf-8 -*-

"""@package docstring
Yowsup connector for wxpyWha (a simple wxWidgets GUI wrapper atop yowsup).

Uses WhaLayer to build the Yowsup stack.

This is based on code from the yowsup echo example, the yowsup cli and pywhatsapp.
"""

# from echo stack
from yowsup.stacks import YowStackBuilder
from yowsup.layers.auth import AuthError
from yowsup.layers.network import YowNetworkLayer

# from cli stack
from yowsup.layers.axolotl.props import PROP_IDENTITY_AUTOTRUST
import sys

# from cli layer
from yowsup.layers import YowLayerEvent

# from http://stackoverflow.com/questions/3702675/how-to-print-the-full-traceback-without-halting-the-program
import traceback

# from https://github.com/tgalal/yowsup/issues/1069
import logging 

from whalayer import WhaLayer

class WhaClient(object):
    def __init__(self, credentials, encryptionEnabled = True):
        stackBuilder = YowStackBuilder()
        self.stack = stackBuilder\
            .pushDefaultLayers(encryptionEnabled)\
            .push(WhaLayer)\
            .build()
        self.stack.setCredentials(credentials)
        self.stack.setProp(PROP_IDENTITY_AUTOTRUST, True)
        
    def setYowsupEventHandler(self, handler):
        interface = self.stack.getLayerInterface(WhaLayer)
        interface.enventHandler = handler

    def sendMessage(self, outgoingMessage):
        interface = self.stack.getLayerInterface(WhaLayer)
        interface.sendMessage(outgoingMessage)
        
    def start(self):
        logging.basicConfig(level=logging.WARNING)
        self.stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))
        try:
            self.stack.loop()
        except AuthError as e:
            sys.stderr.write("Authentication Error: %s\n"%e.message)
        except KeyboardInterrupt:
            # This is only relevant if this is the main module
            # TODO: disconnect cleanly
            print("\nExit")
            sys.exit(0)
        except: # catch *all* exceptions
            sys.stderr.write("Unhandled exception.\n")
            traceback.print_exc()

if __name__ == "__main__":
    client = WhaClient(("login","base64passwd"))
    client.start()
