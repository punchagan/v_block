# An Android script that let's you block calls from unwanted numbers.

# Copyright (C) 2011 Puneeth Chaganti <punchagan@gmail.com>
# Copyright (C) 2011 Thomas Stephen Lee <lee.iitb@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
import android
from time import sleep

# import gdata.contacts
import gdata
import gdata.docs.service

droid = android.Android()

try:
    droid.stopTrackingPhoneState()
except:
    pass

class GoogleDoc():
    """Google Doc Class."""
    def __init__(self, email, password, gdoc_name, num_file):
        try:
            f = open('/sdcard/sl4a/scripts/userinfo.py')
            self.email, self.password = [t.strip() for t in f.readlines()[:2]]
            f.close()
        except:
            self.email = droid.dialogGetInput('Email').result
            self.password = droid.dialogGetPassword('Password', 'For ' + self.email).result
            f = open('/sdcard/sl4a/scripts/userinfo.py', 'w')
            f.write('%s\n' %self.email)
            f.write('%s\n' %self.password)
            f.close()
        self.client = gdata.docs.service.DocsService()
        self.client.email = self.email
        self.client.password = self.password
        self.name = gdoc_name
        self.q = gdata.docs.service.DocumentQuery()
        self.q['title'] = self.name
        self.q['title-exact'] = 'true'
        self.file = num_file
        print "all variables initialized"
        self.get_gdata()

    def get_gdata(self):
        print "logging in"
        self.client.ProgrammaticLogin()
        print "doc querying"
        self.feed = self.client.Query(self.q.ToUri())
        self.entry = self.feed.entry[0]
        self.client.Export(self.entry, self.file)
        print "Fetched latest list!"

    def save_gdata(self):
        print "logging in"
        self.client.ProgrammaticLogin()
        self.feed = self.client.Query(self.q.ToUri())
        print "fetched feed!"
        self.entry = self.feed.entry[0]
        ms = gdata.MediaSource(file_path=self.file,
                                                 content_type=gdata.docs.service.SUPPORTED_FILETYPES['TXT'])
        self.entry.title.text = self.name
        updated_entry = self.client.Put(ms, self.entry.GetEditMediaLink().href)
        print "Numbers Updated!"

def get_block_list(f):
    numbers = open(f).readlines()[1:]
    # first line is being garbled by gdocs.
    block_list = [num.strip() for num in numbers]
    return block_list

def block_number(f, block_list, number):
    # need to update data.. before saving it..
    # otherwise others changes will be lost. 
    block_list.append(number)
    f = open(f, 'w')
    f.write('%s\n' % 'Blocked Numbers') # heading, since first line is being garbled
    for num in block_list:
        f.write('%s\n' % num)
    f.close()

def test_alert_dialog_with_buttons():
    title = 'Alert'
    message = 'Add number to Blocked list? '
    droid.dialogCreateAlert(title, message)
    droid.dialogSetPositiveButtonText('Yes')
    droid.dialogSetNegativeButtonText('No')
    droid.dialogShow()
    response = droid.dialogGetResponse().result
    return response['which'] == 'positive'

def event_loop(g, b_l, f):
    print "started the event loop!"
    ringing, notify, dialog = False, False, False
    # silent = droid.checkRingerSilentMode()
    toggle = False
    while True:
        e = droid.readPhoneState()
        if e.result is not {}:
            # print "result is sane"
            # print e.result, "general"
            if 'state' in e.result.keys() and e.result['state'] == u'ringing':
                ringing = True
                # print "phone is ringing"
                if e.result['incomingNumber'] in b_l:
                    # print "stupid number"
                    # print e.result, "Blocked Number"
                    droid.makeToast("Blocked Number " + e.result['incomingNumber'])
                    print "Toasted"
                    if not notify:
                        if not droid.checkRingerSilentMode().result:
                            print "Toggled Silent mode"
                            droid.toggleRingerSilentMode()
                            toggle = True
                        else:
                            print "Already silent"
                            # already silent
                            pass
                        # print "making notification"
                        droid.notify("Blocked Number ", e.result['incomingNumber'])
                        notify = True # notification printing
                        dialog = True # we don't need dialog for these numbers
                        print "Notified" #, droid.checkRingerSilentMode()
                    else:
                        # only one notification
                        sleep(2) # reduced the loop time. put this for makeToast
                        pass
                else:
                    if not dialog:
                        button = test_alert_dialog_with_buttons()
                        dialog = True # dialog shown
                        print "Dialoged"
                        if button:
                            block_number(f, b_l, e.result['incomingNumber'])
                            g.save_gdata()
                        else:
                            pass
            else:
                if ringing:
                    # state changed from ringing to something
                    ringing = False
                    print "Ringing Stopped"
                    if toggle:
                        droid.toggleRingerSilentMode()
                        toggle = False
                        print "Toggle back to Loud mode"
                notify, dialog = False, False
        sleep(0.1)
    return False

def test_phone_state(g, b_l, f):
    droid.startTrackingPhoneState()
    try:
        event = event_loop(g, b_l, f)
    finally:
        droid.stopTrackingPhoneState()
    return event


if __name__ == '__main__':
    num_file = '/sdcard/sl4a/scripts/numbers.txt'
    g = GoogleDoc('thomas.stephen.lee@gmail.com', 'leepunch',
                  'blockedNumbers', num_file)
    b_l = get_block_list(num_file)
    test_phone_state(g, b_l, num_file)

