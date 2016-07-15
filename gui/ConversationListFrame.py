#!/usr/bin/python
# -*- coding: utf-8 -*-

"""@package docstring
Application logic for the ConversationListFrame.
"""

import _generated
import wx
import pickle
import sys
from ConversationFrame import ConversationFrame

"""If true, message entities are not saved"""
DEBUG_SKIP_WRITE_HISTORY = False

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

class ConversationListFrame ( _generated.ConversationListFrame ):
    def __init__(self, parent, client, login, phonebook):
        _generated.ConversationListFrame.__init__(self, parent)
        self.Bind(INCOMING_MESSAGE_DATA_EVENT, self.onIncomingMessage)
        
        self.client = client
        self.phonebook = phonebook
        self.SetTitle("wxpyWha %s"%(login))
        # TODO: save message entities in home folder rather than working directory
        self.entitiesfilename = "entities_%s.pkl"%(login)
        self.conversationFrames = {}
        self.conversations = {}
        self.messageEntities = self.loadEntities()
        for message in sorted(self.messageEntities, key=lambda m:m.getTimestamp()):
            self.appendMessage(message)
        self.populateConversationListBox()
        
    def appendMessage(self, message):
        # TODO: rename method to "append"
        jid = message.getFrom()
        if jid is None:
            jid = message.getTo()
        if jid not in self.conversations:
            self.conversations[jid] = [message]
        else:
            self.conversations[jid].append(message)
        
    def populateConversationListBox(self):
        for jid in self.conversations:
            self.ConversationListBox.Append(self.phonebook.jidToName(jid),jid)
    
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
            jid = self.ConversationListBox.GetClientData(index)
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
        if DEBUG_SKIP_WRITE_HISTORY:
            sys.stderr.write("Skipped writing entities due to DEBUG_SKIP_WRITE_HISTORY.\n")
        else:
            try:
                with open(self.entitiesfilename, 'wb') as f:
                    # do not save locally generated debug content
                    self.messageEntities = [m for m in self.messageEntities if m.getFrom() not in ["DEBUG@s.whatsapp.net"]]
                    #self.messageEntities = [m for m in self.messageEntities if wx.MessageDialog(self, m.getBody(),"Keep Message?", wx.YES|wx.NO|wx.ICON_QUESTION).ShowModal() == wx.ID_YES]
                    pickle.dump(self.messageEntities, f)
                    f.close()
                    sys.stderr.write("Wrote %d entities.\n"%(len(self.messageEntities)))
            except IOError as ioe:
                sys.stderr.write("IOError: History was not stored.\n")
            
    def loadEntities(self):
        entities = []
        try:
            with open(self.entitiesfilename, 'rb') as f:
                entities = pickle.load(f)
        except IOError as ioe:
            sys.stderr.write("IOError: History was not loaded.\n")
        sys.stderr.write("Loaded %d entities.\n"%(len(entities)))
        return entities
