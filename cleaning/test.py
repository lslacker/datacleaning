#!/usr/bin/env python

from win32com.client import Dispatch

session = Dispatch("MAPI.session")
session.Logon('mail')  # MAPI profile name
inbox = session.Inbox

print "Inbox name is:", inbox.Name
print "Number of messages:", inbox.Messages.Count

for i in range(inbox.Messages.Count):
    message = inbox.Messages.Item(i + 1)
    print message.Subject