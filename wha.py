#!/usr/bin/python
# -*- coding: utf-8 -*-

"""@package docstring
Main module for wxpyWha. A simple wxWidgets GUI wrapper atop yowsup.
"""

import wx
import threading
from whastack import WhaClient
from gui.ConversationListFrame import ConversationListFrame, IncomingMessageHandler
import sys

# from pywhatsapp
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity

"""If true, locally generates a message to handle in the GUI."""
DEBUG_GENERATE_MESSAGE = False

"""If true, don't actually connect to whatsapp (local testing only)."""
DEBUG_PASSIVE = False

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
    
