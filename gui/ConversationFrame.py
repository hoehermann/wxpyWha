#!/usr/bin/python
# -*- coding: utf-8 -*-

"""@package docstring
Application logic for the ConversationFrame.
"""

import _generated
import wx
import datetime

# from pywhatsapp
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity

"""If true, names instead of JIDs are shown in the conversation history (if set by the participant)."""
CONFIG_SHOW_NAMES = True

"""Name to use for own messages in conversation history."""
CONGFIG_OWN_NAME = "SELF" # formerly SELF@s.whatsapp.net

"""If true, hitting the escape key closes the conversation frame."""
CONFIG_ESCAPE_CLOSES = True

class ConversationFrame ( _generated.ConversationFrame ):
    """
    This is the ConversationFrame. 
    
    A simple frame with a textarea for the conversation history, 
    as well as an input area for answers and a send button.
    """
    
    def __init__(self, parent, client, jid, title):
        """
        :param client: Reference to the WhaLayer doing the actual work (for sending messages)
        :param jid: The ID of this conversation (the other party or group chat).
        """
        _generated.ConversationFrame.__init__(self, parent)
        self.client = client
        self.jid = jid
        self.SetTitle(title)
        self.SetIcon(self.GetParent().GetIcon())
        self.MessageTextControl.SetFocus()
        self.ConversationTextControl.SetEditable(False)
        self.Bind(wx.EVT_CHAR_HOOK, self.onKeyPressed)
        
    def onKeyPressed( self, event ):
        """Handler for all kestrokes on this frame."""
        code = event.GetKeyCode()
        if code == wx.WXK_RETURN:
            if event.ShiftDown():
                # shift+return produces a new line
                event.Skip() # event is forwarded to next control
            else:
                # plain return sends message
                self.onSendButtonClick(event) # forwarding the event probably isn't correct
        elif code == wx.WXK_ESCAPE and CONFIG_ESCAPE_CLOSES:
            self.Close()
        else:
            # all other keystrokes
            event.Skip() # event is forwarded to next control
        
    def append(self, message):
        """Adds a message to this conversation history."""
        jid = message.getFrom()
        if jid is None:
            # outgoing message
            # displayed in conversation as sent from SELF
            jid = message.getTo()
            sender = CONGFIG_OWN_NAME
        else:
            # incoming message
            if CONFIG_SHOW_NAMES:
                sender = message.getNotify()
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
            # NOTE: for t == "media", message.url is available, but content is encrypted. as of 2016-07-12, yowsup cannot decrypt
            
        formattedDate = datetime.datetime.fromtimestamp(message.getTimestamp()).strftime('%Y-%m-%d %H:%M:%S')
        self.ConversationTextControl.AppendText(
            "(%s) %s: %s\n"%(
                formattedDate, 
                sender, 
                line.encode("utf-8") 
                # I have no idea why this encode("utf-8") is needed for a message containing 😊, but messages containing 😀😉🐘💨☠ work fine without
                # TODO: Research how python unicode handling interacts with wxPython unicode handling
            )
        )
    
    def onClose( self, event ):
        """Notifies the parent ConversationListFrame before destruction."""
        self.GetParent().onConversationFrameDestroy(self)
        self.Destroy()
        
    def onSendButtonClick( self, event ):
        """Sends a message via the WhaLayer."""
        content = self.MessageTextControl.GetValue()
        if content:
            outgoingMessage = TextMessageProtocolEntity(content, to = self.jid)
            self.client.sendMessage(outgoingMessage) # TODO: find out if pushing into the layer needs a deep copy
            # NOTE: sendMessage return value gets lost?
            # TODO: disable send button and wait for server acknowledgement
            
            # append to list of raw entities, sorted entites, save them
            # append to this conversation
            # TODO: encapsulate in one method
            self.GetParent().messageEntities.append(outgoingMessage)
            self.GetParent().appendMessage(outgoingMessage)
            self.GetParent().saveMessageEntities()
            self.append(outgoingMessage)
            
            # clear input field
            # TODO: only do so after server acknowledged
            self.MessageTextControl.Clear()
