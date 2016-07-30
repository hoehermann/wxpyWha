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
        self.loadMessages()

        # create empty conversations for each contact in phonebook
        for jid in phonebook.get_jids():
            self.updateConversationListBox(jid)
            if jid not in self.conversations:
                self.conversations[jid] = []
                
    def updateConversationListBox(self, jid):
        if jid not in self.conversations:
            self.ConversationListBox.Append(self.phonebook.jid_to_name(jid),jid)
        
    def append(self, message, show=True, save=True):
        # find jid
        jid = message.getFrom()
        if jid is None:
            jid = message.getTo()
            
        # update ListBox for new conversations
        self.updateConversationListBox(jid)
            
        # put message into storage
        if jid not in self.conversations:
            self.conversations[jid] = [message]
        else:
            self.conversations[jid].append(message)
        
        # save messages
        if save:
            self.saveMessages()
            
        # show/create ConversationFrame
        if show:
            self.conversationFrame(jid, message)
    
    def conversationFrame(self, jid, message = None):
        if jid in self.conversationFrames: # frame exists
            cf = self.conversationFrames[jid] # get frame reference
            if message:
                cf.append(message) # append message
            cf.Raise() # bring to front
        else: # frame does not exist
            # create frame
            cf = ConversationFrame(self, self.client, jid, self.phonebook.jid_to_name(jid))
            self.conversationFrames[jid] = cf # save frame reference
            for message in self.conversations[jid]: # append all messages
                cf.append(message)
            cf.Show() # show frame
    
    def onConversationFrameDestroy(self, cf):
        del self.conversationFrames[cf.jid] # remove reference
            
    def onListBox(self, event):
        index = event.GetSelection()
        if (index >= 0):
            self.ConversationListBox.Deselect(index)
            jid = self.ConversationListBox.GetClientData(index)
            self.conversationFrame(jid)
        
    def onIncomingMessage(self, evt):
        message = evt.messageProtocolEntity
        self.append(message)
            
    def saveMessages(self):
        if DEBUG_SKIP_WRITE_HISTORY:
            sys.stderr.write("Skipped writing entities due to DEBUG_SKIP_WRITE_HISTORY.\n")
        else:
            try:
                with open(self.entitiesfilename, 'wb') as f:
                    # do not save locally generated debug content
                    conversations = self.conversations
                    conversations = {k: v for k, v in conversations.iteritems() if k not in ["DEBUG@s.whatsapp.net"]}
                    #conversations = {k: v for k, v in conversations.iteritems() if wx.MessageDialog(self, m.getBody(),"Keep Message?", wx.YES|wx.NO|wx.ICON_QUESTION).ShowModal() == wx.ID_YES}
                    sys.stderr.write("Writing %d messages...\n"%(sum(map(len,conversations.values()))))
                    pickle.dump(self.conversations, f)
                    f.close()
            except IOError as ioe:
                sys.stderr.write("IOError: History was not stored.\n")
            
    def loadMessages(self):
        self.conversations = {}
        try:
            with open(self.entitiesfilename, 'rb') as f:
                data = pickle.load(f)
                if isinstance(data, dict):
                    # history is a dict (conversation jids mapped to list of messages)
                    comparator = lambda jid:jid # default: do not sort
                    if not self.phonebook.is_empty():
                        # phonebook is present: sort list of conversations by name
                        comparator = lambda jid:self.phonebook.jid_to_name(jid)
                    # add conversations into gui
                    for jid in sorted(data, key=comparator):
                        self.updateConversationListBox(jid)
                    self.conversations = data
                elif isinstance(data, list):
                    sys.stderr.write("Data is seems to be old list format. Converting...\n")
                    for message in sorted(data, key=lambda m:m.getTimestamp()):
                        self.append(message,False,False)
                else:
                    sys.stderr.write("Data is neither dict nor list.\n")
        except IOError as ioe:
            sys.stderr.write("IOError: History was not loaded.\n")
        sys.stderr.write("Loaded %d messages.\n"%(sum(map(len,self.conversations.values()))))
