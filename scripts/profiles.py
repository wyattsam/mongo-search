from scrapers import JSONScraper


class ProfilesScraper(JSONScraper):
    NAME = 'profiles'
    API_BASE = 'https://corp.10gen.com/api/'
    EMPLOYEE_URL = API_BASE + 'employee'

    def __init__(self, credentials):
        self.credentials = credentials

    def scrape_employee(self, employee):
        employee_id = employee['uri'].strip('/api/employee/')
        employee['_id'] = 'employee-' + employee_id
        return employee

    def scrape(self):
        params = {'expand': 'team'}
        result = self.get_json(self.EMPLOYEE_URL, params=params,
            auth=self.credentials, digest=True)

        for employee in result['employees']:
            yield self.scrape_employee(employee)
