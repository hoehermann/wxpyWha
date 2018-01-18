#!/usr/bin/python
# -*- coding: utf-8 -*-

"""@package docstring
Main module for wxpyWha. A simple wxWidgets GUI wrapper atop yowsup.
"""

import wx
import threading
from whastack import WhaClient
from gui.ConversationListFrame import ConversationListFrame, YowsupEventHandler
from whaphonebook import Phonebook
import sys

# from pywhatsapp
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity

"""If true, locally generates a message to handle in the GUI."""
DEBUG_GENERATE_MESSAGE = False

"""If true, don't actually connect to whatsapp (local testing only)."""
DEBUG_PASSIVE = False

if __name__ == "__main__":
    if (len(sys.argv) != 3):
        sys.stderr.write("Usage: %s login base64passwd\n"%(sys.argv[0]))
        sys.exit(1)
    # TODO: add compatibility to yowsup configuration file
    login = sys.argv[1]
    base64passwd = sys.argv[2]
    
    app = wx.App()
    
    phonebook = Phonebook.from_csv("phonebook.csv") # TODO: load from user directory rather than working directory
    if phonebook.is_empty():
        phonebook = Phonebook.from_pidgin()
    if phonebook.is_empty():
        phonebook = Phonebook()
    client = WhaClient((login,base64passwd))
    frame = ConversationListFrame(None, client, login, phonebook)
    handler = YowsupEventHandler(frame)
    client.setYowsupEventHandler(handler)
    if not DEBUG_PASSIVE:
        backgroundClient = threading.Thread(target=client.start)
        backgroundClient.daemon = True
        backgroundClient.start()
    if DEBUG_GENERATE_MESSAGE:
        tmpe = TextMessageProtocolEntity(
            "locally generated test message", 
            _from="DEBUG@s.whatsapp.net")
        imh.onIncomingMessage(tmpe)
    
    icon = wx.Icon("wxpyWha.ico", wx.BITMAP_TYPE_ICO)
    frame.SetIcon(icon)
    
    frame.Show()
    app.MainLoop()
    
