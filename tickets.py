""" Our tickets class, responsible for obtaining the tickets
    from the HTML table passed """

from gumpy_exceptions import NoTicketsFoundInTable


class Tickets:

    def __init__(self, table):
        self.table = table
        self.total_hots = 0
        self.tickets_by_date = []
        self.tickets = None
        self.find_tickets()

    ''' Finds all tickets from table passed to class.
        Invoked on initialization of class creation '''
    def find_tickets(self):

        # zero out our instance values so that we can call
        # this method when a refresh is needed
        self.total_hots = 0

        try:
            self.tickets = self.table.findAll('tr', class_='clickable-item')
        except:
            raise NoTicketsFoundInTable

        self.sort_tickets_by_date()

    ''' Create our collection of tickets, ordering them by date '''
    def sort_tickets_by_date(self):

        # noinspection PyTypeChecker
        for ticket in self.tickets:

            # lets collect the data for each ticket
            ticket_data = self.extract_ticket_data(ticket)

            # Find HOT tickets
            if ' hot ' in ticket_data['title'].lower():
                self.total_hots += 1

            # Add the ticket to tickets_by_date array and order
            # them by due date by either adding to existing date
            # or creating new date.
            #
            # First pass of the if statement will fail requiring a new entry
            if self.tickets_by_date:

                date_match = False

                # We need to collect all tickets that share the same
                # date
                for d in self.tickets_by_date:

                    # If current ticket date matches an indexed date
                    # group them.
                    if d['date'] == ticket_data['date']:
                        d['tickets'].append(ticket_data)
                        date_match = True
                        break

                # If there was no date matching, create date entry
                if date_match is False:
                    self.tickets_by_date.append({'date': ticket_data['date'], 'tickets': [ticket_data]})

            # First entry
            else:
                self.tickets_by_date.append({'date': ticket_data['date'], 'tickets': [ticket_data]})

    ''' Return total number of tickets found '''
    def total_tickets(self):
        return len(self.tickets) if self.tickets else 0

    ''' Returns an array of tickets if the date passed matches
        one of the dates in our tickets_by_date array, else return
        an empty array '''
    def get_tickets_by_date(self, date):
        for ticket in self.tickets_by_date:
            if ticket['date'] == date:
                return ticket['tickets']

    ''' Parse the HTML of the ticket and gather required details and return dict '''
    @staticmethod
    def extract_ticket_data(ticket):
        title = ticket.find('td', class_='beetil-title').a.string
        _id = ticket.find('td', class_='beetil-id').span.string[1:]
        date = ticket.find('td', class_='beetil-date').span.span.string

        return {'title': title, 'id': _id, 'date': date}