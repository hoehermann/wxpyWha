#!/usr/bin/python
# -*- coding: utf-8 -*-

# from echo stack
from yowsup.stacks import  YowStackBuilder
from yowsup.layers.auth import AuthError
from yowsup.layers.network import YowNetworkLayer

# from echo layer
from yowsup.layers.interface import YowInterfaceLayer, ProtocolEntityCallback

# from cli stack
from yowsup.layers.axolotl.props import PROP_IDENTITY_AUTOTRUST
import sys

# from cli layer
from yowsup.layers import YowLayerEvent, EventCallback

# from pywhatsapp
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity

# from https://github.com/tgalal/yowsup/issues/1069
import logging 
logging.basicConfig(level=logging.WARNING)

class WhaLayerInterface():
     def __init__(self):
         self.eventTarget = None
         self.sendMessage = None

class WhaLayer(YowInterfaceLayer):
    
    def __init__(self):
        super(WhaLayer, self).__init__()
        YowInterfaceLayer.__init__(self)
        self.interface = WhaLayerInterface() # TODO: I have no idea if this is the correct way of using the interface attribute
        self.interface.sendMessage = self.sendMessage # TODO: I have no idea if this can be called in out-of-thread context
        self.connected = False
    
    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):
        sys.stderr.write("Received a message from %s of type %s\n"%(messageProtocolEntity.getFrom(),messageProtocolEntity.getType()))
        self.toLower(messageProtocolEntity.ack(True)) # taken from yowsup cli (marks message as read, axolotl will do so anyways)
        '''
        # this is from echoclient
        self.toLower(messageProtocolEntity.forward(messageProtocolEntity.getFrom()))
        self.toLower(messageProtocolEntity.ack())
        self.toLower(messageProtocolEntity.ack(True))
        '''
        if self.interface.eventTarget:
            self.interface.eventTarget.onIncomingMessage(messageProtocolEntity)

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        sys.stderr.write("Received a receipt, sending ack.\n")
        self.toLower(entity.ack())

    @EventCallback(YowNetworkLayer.EVENT_STATE_DISCONNECTED)
    def onStateDisconnected(self,layerEvent):
        self.connected = False
        sys.stderr.write("Disconnected. Reason: %s\n" % layerEvent.getArg("reason"))
        
    @ProtocolEntityCallback("success")
    def onSuccess(self, entity):
        self.connected = True
        sys.stderr.write("Success: Logged in.\n")
        
        if False:
            sys.stderr.write("Generating a local message for debbugging the GUI...\n")
            tmpe = TextMessageProtocolEntity("locally generated test message", _from="DEBUG@s.whatsapp.net")
            self.interface.eventTarget.onIncomingMessage(tmpe)

    @ProtocolEntityCallback("failure")
    def onFailure(self, entity):
        sys.stderr.write("Login Failed. Reason: %s\n" % entity.getReason())
        
    def sendMessage(self, jid, content):
        sys.stderr.write("WhaLayer.sendMessage\n")
        if not self.connected:
            sys.stderr.write("Cannot send message. Not connected.\n")
        else:
            outgoingMessage = TextMessageProtocolEntity(content, to = jid)
            self.toLower(outgoingMessage)

# TODO: move this into separate file
class WhaClient(object):
    def __init__(self, credentials, encryptionEnabled = True):
        stackBuilder = YowStackBuilder()
        self.stack = stackBuilder\
            .pushDefaultLayers(encryptionEnabled)\
            .push(WhaLayer)\
            .build()
        self.stack.setCredentials(credentials)
        self.stack.setProp(PROP_IDENTITY_AUTOTRUST, True)
        
    def setIncomingMessageHandler(self, eventTarget):
        interface = self.stack.getLayerInterface(WhaLayer)
        interface.eventTarget = eventTarget

    def sendMessage(self, jid, content):
        sys.stderr.write("WhaClient.sendMessage\n")
        interface = self.stack.getLayerInterface(WhaLayer)
        interface.sendMessage(jid, content)
        
    def start(self):
        self.stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))
        try:
            self.stack.loop()
        except AuthError as e:
            print("Authentication Error: %s" % e.message)
        except KeyboardInterrupt:
            # This is only relevant if this is the main module
            # TODO: disconnect cleanly
            print("\nExit")
            sys.exit(0)
        except: # catch *all* exceptions
            e = sys.exc_info()[0]
            sys.stderr.write("Unhandled exception: %s"%(e))

if __name__ == "__main__":
    client = WhaClient(("login","base64passwd"))
    client.start()
