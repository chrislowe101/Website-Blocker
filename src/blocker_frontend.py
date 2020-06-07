from tkinter import *
from blocker_backend import WebsiteDatabase
from blocker_backend import HostsFile
from blocker_backend import BlockTime
import threading
from flask import Flask, render_template

"""
Application that manages a database of websites to block, and the blocking
functionality. The user can interact with this through through a GUI.

Must be run as admin to be able to access hosts file
"""

"""
Frontend - tkinter-based GUI for interacting with application.
Build executable with command 'pyinstaller --clean --onefile --windowed --uac-admin blocker_frontend.py'
"""

class WebsiteBlocker(object):
    """User interface GUI for website blocker"""

    def __init__(self, window, database):
        self.window = window
        self.selected_entry = []
        self.database = WebsiteDatabase(database)
        self.hosts = HostsFile(test_flag=False)
        self.bt = BlockTime()

        self.window.wm_title('Website Blocker')

        # First section - website list, with options to add/update/remove websites
        l1 = Label(window, text='Websites to Block', font=('Helvetica','12','bold'))
        l1.grid(row=0, column=0, columnspan=3)

        self.list1 = Listbox(window, height = 10, width = 64)
        self.list1.grid(row=1, column=0, rowspan=6, columnspan=3)
        sb1 = Scrollbar(window)
        sb1.grid(row = 1,column = 3, rowspan = 6)
        self.list1.configure(yscrollcommand = sb1.set)
        sb1.configure(command = self.list1.yview)
        self.list1.bind('<<ListboxSelect>>', self.getSelectedRow)
        self.viewCommand()

        l2 = Label(window, text='Selected website:')
        l2.grid(row=7, column=0, columnspan=3)

        self.website_entry = StringVar()
        self.e1 = Entry(window, textvariable=self.website_entry, width=64)
        self.e1.grid(row=8, column=0, columnspan=3)

        b1 = Button(window, text='Add website', width=16, command=self.addCommand)
        b1.grid(row=9, column=0)

        b2 = Button(window, text='Update website', width=16, command=self.updateCommand)
        b2.grid(row=9, column=1)

        b3 = Button(window, text='Delete website', width=16, command=self.deleteCommand)
        b3.grid(row=9, column=2)

        # Second section - blocker configuration
        l3 = Label(window, text='Configuration', font=('Helvetica','12','bold'))
        l3.grid(row=0, column=4, columnspan=2)

        self.enable_option = StringVar()
        self.enable_option.set('no')
        c1 = Checkbutton(window, text='Enable blocker', variable=self.enable_option, onvalue='yes', offvalue='no', command=self.enableCommand)
        c1.grid(row=1, column=4, columnspan=2)

        self.time_option = StringVar()
        self.time_option.set('no')
        c2 = Checkbutton(window, text='Block between\nspecified times', variable=self.time_option, onvalue='yes', offvalue='no', command=self.timeCommand)
        c2.grid(row=2, column=4, columnspan=2)

        hour_list = ('00','01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23')
        minute_list = ('00', '15', '30', '45')

        l4 = Label(window, text='Start time')
        l4.grid(row=3, column=4, columnspan=2)

        self.start_hour = StringVar()
        self.start_hour.set(hour_list[9])
        self.o1 = OptionMenu(window, self.start_hour, *hour_list, command=self.timeUpdateCommand)
        self.o1.grid(row=4, column=4)

        self.start_min = StringVar()
        self.start_min.set(minute_list[0])
        self.o2 = OptionMenu(window, self.start_min, *minute_list, command=self.timeUpdateCommand)
        self.o2.grid(row=4, column=5)

        l5 = Label(window, text='End time')
        l5.grid(row=5, column=4, columnspan=2)

        self.end_hour = StringVar()
        self.end_hour.set(hour_list[17])
        self.o3 = OptionMenu(window, self.end_hour, *hour_list, command=self.timeUpdateCommand)
        self.o3.grid(row=6, column=4)

        self.end_min = StringVar()
        self.end_min.set(minute_list[0])
        self.o4 = OptionMenu(window, self.end_min, *minute_list, command=self.timeUpdateCommand)
        self.o4.grid(row=6, column=5)

        self.l6 = Label(window, text='Play!', font=('Helvetica','12','bold'), background='green', width=10, pady=5)
        self.l6.grid(row=8, column=4, rowspan=2, columnspan=2)

        self.enableCommand()

    def getSelectedRow(self, event):
        """Get the currently selected row from the list box. Uses the Tkinter bind method"""
        try:
            index = self.list1.curselection()[0]
            self.selected_entry = self.list1.get(index)
            self.e1.delete(0, END)
            self.e1.insert(END, self.selected_entry[1])
        except IndexError:
            pass

    def viewCommand(self):
        """Displays all websites to be blocked. Called by most other website functions"""
        self.list1.delete(0, END)        # Clear all entries from the list box
        for row in self.database.view():
            self.list1.insert(END, row)    # Sequentially add all entries to the list box

    def addCommand(self):
        """Add the URL in the website field to the list of blocked sites"""
        self.database.add(self.website_entry.get())
        self.viewCommand()

    def updateCommand(self):
        """Update the currently selected URL to the value in the website field"""
        self.database.update(self.selected_entry[0], self.website_entry.get())
        self.viewCommand()

    def deleteCommand(self):
        """Delete the currently selected URL from the list of blocked sites"""
        self.database.delete(self.selected_entry[0])
        self.viewCommand()

    def enableCommand(self):
        """Enables or disables blocking depending on configuration"""
        if self.enable_option.get() == 'yes':
            if self.time_option.get() == 'no':
                self.hosts.blocking_enable(self.database.view())    # Blocking enabled, ignoring time
                self.l6.configure(text='Blocking', background='red')
            elif self.bt.checkTime():
                self.hosts.blocking_enable(self.database.view())    # Blocking enabled and in blocking window
                self.l6.configure(text='Blocking', background='red')
            else:
                self.hosts.blocking_disable(self.database.view())   # Blocking enabled but outside blocking window
                self.l6.configure(text='Play!', background='green')
        else:
            self.hosts.blocking_disable(self.database.view())       # Blocking disabled
            self.l6.configure(text='Play!', background='green')

    def timeCommand(self):
        """Updates blocking times to reflect selection, and checks if blocking shoudl be enabled/disabled"""
        self.bt.updateTimes(self.start_hour.get(), self.start_min.get(), self.end_hour.get(), self.end_min.get())
        self.enableCommand()

    def timeUpdateCommand(self,value):
        """Responds to change in one of the time fields"""
        self.timeCommand()

    def runCommand(self):
        """A recursive loop to regularly check whether to block or not, and the health of the Flask local webserver"""
        self.enableCommand()
        self.window.after(5000, self.runCommand)

"""Flask application for block website, run as a separate thread"""
app = Flask(__name__)

@app.route('/')
def block():
    return render_template('block.html')

def thread_webpage():
    """Function to start Flask application as a thread"""
    app.run(port=80, host='127.0.0.1', debug=False, use_reloader=False)

"""Run application only if main"""
if __name__ == "__main__":
    thread = threading.Thread(target=thread_webpage, daemon=True)  # Start Flask app as a daemon process
    thread.start()

    database = 'websites.db'
    root = Tk()
    blocker = WebsiteBlocker(root, database)
    blocker.runCommand()
    root.mainloop()
