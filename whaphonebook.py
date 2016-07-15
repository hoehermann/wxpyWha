#!/usr/bin/python
# -*- coding: utf-8 -*-

"""@package docstring
A phone book. It maps jids to names.

Based on suggestion by https://github.com/sowerkoku .
"""

import csv
import sys
import traceback

class Phonebook():
    
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
            traceback.print_exc()
        except: # catch *all* exceptions
            sys.stderr.write("Unhandled exception.\n")
            traceback.print_exc()
        sys.stderr.write("Phonebook has %d entries.\n"%(len(this.entries)))
        return this
    
    def __init__(self):
        self.entries = {
            "phone1@s.whatsapp.net" : "contact1",
            "phone2@s.whatsapp.net" : "contact2",
        }

    def jidToName(self, jid):
        if jid not in self.entries:
            return jid
        else:
            return self.entries[jid]
            
if __name__ == "__main__":
    phonebook = Phonebook.from_csv("phonebook.csv")
    print(phonebook.entries)
