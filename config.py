""" Our user configuration class

Responsible for reading and writing to config.ini the uesrname and password
of the user so we can pass it along.

"""
from configparser import ConfigParser
import os
import rumps


# simple bool, self explanatory
def config_file_exists():
    return True if os.path.isfile('config.ini') and os.path.getsize('config.ini') > 0 else False


class Config:
    def __init__(self):
        self.username = None
        self.password = None

    # return user data from our config file
    def get_user_data(self):

        if not config_file_exists():
            self.create_config_file()

        return {'username': self.config_section_map("Login")['username'],
                'password': self.config_section_map("Login")['password']}

    # friendly name for updating user info
    def update_user_info(self):
        self.create_config_file()

    # Our meat!
    def create_config_file(self):
        # reset values in case they're still floating around
        # on the current class instance
        self.username = self.password = None

        config = ConfigParser()

        # capture user login info
        while True:
            window = rumps.Window(message='Enter your username', title='GoToAssist Login', dimensions=(360, 20))

            self.username = window.run().text

            if self.username:
                break

        while True:
            window = rumps.Window(message='Enter your password (password visible when entering)',
                                  title='GoToAssist Login', dimensions=(360, 20))

            self.password = window.run().text

            if self.password:
                break

        # open our config file or create it if it doesn't exist
        file = open('config.ini', 'w+')

        # Empty its contents when doing an update to the file
        file.truncate()

        # create our file sections and store user data
        config.add_section('Login')
        config.set('Login', 'username', self.username)
        config.set('Login', 'password', self.password)
        config.write(file)

        file.close()

    @staticmethod
    def config_section_map(section):
        dict1 = {}
        config = ConfigParser()
        config.read('config.ini')
        options = config.options(section)
        for option in options:
            try:
                dict1[option] = config.get(section, option)
                if dict1[option] == -1:
                    print("skip: %s" % option)
            except:
                print("exception on %s!" % option)
                dict1[option] = None
        return dict1