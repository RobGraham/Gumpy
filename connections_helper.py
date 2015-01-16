from socket import AF_INET, SOCK_DGRAM, socket, gaierror
from gumpy_exceptions import NoNetworkConnection

# Our local machines on the Nordstrom network start with 10.xxx ip's
# return true if on nord network
def behind_proxy():

    # get our socket object
    s = socket(AF_INET, SOCK_DGRAM)

    try:
        s.connect(('google.com', 80))
        # crude way of doing it but seemed to be the only working
        # code to get local ip info.
        ip = s.getsockname()[0]

        # Does it start with 10. ?
        return ip[:3] == "10."
    except gaierror:
        raise NoNetworkConnection



def is_connected():
    # get our socket object
    s = socket(AF_INET, SOCK_DGRAM)

    # crude way of doing it but seemed to be the only working
    # code to get local ip info.
    try:
        s.connect(('google.com', 80))
        return True
    except:
        return False


def test_connection():
    # get our socket object
    s = socket(AF_INET, SOCK_DGRAM)

    # crude way of doing it but seemed to be the only working
    # code to get local ip info.
    try:
        s.connect(('google.com', 80))
        return True
    except gaierror:
        raise NoNetworkConnection