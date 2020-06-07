import sqlite3
from datetime import datetime, time
from shutil import copyfile
import sys

"""
Application that manages a database of websites to block, and the blocking
functionality. The user can interact with this through through a GUI.
"""

"""
Backend - sqlite3 database. Uses databeas "websites.db" - creates this if doesn't already exist
"""

class WebsiteDatabase:
    """Class for managing the database of websites to be blocked"""

    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()
        self.cur.execute("CREATE TABLE IF NOT EXISTS websites (id INTEGER PRIMARY KEY, url TEXT PRIMARY KEY)")
        self.conn.commit()

    def view(self):
        self.cur.execute("SELECT * FROM websites")
        rows = self.cur.fetchall()
        return rows

    def add(self, url):
        self.cur.execute("INSERT INTO websites VALUES (NULL,?)",(url,))
        self.conn.commit()

    def delete(self, id):
        self.cur.execute("DELETE FROM websites WHERE id=?",(id,))
        self.conn.commit()

    def update(self, id, url):
        self.cur.execute("UPDATE websites SET url=? WHERE id=?",(url,id))
        self.conn.commit()

    def __del__(self):
        self.conn.close()

class HostsFile:
    """Class for manipulating the hosts file"""

    def __init__(self, test_flag=True):

        # Check operating system
        if sys.platform.startswith('linux'):
            op_sys = "linux"
        else:
            op_sys = sys.platform

        # Set host file path
        if test_flag:
            self.hosts_path = "hosts"
        else:
            if op_sys == "win32":
                self.hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            elif op_sys == "linux" or op_sys == "darwin":
                self.hosts_path = r"\etc\hosts"    # For live use on Mac or Linux
            else:
                self.hosts_path = None

        self.redirect = "127.0.0.1"                 # Redirect page
        copyfile(self.hosts_path,"hosts.backup")    # Create a backup of the hosts file

    def blocking_enable(self, website_list):
        with open(self.hosts_path,'r+') as file:
            content = file.read()
            for website in website_list:
                if website[1] in content:
                    pass
                else:
                    file.write(self.redirect + " " + website[1] + "\n")

    def blocking_disable(self, website_list):
        with open(self.hosts_path,'r+') as file:
            content = file.readlines()      # readlines creates a list where each item is a line of the file
            file.seek(0)
            for line in content:
                if not any(website[1] in line for website in website_list):
                    file.write(line)
            file.truncate()

class BlockTime:
    """Class that compares start and end times, and determines whether or not blocking should be enabled"""

    def __init__(self, start_hour='00', start_min='00', end_hour='01', end_min='00'):
        self.start_time = time(int(start_hour), int(start_min))
        self.end_time = time(int(end_hour), int(end_min))
        self.start_before_end = True

    def updateTimes(self, start_hour, start_min, end_hour, end_min):
        self.start_time = time(int(start_hour), int(start_min))
        self.end_time = time(int(end_hour), int(end_min))

        if self.end_time >= self.start_time:
            self.start_before_end = True
        else:
            self.start_before_end = False

    def checkTime(self):
        time_now = datetime.now().time()
        if self.start_before_end:
            if self.start_time < time_now < self.end_time:
                return True
            else:
                return False
        else:
            if  (time_now > self.start_time) or (time_now < self.end_time):
                return True
            else:
                return False
