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
        self.filename = None
    
    @classmethod
    def from_csv(cls, csv_file_name):
        this = cls()
        this.filename = csv_file_name
        this.entries = {}
        try:
            with open(csv_file_name, 'r', encoding='utf-8') as csvfile:
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
        
    def add(self, jid, name):
        if jid not in self.entries:
            sys.stderr.write("Added name %s for jid %s to phonebook.\n"%(name, jid))
            self.entries[jid] = name
            return True
        else:
            return False

    def jid_to_name(self, jid):
        if jid not in self.entries:
            sys.stderr.write("Phonebook contains no name for jid %s.\n"%(jid))
            return jid
        else:
            return self.entries[jid]
            
    def get_jids(self):
        return self.entries.keys()
            
    def to_csv_file(self, csv_file_name = None):
        if csv_file_name is None:
            csv_file_name = self.filename
        if csv_file_name is not None:
            try:
                with open(csv_file_name, 'wb') as csvfile:
                    writer = csv.writer(csvfile, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
                    for jid, name in self.entries.items():
                        writer.writerow([jid, name])
                    sys.stderr.write("Wrote %d Phonebook entries into file.\n"%(len(self.entries)))
            except IOError as ioe:
                sys.stderr.write("IOError: Phonebook was not stored.\n")
            except:
                sys.stderr.write("Unhandled exception.\n")
                traceback.print_exc()
            
if __name__ == "__main__":
    phonebook = Phonebook.from_csv("phonebook.csv")
    print(phonebook.entries)
    phonebook = Phonebook.from_pidgin()
    print(phonebook.entries)
