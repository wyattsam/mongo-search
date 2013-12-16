from scrapers import JSONScraper

class ProfilesScraper(JSONScraper):
    NAME = 'profiles'
    API_BASE = 'https://corp.mongodb.com/api/'
    EMPLOYEE_URL = API_BASE + 'employee'

    def __init__(self, credentials):
        self.credentials = credentials

    def scrape_employee(self, employee):
        employee_id = employee['uri'].partition('/api/employee/')[2]
        employee['crowd_id'] = employee_id
        employee['_id'] = 'employee-' + employee_id
        employee['full_name'] = ' '.join(
            [employee['first_name'], employee['last_name']])
        print '[PROFILE] ' + employee['full_name']
        return employee

    def scrape(self):
        params = {'expand': 'team'}
        result = self.get_json(self.EMPLOYEE_URL, params=params,
            auth=self.credentials, digest=True)

        for employee in result['employees']:
            yield self.scrape_employee(employee)


if __name__ == '__main__':
    import settings
    from scrapers import ScrapeRunner
    runner = ScrapeRunner(**settings.MONGO)
    scraper = ProfilesScraper(**settings.PROFILES)
    runner.run(scraper, remove=True)
