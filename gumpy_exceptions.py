class NoNetworkConnection(Exception):
    def __init__(self, message="No Network Connection"):

        # Call the base class constructor with the parameters it needs
        super(NoNetworkConnection, self).__init__(message)


class FormSubmissionError(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super(FormSubmissionError, self).__init__(message)


class IncidentsTableNotFound(Exception):
    def __init__(self, message='Incidents table not found!'):

        # Call the base class constructor with the parameters it needs
        super(IncidentsTableNotFound, self).__init__(message)


class GoToAssistBarNotFound(Exception):
    def __init__(self, message='Can\'t find the GoToAssist header. I don\'t know where I am!'):

        # Call the base class constructor with the parameters it needs
        super(GoToAssistBarNotFound, self).__init__(message)


class NoTicketsFoundInTable(Exception):
    def __init__(self, message='Cannot find any tickets'):

        # Call the base class constructor with the parameters it needs
        super(NoTicketsFoundInTable, self).__init__(message)