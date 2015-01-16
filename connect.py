"""
    Our connection class for logging into GoToAssist
    and returning our incidents table
"""

from mechanicalsoup import Browser
from connections_helper import behind_proxy, is_connected, test_connection
from config import Config
from gumpy_exceptions import FormSubmissionError, IncidentsTableNotFound, GoToAssistBarNotFound

config = Config()


class Connect:

    def __init__(self):
        # Get our user data from configuration
        self._connected = False
        self.username = self.password = None

        # create our virtual browser
        self.browser = Browser2()

        # Default proxy bool value but verified again when connect() is invoked.
        self._behind_proxy = True

    @property
    def connected(self):
        """ Connected is set when pinging google is successful
            during behind_proxy method call """
        return self._connected

    @property
    def behind_proxy(self):
        return self._behind_proxy

    ''' Our main connect method to connect to our service (GoToAssist) '''
    def connect(self):

        print("calling connect")
        
        self.username = config.get_user_data()['username']
        self.password = config.get_user_data()['password']

        # Are we behind a proxy?
        try:
            self._behind_proxy = behind_proxy()
        except:
            # send exception message back to caller
            raise

        # Response object of our url
        login_page = self.browser.get(ConnProps.LOGIN_URL, proxies=ConnProps.PROXY_DICT) if self._behind_proxy \
            else self.browser.get(ConnProps.LOGIN_URL)

        # login_page.soup is a BeautifulSoup object http://www.crummy.com/software/BeautifulSoup/bs4/doc/#beautifulsoup
        # now grab the login form
        login_form = login_page.soup.form

        # specify username and password to inject into the page's form
        login_form.select("#emailAddress")[0]['value'] = self.username
        login_form.select("#password")[0]['value'] = self.password

        print("before form submit")

        # submit the login form
        page2 = self.browser.submit(login_form, ConnProps.LOGIN_URL, proxies=ConnProps.PROXY_DICT) \
            if self._behind_proxy else self.browser.submit(login_form, ConnProps.LOGIN_URL)

        # After submitting the form, lets see if there are any errors.
        # This is reliant on the finding of an error banner on the GoToAssist side.
        # Most likely, incorrect credentials.
        error_banner = page2.soup.select('#credentials.errors')[0] if page2.soup.select('#credentials.errors') \
            else None

        # If ones email address is of an incorrect format, the error shows up as an inline
        # div and not from a banner message so we have to handle it differently.
        error_email = page2.soup.find('div', class_='inline-error')

        print("after form submit")

        if error_banner:
            self._connected = False
            raise FormSubmissionError(error_banner.text)

        elif error_email:
            self._connected = False
            raise FormSubmissionError('Not a valid email address. Please update your settings')

        # verify we are logged in (thanks to cookies) as we browse the rest of the site!
        # Lets start by grabbing a dom element specific to GTA to make sure we're where we should be
        elif not page2.soup.find('div', class_='gotoassist-bar'):
            self._connected = False
            raise GoToAssistBarNotFound
        else:
            self._connected = True

    ''' Lets attempt to obtain our table of tickets '''
    def get_incidents_table(self):

        # lets head over to the iDev team's incidents page and grab those tickets!
        incidents_page = self.browser.get(ConnProps.INCIDENTS_URL, proxies=ConnProps.PROXY_DICT) if self._behind_proxy \
            else self.browser.get(ConnProps.INCIDENTS_URL)

        # grab the table by its id
        incidents_table = incidents_page.soup.select("#incident-table")

        if incidents_table:
            return incidents_table[0]
        else:
            raise IncidentsTableNotFound


class Browser2(Browser):
    # @OVERRIDE
    # The submit method of Browser.submit from mechanicalsoup does not
    # accept kwargs. As such, our proxy settings do not get passed correctly thus
    # causing error. We must overide the method with our own version.
    def submit(self, form, url=None, **kwargs):
        request = self._prepare_request(form, url)
        response = self.session.send(request, **kwargs)
        Browser.add_soup(response)
        return response


class ConnProps:
    # The initial page to load. This is our login page.
    # This can be overridden when creating your an instance of Connect
    LOGIN_URL = "https://login.citrixonline.com/login?service=https%3A%2F%2Fdesk.gotoassist.com%2Fauth%2Fcas%2Fcallback%3Furl"

    # After successful login, we want to route to the iDev incidents page
    # This can be overridden when creating your an instance of Connect
    INCIDENTS_URL = "https://desk.gotoassist.com/incidents?user_id=4278194272"

    # Our proxy settings that will be set if our connection deems we are
    # behind the Nord network. This can be overridden when creating your
    # an instance of Connect
    PROXY_DICT = {
        "http": "webproxy.nordstrom.net:8181",
        "https": "webproxy.nordstrom.net:8181",
        "ftp": "webproxy.nordstrom.net:8181"
    }