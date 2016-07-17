#!/usr/bin/python
# -*- coding: utf-8 -*-

"""@package docstring
A phone book. It maps jids to names.

Code contributed by by https://github.com/sowerkoku . Thanks.
"""

import csv
import xml.etree.ElementTree as ElementTree
import os
import sys
import traceback

# This suppresses an XPath related FutureWarning.
import warnings
warnings.simplefilter(action = "ignore", category = FutureWarning)

class Phonebook():
    
    def __init__(self):
        """ Creates a default phonebook with dummy content.
        (You may edit this to your needs.)
        """
        self.entries = {
            # example of content
            "phone1@s.whatsapp.net" : "contact1",
            "phone2@s.whatsapp.net" : "contact2",
        }
    
    @classmethod
    def from_csv(cls, csv_file_name):
        this = cls()
        this.entries = {}
        try:
            with open(csv_file_name, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter='\t')
                for row in reader:
                    this.entries[row[0]] = row[1]
        except IOError as ioe:
            sys.stderr.write("IOError: Phonebook was not loaded.\n")
        except:
            sys.stderr.write("Unhandled exception.\n")
            traceback.print_exc()
        sys.stderr.write("Phonebook loaded from CSV has %d entries.\n"%(len(this.entries)))
        return this
        
    @classmethod
    def from_pidgin(cls):
        this = cls()
        this.entries = {}
        home = os.path.expanduser("~")
        try:
            tree = ElementTree.parse(os.path.join(home,".purple","blist.xml"))
            # extract contact info
            for elem in tree.iterfind('//buddy[@proto="prpl-whatsapp"]'):
                this.entries["%s@s.whatsapp.net"%(elem.find('name').text)] = elem.find('alias').text
            # extract group chat info
            for elem in tree.iterfind('//chat[@proto="prpl-whatsapp"]'):
                this.entries["%s@g.us"%(elem.find('.//component[@name="id"]').text)] = elem.find('alias').text
        except IOError as ioe:
            sys.stderr.write("IOError: Phonebook was not loaded.\n")
        except:
            sys.stderr.write("Unhandled exception.\n")
            traceback.print_exc()
        sys.stderr.write("Phonebook loaded from Pidgin has %d entries.\n"%(len(this.entries)))
        return this
        
    def is_empty(self):
        return not bool(self.entries)

    def jidToName(self, jid):
        if jid not in self.entries:
            return jid
        else:
            return self.entries[jid]
            
    def get_jids(self):
        return self.entries.keys()
            
if __name__ == "__main__":
    phonebook = Phonebook.from_csv("phonebook.csv")
    print(phonebook.entries)
    phonebook = Phonebook.from_pidgin()
    print(phonebook.entries)
