# wxpyWha

Crude wxPython GUI around the yowsup Whatsapp client library.

For Python 2.7. Tested on Linux only.

It looks like this:
![Screenshot](/screenshot.png?raw=true "Screenshot")

## Features

 *  Receive text messages from single person conversations and group chats.
 *  Answering a conversation with a text message.
 *  Initiating a conversasation with a known contact.
 *  Supports unicode emojis and other characters.
 *  Receive audio or image media messages from single person conversations.

## Manual

### Phonebook

A file with tab separated pairs of numbers and names can act as a phonebook (also known as "list of contacts").

### Initiate Conversation

To initiate a conversation, follow these steps:

 1.  Shutdown program.
 2.  Manually add the contact's jid and name to the phonebook.
 3.  Start program.  
     An empty conversation with the newly added contact should be displayed in the list of conversations.

## Dependencies

Depends on [yowsup](https://github.com/tgalal/yowsup) and [wxPython](https://www.wxpython.org).

 *  yowsup can usually be installed with `pip install yowsup2` (Linux and Windows). Building yowsup's implementation of Curve25519 currently fails on Windows due to a [bug](https://github.com/tgalal/python-axolotl-curve25519/issues/5).
 *  wxPython can be installed via package manager (Linux distributions) or downloaded from their website (Windows).

See the respective project websites for more detailed installation instructions.

## Legal

License is GPL.

### Icon
The application icon consists of three images of different sources:

 *  [Paul Sherman](http://www.wpclipart.com/animals/snake/snake_clipart/snake_nervous_cartoon.png.html), Public Domain
 *  [The wxWidgets Project](https://commons.wikimedia.org/wiki/File:WxWidgets.svg), Creative Commons
 *  [David G. Fandos](https://github.com/davidgfnet/whatsapp-purple/raw/master/whatsapp48.png), unknown License
