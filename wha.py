#!/usr/bin/python
# -*- coding: utf-8 -*-

"""@package docstring
Main module for wxpyWha. A simple wxWidgets GUI wrapper atop yowsup.
"""

import wx
import wxWha
import threading
from whalayer import WhaClient
import sys
import pickle
import datetime

# from pywhatsapp
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity

"""If true, locally generates a message to handle in the GUI."""
DEBUG_GENERATE_MESSAGE = False

"""If true, don't actually connect to whatsapp (local testing only)."""
DEBUG_PASSIVE = False

IncomingMessageDataEventType = wx.NewEventType()
INCOMING_MESSAGE_DATA_EVENT = wx.PyEventBinder(IncomingMessageDataEventType, 1)
class IncomingMessageDataEvent(wx.PyCommandEvent):
    """Custom event type for receiving messages."""
    def __init__(self, etype, eid, messageProtocolEntity):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self.messageProtocolEntity = messageProtocolEntity

class IncomingMessageHandler():
    """Handler for incoming messages."""
    def __init__(self, gui):
        self.gui = gui
    def onIncomingMessage(self, messageProtocolEntity):
        """
        This is called from outside the wxApp context.
        Generates a wxEvent and posts it to the wxApp main loop.
        """
        evt = IncomingMessageDataEvent(IncomingMessageDataEventType, -1, messageProtocolEntity)
        wx.PostEvent(self.gui, evt)

class ConversationFrame ( wxWha.ConversationFrame ):
    def __init__(self, parent, client, jid):
        wxWha.ConversationFrame.__init__(self, parent)
        self.client = client
        # TODO: do not abuse title as field for jid
        self.SetTitle(jid)
        
    def append(self, message):
        jid = message.getFrom()
        if jid is None:
            jid = message.getTo()
            sender = "SELF@s.whatsapp.net" # TODO: move to constant
        else:
            if message.isGroupMessage():
                sender = message.getParticipant()
            else:
                sender = jid
        t = message.getType()
        if t == "text":
            line = message.getBody()
        else:
            line = "Message is of unhandled type %s."%(t)
        formattedDate = datetime.datetime.fromtimestamp(message.getTimestamp()).strftime('%Y-%m-%d %H:%M:%S')
        self.ConversationTextControl.AppendText("(%s) %s: %s\n"%(formattedDate, sender, line))
    
    def onClose( self, event ):
        self.GetParent().onConversationFrameDestroy(self)
        self.Destroy()
        
    def onSendButtonClick( self, event ):
        jid = self.GetTitle()
        content = self.MessageTextControl.GetValue()
        self.client.sendMessage(jid, content)
        # NOTE: sendMessage return value gets lost?
        # TODO: disable send button and wait here until server receipt
        # TODO: message entity is constructed here AND in the client. do a copy instead?
        outgoingMessage = TextMessageProtocolEntity(content, to = jid)
        self.append(outgoingMessage)
        self.MessageTextControl.Clear()

class ConversationListFrame ( wxWha.ConversationListFrame ):
    def __init__(self, parent, client, login):
        wxWha.ConversationListFrame.__init__(self, parent)
        self.Bind(INCOMING_MESSAGE_DATA_EVENT, self.onIncomingMessage)
        
        self.client = client
        self.SetTitle("wxpyWha %s"%(login))
        # TODO: save message entities in home folder
        self.entitiesfilename = "entities_%s.pkl"%(login)
        self.conversationFrames = {}
        self.conversations = {}
        self.messageEntities = self.loadEntities()
        for message in sorted(self.messageEntities, key=lambda m:m.getTimestamp()):
            self.appendMessage(message)
        self.populateConversationListBox()
        
    def appendMessage(self, message):
        jid = message.getFrom()
        if jid not in self.conversations:
            self.conversations[jid] = [message]
        else:
            self.conversations[jid].append(message)
        
    def populateConversationListBox(self):
        for jid in self.conversations:
            self.ConversationListBox.Append(jid)
    
    def conversationFrame(self, jid, message = None):
        if jid in self.conversationFrames:
            cf = self.conversationFrames[jid]
            if message:
                cf.append(message)
            cf.Raise()
        else:
            cf = ConversationFrame(self, self.client, jid)
            for message in self.conversations[jid]:
                cf.append(message)
            cf.Show()
            self.conversationFrames[jid] = cf
    
    def onConversationFrameDestroy(self, cf):
        del self.conversationFrames[cf.GetTitle()]
            
    def onListBox( self, event ):
        index = event.GetSelection()
        if (index >= 0):
            self.ConversationListBox.Deselect(index)
            jid = self.ConversationListBox.GetString(index)
            self.conversationFrame(jid)
        
    def onIncomingMessage(self, evt):
        message = evt.messageProtocolEntity
        self.messageEntities.append(message)
        self.saveMessageEntities()
        jid = message.getFrom()
        if jid not in self.conversations:
            self.ConversationListBox.Append(jid)
        self.appendMessage(message)
        self.conversationFrame(jid, message)
            
    def saveMessageEntities(self):
        if DEBUG_PASSIVE:
            sys.stderr.write("Skipped writing entities due to DEBUG_PASSIVE.\n")
        else:
            with open(self.entitiesfilename, 'wb') as f:
                # do not save locally generated debug content
                self.messageEntities = [m for m in self.messageEntities if m.getFrom() not in ["DEBUG@s.whatsapp.net"]]
                #self.messageEntities = [m for m in self.messageEntities if wx.MessageDialog(self, m.getBody(),"Keep Message?", wx.YES|wx.NO|wx.ICON_QUESTION).ShowModal() == wx.ID_YES]
                pickle.dump(self.messageEntities, f)
                f.close()
                sys.stderr.write("Wrote %d entities.\n"%(len(self.messageEntities)))
            
    def loadEntities(self):
        entities = []
        try:
            with open(self.entitiesfilename, 'rb') as f:
                entities = pickle.load(f)
        except IOError as ioe:
            sys.stderr.write("IOError: History was not loaded.\n")
        sys.stderr.write("Loaded %d entities.\n"%(len(entities)))
        return entities

if __name__ == "__main__":
    if (len(sys.argv) != 3):
        sys.stderr.write("Usage: %s login base64passwd"%(sys.argv[0]))
        sys.exit(1)
    login = sys.argv[1]
    base64passwd = sys.argv[2]
    
    app = wx.App()
    
    client = WhaClient((login,base64passwd))
    frame = ConversationListFrame(None, client, login)
    imh = IncomingMessageHandler(frame)
    client.setIncomingMessageHandler(imh)
    if not DEBUG_PASSIVE:
        backgroundClient = threading.Thread(target=client.start)
        backgroundClient.daemon = True
        backgroundClient.start()
    if DEBUG_GENERATE_MESSAGE:
        tmpe = TextMessageProtocolEntity(
            "locally generated test message", 
            _from="DEBUG@s.whatsapp.net")
        imh.onIncomingMessage(tmpe)
    
    frame.Show()
    app.MainLoop()
    
