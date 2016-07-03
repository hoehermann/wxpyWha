#!/usr/bin/python
# -*- coding: utf-8 -*-

import wx
from wxWha import ConversationFrame, ConversationListFrame
import threading
from whalayer import WhaClient
import sys
import pickle
import datetime

IncomingMessageDataEventType = wx.NewEventType()
INCOMING_MESSAGE_DATA_EVENT = wx.PyEventBinder(IncomingMessageDataEventType, 1)
class IncomingMessageDataEvent(wx.PyCommandEvent):
    def __init__(self, etype, eid, messageProtocolEntity):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self.messageProtocolEntity = messageProtocolEntity

"""
This is called from outside the wxApp context.
Generates a wxEvent and posts it to the wxApp main loop.
"""
class IncomingMessageHandler():
    def __init__(self, gui):
        self.gui = gui
    def onIncomingMessage(self, messageProtocolEntity):
        #sys.stderr.write("IncomingMessageHandler received incoming message.\n")
        evt = IncomingMessageDataEvent(IncomingMessageDataEventType, -1, messageProtocolEntity)
        wx.PostEvent(self.gui, evt)

class MainFrame ( ConversationListFrame ):
    def __init__(self, parent, client):
        ConversationListFrame.__init__(self,parent)
        self.Bind(INCOMING_MESSAGE_DATA_EVENT, self.onIncomingMessage)
        self.conversationFrames = {}
        self.client = client
        self.load()
        for jid in self.conversationFrames:
            self.ConversationListBox.Append(jid)
            
    def onListBox( self, event ):
        index = event.GetSelection()
        jid = self.ConversationListBox.GetString(index)
        self.conversationFrames[jid].Show()
        
    # TODO: move method into ConversationFrame
    def onSendButtonClick( self, conversationFrame, event ):
        sys.stderr.write("onSendButtonClick\n")
        self.client.sendMessage(conversationFrame.GetTitle(), conversationFrame.MessageTextControl.GetValue())
        conversationFrame.ConversationTextControl.AppendText("%s: %s\n"%("Ich", conversationFrame.MessageTextControl.GetValue()))
        conversationFrame.MessageTextControl.Clear()
        
    def conversation(self, f):
        # TODO: reconstruct C++ part of frame
        if f not in self.conversationFrames:
            # TODO: repopulate ConversationListFrame
            cf = ConversationFrame(self)
            self.conversationFrames[f] = cf
            # TODO: move initialisation into ConversationFrame
            cf.SetTitle(f)
            cf.SendButton.Bind( wx.EVT_BUTTON, lambda event: self.onSendButtonClick(cf, event))
        else:
            cf = self.conversationFrames[f]
        return cf
        
    def onIncomingMessage(self, evt):
        message = evt.messageProtocolEntity
        
        entities = self.loadEntities()
        entities.append(message)
        self.saveEntities(entities)
        
        jid = message.getFrom()
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
        
        cf = self.conversation(jid)
        cf.ConversationTextControl.AppendText("(%s) %s: %s\n"%(formattedDate, sender, line))
        cf.Show()
            
        self.save()

    def save(self):
        conversations = {}
        for f, cf in self.conversationFrames.items():
            conversations[f] = cf.ConversationTextControl.GetValue()
        with open("messages.pkl", 'wb') as f:
            pickle.dump(conversations, f)
            f.close()
            
    def load(self):
        try:
            with open("messages.pkl", 'rb') as f:
                conversations = pickle.load(f)
                for f, text in conversations.items():
                    cf = self.conversation(f)
                    cf.ConversationTextControl.AppendText(text)
                    cf.Show()
        except IOError as ioe:
            sys.stderr.write("IOError: History was not loaded.\n")
            
    def saveEntities(self, entities):
        with open("entities.pkl", 'wb') as f:
            pickle.dump(entities, f)
            f.close()
            sys.stderr.write("Wrote %d entities.\n"%(len(entities)))
            
    def loadEntities(self):
        entities = []
        try:
            with open("entities.pkl", 'rb') as f:
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
    
    app = wx.App(False)
    
    client = WhaClient((login,base64passwd))
    frame = MainFrame(None, client)
    imh = IncomingMessageHandler(frame)
    client.setIncomingMessageHandler(imh)
    
    backgroundClient = threading.Thread(target=client.start)
    backgroundClient.start()
    
    frame.Show()
    app.MainLoop()
    
