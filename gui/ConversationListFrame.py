# -*- coding: utf-8 -*-

"""@package docstring
Application logic for the ConversationListFrame.
"""

import gui._generated # TODO: name this properly (mind inheritance and super calls)
import wx
import pickle
import sys
from gui.ConversationFrame import ConversationFrame
from yowsup.layers.protocol_messages.protocolentities import MessageProtocolEntity

"""If true, message entities are not saved"""
DEBUG_SKIP_WRITE_HISTORY = False

DataEventType = wx.NewEventType()
DATA_EVENT = wx.PyEventBinder(DataEventType, 1)
class DataEvent(wx.PyCommandEvent):
    """Custom event type for receiving messages."""
    def __init__(self, etype, eid, data):
        wx.PyCommandEvent.__init__(self, etype, eid)
        self.data = data
        
class YowsupEventHandler():
    """Handler for incoming messages."""
    def __init__(self, gui):
        self.gui = gui
    def handleEvent(self, data):
        """
        This is called from outside the wxApp context.
        Generates a wxEvent and posts it to the wxApp main loop.
        """
        evt = DataEvent(DataEventType, -1, data)
        wx.PostEvent(self.gui, evt)

class ConversationListFrame ( gui._generated.ConversationListFrame ):
    def __init__(self, parent, client, login, phonebook):
        gui._generated.ConversationListFrame.__init__(self, parent)
        self.Bind(DATA_EVENT, self.onYowsupEvent)
        
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
        
    def append(self, message, show=True, save=True, new=True):
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
            self.conversationFrame(jid, message, new)
    
    def conversationFrame(self, jid, message = None, new = False):
        # Setting new to default True will always re-process last media-message
        if jid in self.conversationFrames: # frame exists
            cf = self.conversationFrames[jid] # get frame reference
            if message:
                cf.append(message, new) # append message
            cf.Raise() # bring to front
        else: # frame does not exist
            # create frame
            cf = ConversationFrame(self, self.client, jid, self.phonebook.jid_to_name(jid))
            self.conversationFrames[jid] = cf # save frame reference
            for idx, message in enumerate(self.conversations[jid]): # append all messages
                cf.append(message, new and idx == len(self.conversations[jid])-1) # mark only last message as new
            cf.Show() # show frame
    
    def onConversationFrameDestroy(self, cf):
        del self.conversationFrames[cf.jid] # remove reference
            
    def onListBox(self, event):
        index = event.GetSelection()
        if (index >= 0):
            self.ConversationListBox.Deselect(index)
            jid = self.ConversationListBox.GetClientData(index)
            self.conversationFrame(jid)
        
    def onYowsupEvent(self, evt):
        if (isinstance(evt.data, MessageProtocolEntity)):
            self.onIncomingMessage(evt)
        elif (isinstance(evt.data,tuple)):
            if (evt.data[0] == "sendMessage"):
                self.onMessageSent(evt)
            elif (evt.data[0] == "ack"):
                self.onMessageAcknowledged(evt)
            else:
                sys.stderr.write("Unknown Yowsup event \"%s\".\n"%(evt.data[0]))
        else:
            sys.stderr.write("Unknown Yowsup event \"%s\".\n"%(str(evt.data.__class__)))
        
    def onIncomingMessage(self, evt):
        message = evt.data
        self.append(message)
        
    def onMessageSent(self, evt):
        _, message, status = evt.data
        jid = message.getTo()
        if jid in self.conversationFrames:
            self.conversationFrames[jid].onMessageSent(status, message)
            
    def onMessageAcknowledged(self, evt):
        _, entity = evt.data
        if (entity.getClass() == "message"):
            jid = entity._from # TODO: do not access "private" attribute
            if jid in self.conversationFrames:
                self.conversationFrames[jid].onMessageAcknowledged(entity)
            
    def saveMessages(self):
        if DEBUG_SKIP_WRITE_HISTORY:
            sys.stderr.write("Skipped writing entities due to DEBUG_SKIP_WRITE_HISTORY.\n")
        else:
            try:
                with open(self.entitiesfilename, 'wb') as f:
                    conversations = self.conversations
                    # do not save locally generated debug content
                    conversations = {k: v for k, v in conversations.items() if k not in ["DEBUG@s.whatsapp.net"]}
                    #conversations = {k: v for k, v in conversations.iter() if wx.MessageDialog(self, m.getBody(),"Keep Message?", wx.YES|wx.NO|wx.ICON_QUESTION).ShowModal() == wx.ID_YES}
                    sys.stderr.write("Writing %d messages...\n"%(sum(map(len,conversations.values()))))
                    pickle.dump(conversations, f)
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
                        self.append(message,False,False,False)
                    self.saveMessages()
                else:
                    sys.stderr.write("Data is neither dict nor list.\n")
        except IOError as ioe:
            sys.stderr.write("IOError: History was not loaded.\n")
        sys.stderr.write("Loaded %d messages.\n"%(sum(map(len,self.conversations.values()))))
