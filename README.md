# wxpyWha

Crude wxPython GUI around the yowsup Whatsapp client library.

For Python 2.7. Tested on Linux only.

It looks like this:
![Screenshot](/screenshot.png?raw=true "Screenshot")

## Features

 *  Receive text messages from single person conversations and group chats.
 *  Answering a conversation with a text message.
 *  Supports unicode emojis and other characters.

## Dependencies

Depends on [yowsup](https://github.com/tgalal/yowsup) and [wxPython](https://www.wxpython.org).

* yowsup can usually be installed with `pip install yowsup2` (Linux and Windows). Builing on Windows currently fails due to a [bug](https://github.com/tgalal/python-axolotl-curve25519/issues/5).
* wxPython can be installed via package manager (Linux distributions) or downloaded from their website (Windows).

See the respective project websites for more detailed installation instructions.

## Legal

### Icon
The application icon consists of three images of different sources:

* [Paul Sherman](http://www.wpclipart.com/animals/snake/snake_clipart/snake_nervous_cartoon.png.html), Public Domain
* [The wxWidgets Project](https://commons.wikimedia.org/wiki/File:WxWidgets.svg), Creative Commons
* [David G. Fandos](https://github.com/davidgfnet/whatsapp-purple/raw/master/whatsapp48.png), unknown License
