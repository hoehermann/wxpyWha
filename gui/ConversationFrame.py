#!/usr/bin/python
# -*- coding: utf-8 -*-

"""@package docstring
Application logic for the ConversationFrame.
"""

import gui._generated # TODO: name this properly (mind inheritance and super calls)
import wx
import datetime
import traceback

import tempfile # temporary filenames for downloaded media files
#from urllib2 import HTTPError # for handling errors while downloading media files

# from pywhatsapp
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity

"""If True, names instead of JIDs are shown in the conversation history (if set by the participant)."""
CONFIG_SHOW_NAMES = True

"""
If True, phonebook is automatically filled with names and numbers of incoming messages.
This doesn't do anthing useful, yet.
Only active, if CONFIG_SHOW_NAMES is True.
"""
CONFIG_PHONEBOOK_AUTO_ADD = False

"""Name to use for own messages in conversation history."""
CONGFIG_OWN_NAME = "SELF" # formerly SELF@s.whatsapp.net

"""If true, hitting the escape key closes the conversation frame."""
CONFIG_ESCAPE_CLOSES = True

class ConversationFrame ( gui._generated.ConversationFrame ):
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
        gui._generated.ConversationFrame.__init__(self, parent)
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
        
    def append(self, message, new):
        """Adds a message to this conversation history display."""
        jid = message.getFrom()
        if jid is None:
            # outgoing message
            # displayed in conversation as sent from SELF
            jid = message.getTo()
            sender_name = CONGFIG_OWN_NAME
        else:
            # incoming message
            if CONFIG_SHOW_NAMES:
                # show names of contacts
                sender_name = message.getNotify()
                if sender_name and CONFIG_PHONEBOOK_AUTO_ADD:
                    # automatically add contacts to phonebook
                    sender_jid = jid
                    if message.isGroupMessage():
                        sender_jid = message.getParticipant()
                    if self.GetParent().phonebook.add(sender_jid, sender_name):
                        # this was a previously unknown contact: save phonebook file
                        self.GetParent().phonebook.to_csv_file()
            else:
                # do not resolve names, show jids instead
                if message.isGroupMessage():
                    sender_name = message.getParticipant()
                else:
                    sender_name = jid
        t = message.getType()
        if t == "text":
            line = message.getBody()
        elif t == "media":
            # TODO: split this into shorter methods. maybe move into main application logic.
            mt = message.getMediaType()
            if new:
                if hasattr(message, 'getMediaContent') and callable(getattr(message, 'getMediaContent')):
                    if mt in ["image", "audio", "video", "document"]:
                        extension = "unknown"
                        try:
                            pass
                            extension = message.getExtension()
                        except Exception as e:
                            if "Unsupported/unrecognized mimetype" in str(e):
                                extension = ".%s"%(message.getMimeType().split("/")[-1])
                            else:
                                raise
                        filename = "%s/%s%s"%(tempfile.gettempdir(),message.getId(),extension)
                        try:
                            f = open(filename, 'wb')
                            f.write(message.getMediaContent())
                            line = "File of media type %s with %s bytes size was downloaded from %s and decrypted to local file %s."%(message.getMediaType(),str(message.getMediaSize()),message.getMediaUrl(),filename)
                        #except HTTPError as httpe:
                        #    line = "File of media type %s could not be downloaded. Reason: %s"%(message.getMediaType(),httpe.reason)
                        except:
                            # TODO: reintroduce error-handling
                            raise
                    else:
                        line = "Message is of unhandled media type %s."%(mt)
                else:
                    line = "The currently loaded version of yowsup cannot decrypt media messages."
            else:
                line = "Message of type %s was received in the past."%(t)
        else:
            line = "Message is of unhandled type %s."%(t)
            
        formattedDate = datetime.datetime.fromtimestamp(message.getTimestamp()).strftime('%Y-%m-%d %H:%M:%S')
        self.ConversationTextControl.AppendText(
            "(%s) %s: %s\n"%(
                formattedDate, 
                sender_name, 
                line
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
            try:
                self.StatusBar.SetStatusText("Sending message...")
                outgoingMessage = TextMessageProtocolEntity(content, to = self.jid)
                sent = self.client.sendMessage(outgoingMessage)
                # TODO: find out if pushing into the layer needs a deep copy
                # TODO: find out why the returncode stored in "sent" is always "None"
                self.MessageTextControl.SetEditable(False)
                self.SendButton.Enable(False)
            except:
                self.StatusBar.SetStatusText("An error occurred.")
                raise
        else:
            self.StatusBar.SetStatusText("Empty message was ignored.")

    def onMessageSent(self, status, message = None):
        """Handler for information about a message being successfully sent or not."""
        if (isinstance(status, bool)):
            if (status):
                # message reported sent
                self.StatusBar.SetStatusText("Message sent, waiting for server response...")
                self.GetParent().append(message)
            else:
                # this actually is never used
                self.StatusBar.SetStatusText("Unknown error occurred.")
        else:
            # an error string was given, display it
            self.StatusBar.SetStatusText(status)
        # re-enable GUI so the message can be edited and/or sent again
        self.MessageTextControl.SetEditable(True)
        self.SendButton.Enable(True)
        
    def onMessageAcknowledged(self):
        """Handler for server-side acknowledgements."""
        self.StatusBar.SetStatusText("Message received by server.")
        # TODO: ignore repeated "partitipant received message" acknowledgements in group chats
        self.MessageTextControl.Clear()
