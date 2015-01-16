"""Gumpy
The legacy content dev's friend!

Gumpy is a scraper tool that gives developers an overview of total
tickets to be completed on a per due date basis or total tickets collectively.

"""

__author__ = "Rob Graham (rfgraham85@gmail.com)"
__version__ = "1.0"
__copyright__ = "Copyright (c) 2004-9999 Rob Graham"
__license__ = "MIT"

__all__ = ['Gumpy']

import rumps
from connect import Connect
from tickets import Tickets
from config import Config
from gumpy_exceptions import NoNetworkConnection, NoTicketsFoundInTable


class Gumpy(rumps.App):

    def __init__(self):
        super(Gumpy, self).__init__(GumpyTitles.GUMPY)
        self.refresh_interval_minutes = 600  # 10 minutes default
        self.refresh_interval_timer = None
        self.refresh_interval_menu_item = None
        self.tickets = None
        self.connection = None
        self.connection_thread = None
        self.create_menu(first_pass=True)
        self.connect_thread()

    def menu_update_settings(self, _):
        """ @MenuAction - Request user update their id/password """
        Config().update_user_info()

    def menu_refresh_tickets(self, _):
        """ @MenuAction - Request new tickets """
        self.refresh_interval_thread(force_refresh=True)

    def menu_connect(self, _):
        """ @MenuAction - Attempt to connect by initiating the connection thread """
        self.connect_thread()

    def menu_quit(self, _):
        """ @MenuAction - Quit app """
        rumps.quit_application()

    """
    Menu Callback. Set our refresh interval to automatically gather updates.
    Unfortunately MenuItem's callback doesn't support passed args so we have to
    create multiple methods to do one simple task unfortunately
    """
    def menu_set_refresh_interval_5(self, item):
        """ :param item: the MenuItem that was clicked is passed as part of its callback """
        self.menu_interval_selected_state_update(time=300, menu_item=item)  # 5 minutes

    def menu_set_refresh_interval_10(self, item):
        self.menu_interval_selected_state_update(time=600, menu_item=item)  # 10 minutes

    def menu_set_refresh_interval_15(self, item):
        self.menu_interval_selected_state_update(time=900, menu_item=item)  # 15 minutes

    def menu_set_refresh_interval_30(self, item):
        self.menu_interval_selected_state_update(time=1800, menu_item=item)  # 30 minutes

    def menu_set_refresh_interval_60(self, item):
        self.menu_interval_selected_state_update(time=3600, menu_item=item)  # 60 minutes

    def menu_set_refresh_interval_off(self, item):
        self.menu_interval_selected_state_update(time=0, menu_item=item)  # turn off

    def menu_interval_selected_state_update(self, time, menu_item):
        """ Update the local refresh interval's time which the refresh interval
            thread uses.

            This method is called when any of the 'Refresh Time' submenu items are clicked
            and their time values are passed.

            :param time: the new time that the refresh thread should use
            :param menu_item: the MenuItem that was clicked """
        self.refresh_interval_minutes = time
        self.refresh_interval_menu_item = menu_item

        # If 0 is passed we know the intention is to turn off the refresh interval
        if time is not 0:
            self.refresh_interval_thread(force_refresh=True)
            rumps.notification(GumpyTitles.INTERVAL_SET, '', str(round(self.refresh_interval_minutes / 60)) + ' minutes')
        else:
            self.refresh_interval_thread(stop=True)
            rumps.notification(GumpyTitles.INTERVAL_SET, '', 'Turned Off')

    def set_menu_interval_selected_state(self):
        """ Once the user has selected the refresh interval in the menu
            we can leverage the OS menu state and provide a checkmark.

            First we have to get the parent MenuItem which contains the
            collection of submenu MenuItems that need to change states.
        """
        refresh_time = self.menu.get('Refresh Time')

        if self.refresh_interval_menu_item is not None:
            # Because the menu gets cleared when new menu states need to be made,
            # reference_interval_menu_item will be referencing an old menu item in
            # memory no longer in the menu. Lets get the newest reference by using
            # the title of the original menu item.
            item = refresh_time.get(self.refresh_interval_menu_item.title)

            for i in refresh_time:
                if i == item.title:
                    item.state = 1
                else:
                    # Reset the states of all other MenuItems
                    refresh_time.get(i).state = 0

    def create_menu(self, first_pass=False):
        """ Create the menu options """

        print('calling menu')

        # Each time the user refreshes ticket results, our
        # menu will need to update, so lets clear the menu options
        self.menu.clear()

        menu = []

        # If we have tickets stored, add them to the menu first
        if self.tickets and self.tickets.tickets_by_date:
            for t in self.tickets.tickets_by_date:
                title = t['date'] + ": " + str(len(t['tickets']))
                menu.append(rumps.MenuItem(title))

        # process to create separator
        menu.append(None)

        # User settings/options
        menu.append(rumps.MenuItem('Update User Settings', callback=self.menu_update_settings))
        menu.append(rumps.MenuItem('Refresh Results', callback=self.menu_refresh_tickets))

        # setup a submenu for users to select when they want Gumpy to auto refresh
        # ticket results
        refresh_interval_menu_items = rumps.MenuItem('Refresh Time')
        refresh_interval_menu_items.add(rumps.MenuItem('5 minutes', callback=self.menu_set_refresh_interval_5))
        refresh_interval_menu_items.add(rumps.MenuItem('10 minutes', callback=self.menu_set_refresh_interval_10))
        refresh_interval_menu_items.add(rumps.MenuItem('15 minutes', callback=self.menu_set_refresh_interval_15))
        refresh_interval_menu_items.add(rumps.MenuItem('30 minutes', callback=self.menu_set_refresh_interval_30))
        refresh_interval_menu_items.add(rumps.MenuItem('60 minutes', callback=self.menu_set_refresh_interval_60))
        refresh_interval_menu_items.add(rumps.MenuItem('Turn Off', callback=self.menu_set_refresh_interval_off))

        menu.append(refresh_interval_menu_items)

        menu.append(rumps.MenuItem('Connect', callback=self.menu_connect))

        # rumps automatically adds Quit to the menu AFTER we've appended our items.
        # However, when we use self.menu.clear(), it clears Quit also so we have to
        # add it again.
        if not first_pass and not self.menu.get('Quit'):
            menu.append(rumps.MenuItem('Quit', callback=self.menu_quit))

        # Force menu update
        self.menu.update(menu)

        # After the menu has been updated with the new values, lets ensure that
        # the selected state of the refresh interval submenu is set
        if self.refresh_interval_menu_item is None:
            self.refresh_interval_menu_item = self.menu.get('Refresh Time').get('10 minutes')

        self.set_menu_interval_selected_state()

    def get_tickets(self, first_pass=True):

        """ Gather our collection of tickets if successful so that
        we may add their data to our menu """

        print('getting tickets')

        self.title = GumpyTitles.FETCHING

        if self.connection and self.connection.connected:

            table = self.connection.get_incidents_table()

            try:
                tickets = Tickets(table)

                # After passing the table to our Tickets constructor,
                # if everything went according to plan, we should have > 0 tickets
                if tickets.total_tickets():
                    self.tickets = tickets

                    # set the app title
                    self.title = GumpyTitles.GUMPY + ' - Hots: ' + str(tickets.total_hots) \
                        if tickets.total_hots else GumpyTitles.GUMPY
                else:
                    rumps.alert(NoTicketsFoundInTable())

            except Exception as e:
                rumps.alert(e)

        # This ensures we don't show an alert twice when the app starts but only
        # when the user requests that the results be refreshed.
        elif not first_pass:
            rumps.alert(NoNetworkConnection())

        self.title = GumpyTitles.GUMPY

        # After we've sucessfully obtained our tickets, we must update
        # the menu to reflect.
        self.create_menu()

    def connect(self, *args):

        """ Called via our connect thread...

        Attempt to create a new connection with our Connect
        class and store the value to our self.connection instance variable """

        # With the potential dropped internet connections, sessions ending and more,
        # which have caused errors, it's easier and safer if we attempt to create a
        # new instance of Connect which provides a clean session. Future improvements
        # could be made to rectify this action to help memory/performance.
        self.connection = Connect()
        self.title = GumpyTitles.CONNECTING

        try:
            self.connection.connect()
            rumps.notification(GumpyTitles.CONNECTION_SUCCESS, '', 'Have a cookie')

            # This explicitly calls get_tickets method on a rumps.Timer (new thread) interval
            if self.refresh_interval_timer is None:
                self.refresh_interval_thread()
            else:
                # If this isn't the first time connect is being called, we will update
                # our ticket results by refreshing our interval thread which calls get_tickets
                self.refresh_interval_thread(force_refresh=True)

        except Exception as e:
            rumps.alert(e)
        finally:
            self.title = GumpyTitles.GUMPY

    def refresh_interval_thread(self, force_refresh=False, stop=False):
        """ Our interval Timer (thread) which will request our tickets
            after a specified time """

        if self.refresh_interval_timer is not None:
            if stop:
                self.refresh_interval_timer.stop()
                return
            elif force_refresh:
                self.refresh_interval_timer.stop()

        # new Timer with callback and time
        self.refresh_interval_timer = rumps.Timer(self.get_tickets, self.refresh_interval_minutes)
        self.refresh_interval_timer.start()

    def connect_thread(self):
        """ Our connection thread which we'll create by using rumps.Timer
            since it ties into NS threading and saves me the hassle.

            This method is responsible for calling our connect method. By
            doing this on a thread, we free up the applications start time
            because of the long time it takes for connection and login of
            GoToAssist session to take place """

        # When user clicks Connect in the app menu, lets stop the previous
        # interval so we can start it again.
        if self.connection_thread is not None:
            self.connection_thread.stop()
        else:
            # callback and interval, set in the distant future since we don't
            # need to automatically call connect again unless the user requests it
            self.connection_thread = rumps.Timer(self.connect, 10000)

        self.connection_thread.start()

class GumpyTitles:
    GUMPY = 'Gumpy'
    CONNECTING = 'Gumpy Connecting...'
    FETCHING = 'Gumpy Fetching...'
    CONNECTION_SUCCESS = 'Gumpy: Connection Successful'
    INTERVAL_SET = 'Gumpy refresh interval set to'