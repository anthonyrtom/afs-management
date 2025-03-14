from django.core.management.base import BaseCommand
from django.conf import settings
import datetime
from client.models import VatCategory, ClientType, FinancialYear, Month
from users.models import JobTitle


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        self.populate_client_type()
        self.populate_vat_category()
        self.populate_financial_year()
        self.populate_month()
        self.populate_job_title()

    def populate_client_type(self):
        client_type_list = ["Close Corporation", "Sole Proprietor", "Individual", "Trust",
                            "Private Company", "Public Company", "Partnership", "Non Profit Organisation", "Non Profit Company", "Incoporation", "Foreign Company"]
        for client_type in client_type_list:
            ct = ClientType.objects.get_or_create(name=client_type)

    def populate_vat_category(self):
        vat_category_list = [("A", "Submit every two months ending Jan, March, May, July, Sept and Nov"), (
            "B", "Submit every two months ending Feb, Apr, Jun, Aug, Oct and Dec"), ("C", "Submit every month"), ("D", "Submit one return for every 6 calendar months, ending on the last day of February and August"), ("E", "Submit one return for every 12 months, ending on the last day of the vendor's year of assessment")]

        for vat_category in vat_category_list:
            vc = VatCategory.objects.get_or_create(
                vat_category=vat_category[0], category_descr=vat_category[1])

    def populate_financial_year(self):
        min_year = settings.FIRST_FINANCIAL_YEAR
        max_year = datetime.datetime.now().year + 1
        years = list(range(min_year, max_year))
        for year in years:
            fin_year = FinancialYear.objects.get_or_create(the_year=year)

    def populate_month(self):
        months = settings.MONTHS_LIST
        for month in months:
            month_instance = Month.objects.get_or_create(name=month)

    def populate_job_title(self):
        job_titles = [("Accountant", "Normal Accountant"), ("Tax Clerk", "Normal tax clerk"),
                      ("Tax Manager", "Leader of tax"), ("Accounting Manager", "Manager below director")]
        for job_title in job_titles:
            jt = JobTitle.objects.get_or_create(
                title=job_title[0], description=job_title[1])
