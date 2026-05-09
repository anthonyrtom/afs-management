from __future__ import annotations
from django.utils import timezone
import calendar
from datetime import date, datetime
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.conf import settings
from users.models import CustomUser
from django.core.exceptions import ValidationError
from datetime import time


class ClientType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    def clean(self):
        self.name = self.name.strip().title()
        if ClientType.objects.exclude(id=self.id).filter(name__iexact=self.name).exists():
            raise ValidationError(
                {'name': f'A client type with the name "{self.name}" already exists.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class VatCategory(models.Model):
    vat_category = models.CharField(max_length=10, null=False, unique=True)
    category_descr = models.CharField(max_length=150, null=True)

    class Meta:
        verbose_name_plural = "Vat categories"

    def __str__(self):
        return self.vat_category


class FinancialYear(models.Model):
    the_year = models.IntegerField(
        validators=[MinValueValidator(settings.FIRST_FINANCIAL_YEAR), MaxValueValidator(settings.LAST_FINANCIAL_YEAR)], unique=True)

    def __str__(self):
        return f"{self.the_year}"


class Month(models.Model):
    name = models.CharField(max_length=9, unique=True)

    class Meta:
        verbose_name_plural = "Months"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.title()
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        self.name = self.name.strip().title()
        if Month.objects.exclude(id=self.id).filter(name__iexact=self.name).exists():
            raise ValidationError(
                {'name': f'A month with that name "{self.name}" already exists.'})


class ClientGroup(models.Model):
    name = models.CharField(max_length=150, null=False,
                            blank=False, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.title()
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        self.name = self.name.strip().title()
        if ClientGroup.objects.exclude(id=self.id).filter(name__iexact=self.name).exists():
            raise ValidationError(
                {'name': f'That group already exists-"{self.name}"'})


class Client(models.Model):
    name = models.CharField(max_length=150, null=False)
    client_type = models.ForeignKey(
        ClientType, on_delete=models.SET_NULL, null=True, related_name='clients')
    client_group = models.ForeignKey(
        ClientGroup, on_delete=models.SET_NULL, null=True, related_name='group_clients', blank=True)
    surname = models.CharField(max_length=150, null=True)
    email = models.EmailField(max_length=100, null=True)
    cell_number = models.CharField(max_length=50, null=True)
    contact_person = models.CharField(max_length=150, null=True)
    contact_person_cell = models.CharField(max_length=50, null=True)
    month_end = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)])
    is_active = models.BooleanField(default=False)
    is_sa_resident = models.BooleanField(default=True)
    last_day = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)])
    income_tax_number = models.CharField(max_length=15, null=True, unique=True)
    paye_reg_number = models.CharField(max_length=15, null=True, unique=True)
    first_month_for_paye_sub = models.ForeignKey(
        Month, on_delete=models.SET_NULL, null=True, related_name="paye_clients")
    uif_reg_number = models.CharField(max_length=25, null=True, unique=True)
    entity_reg_number = models.CharField(max_length=25, null=True, unique=True)
    birthday_of_entity = models.DateField(null=True)
    vat_reg_number = models.CharField(max_length=25, null=True, unique=True)
    first_month_for_vat_sub = models.ForeignKey(
        Month, on_delete=models.SET_NULL, null=True, related_name="vat_clients")
    vat_category = models.ForeignKey(
        VatCategory, on_delete=models.SET_NULL, related_name="clients", null=True)
    registered_address = models.CharField(max_length=150, null=True)
    coida_reg_number = models.CharField(max_length=15, null=True, unique=True)
    first_month_for_coida_sub = models.ForeignKey(
        Month, on_delete=models.SET_NULL, null=True, related_name="coida_clients")
    internal_id_number = models.CharField(
        max_length=15, null=True, unique=True)
    uif_dept_reg_number = models.CharField(
        max_length=15, null=True, unique=True)
    accountant = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="clients")
    first_financial_year = models.ForeignKey(
        FinancialYear, on_delete=models.SET_NULL, null=True, related_name="first_fin_year")
    financial_years = models.ManyToManyField(
        FinancialYear, through='ClientFinancialYear', related_name='clients')
    client_service = models.ManyToManyField(
        'Service', through='ClientService', related_name='client_services')

    def clean(self):
        self.name = self.name.strip().upper()
        if self.surname:
            self.surname = self.surname.strip().upper()

    def save(self, *args, **kwargs):
        # self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        permissions = [
            ("update_client", "A User can update client information")]
        ordering = ['name']

    def __str__(self):
        return self.get_client_full_name()

    def get_month_end_as_string(self):
        if not self.month_end:
            return None
        index = self.month_end - 1
        return settings.MONTHS_LIST[index].title()

    def get_client_full_name(self):
        if not self.client_type:
            return self.name
        if self.name and self.surname:
            return self.name + " " + self.surname
        return self.name

    def get_birthday_in_year(self, year):
        curr_date = None
        if not self.is_client_cipc_reg_eligible():
            return curr_date

        if not isinstance(self.month_end, int) or not 1 <= self.month_end <= 12:
            # Handle invalid month_end appropriately (e.g., raise an error, log, return None)
            print(f"Warning: Invalid month_end: {self.month_end}")
            return None

        try:
            curr_date = date(
                year, self.birthday_of_entity.month, self.birthday_of_entity.day)
        except ValueError as e:
            print(e)
            if self.birthday_of_entity.day == 29 and self.month_end == 2:  # Specifically handle Feb 29th
                curr_date = date(year, self.month_end, 28)
            else:
                # Handle other ValueError cases if needed (e.g., log, return None)
                print(
                    f"Warning: Invalid date for year {year}, month {self.month_end}, day {self.birthday_of_entity.day}: {e}")
                pass  # Keep curr_date as None

        return curr_date

    def is_client_cipc_reg_eligible(self):
        if not self.client_type:
            return False
        if self.client_type.name in ["Sole Proprietor", "Individual", "Trust", "Partnership", "Non Profit Organisation", "Foreign Company"]:
            return False
        if not self.entity_reg_number:
            return False
        if len(self.entity_reg_number) != 14:
            return False
        if not self.birthday_of_entity:
            return False
        split_arr = self.entity_reg_number.split("/")
        if len(split_arr[0]) != 4 or len(split_arr[1]) != 6 or len(split_arr[2]) != 2:
            return False
        return True

    def is_afs_client(self, as_at_date=None):
        if self.client_type and self.client_type.name in ["Individual", "Foreign Company", "Partnership"]:
            return False
        if not self.is_active:
            return False
        if not (self.month_end and self.last_day):
            return False
        if not self.first_financial_year:
            return False
        if as_at_date:
            service_name = self.get_service_name("afs")
            try:
                service = Service.objects.get(name=service_name)
                return ClientService.is_service_offered(self.id, service.id, as_at_date)
            except:
                return False
        else:
            return False

    def is_prov_tax_client(self, as_at_date=None):
        if not self.is_active:
            return False
        if self.client_type and self.client_type.name in ["Foreign Company", "Partnership"]:
            return False
        if not (self.month_end and self.last_day):
            return False
        if not self.first_financial_year:
            return False
        if as_at_date:
            service_name = self.get_service_name("prov_tax")
            try:
                service = Service.objects.get(name=service_name)
                return ClientService.is_service_offered(self.id, service.id, as_at_date)
            except:
                return False
        else:
            return False

    def is_first_prov_tax_month(self, as_at_date):
        if not self.is_prov_tax_client(as_at_date):
            return False
        if not isinstance(as_at_date, date):
            raise ValueError("Date required")
        month = as_at_date.month
        prov_tax_month = self.get_first_prov_tax_month()
        return month == prov_tax_month

    def is_second_prov_tax_month(self, as_at_date):
        if not self.is_prov_tax_client(as_at_date):
            return False
        if not isinstance(as_at_date, date):
            raise ValueError(f"{as_at_date} is not a valid date")
        month = as_at_date.month
        return month == self.month_end

    def get_first_prov_tax_month(self):
        if not self.month_end:
            raise ValueError("Month can not be blank")
        if self.month_end < 7:
            return self.month_end + 6
        elif self.month_end <= 12:
            return (self.month_end + 6) % 12

    def get_service_name(self, service_name):
        if service_name == "afs":
            return "Annual Financial Statements"
        elif service_name == "prov_tax":
            return "Provisional Tax"
        return None

    def is_year_after_afs_first(self, year, as_of_date=None):
        if not self.is_afs_client(as_of_date):
            return False
        if int(self.first_financial_year.the_year) > year:
            return False
        return True

    def is_year_after_first_financial_year(self, year):
        if not (self.month_end and self.last_day):
            return False
        if not self.first_financial_year:
            return False

        first_year = self.first_financial_year.the_year

        _, first_year_last_day = calendar.monthrange(
            first_year, self.month_end)
        first_year_end = datetime(
            first_year, self.month_end, first_year_last_day).date()

        _, given_year_last_day = calendar.monthrange(year, self.month_end)
        given_year_end = datetime(
            year, self.month_end, given_year_last_day).date()

        return given_year_end >= first_year_end

    def is_vat_vendor(self, as_at_date, service_name):
        if not self.vat_category:
            return False
        service = Service.objects.filter(name=service_name).first()
        if not service:
            return False
        is_client_service = ClientService.is_service_offered(
            client_id=self.id, service_id=service.id, as_at_date=as_at_date)
        return is_client_service

    @staticmethod
    def get_afs_clients(as_of_date, month=None, client_type=None, filter_q=None):
        clients = []
        try:
            if client_type:
                client_type = ClientType.objects.filter(
                    name=client_type).first()
                clients = Client.objects.filter(client_type=client_type)
            else:
                clients = Client.objects.all()
            if month:
                clients = clients.filter(month_end=month)
            clients = clients.order_by("name")
            if filter_q:
                clients = clients.filter(name__icontains=filter_q)
            clients = [
                client for client in clients if client.is_afs_client(as_of_date)]
            return clients
        except:
            return clients

    @staticmethod
    def get_prov_tax_clients(as_of_date, month=None, client_type=None, filter_q=None):
        clients = []
        try:
            if client_type:
                client_type = ClientType.objects.filter(
                    name=client_type).first()
                clients = Client.objects.filter(client_type=client_type)
            else:
                clients = Client.objects.all()
            if month:
                clients = clients.filter(month_end=month)
            clients = clients.order_by("name")
            if filter_q:
                clients = clients.filter(name__icontains=filter_q)
            clients = [
                client for client in clients if client.is_prov_tax_client(as_of_date)]

            return clients
        except:
            return clients

    @staticmethod
    def get_first_second_prov_tax_clients(as_of_date, month=None, client_type=None, filter_q=None):
        clients = []
        try:
            if client_type:
                client_type = ClientType.objects.filter(
                    name=client_type).first()
                clients = Client.objects.filter(
                    client_type=client_type).order_by("name")
            else:
                clients = Client.objects.all().order_by("name")

            if filter_q:
                clients = clients.filter(name__icontains=filter_q)

            if month:
                clients = [client for client in clients if client.get_first_prov_tax_month(
                    as_of_date) == month or client.month_end == month]
            data = []
            service_id = Service.objects.get(name="Provisional Tax")
            for client in clients:
                if client.is_prov_tax_client(as_of_date):
                    data.append(client)

            return data
        except:
            return clients

    @staticmethod
    def get_vat_clients_for_category(category=None, accountant=None):
        if category:
            category = category.title()
        else:
            return Client.objects.filter(vat_category__isnull=False)

        vat_category = VatCategory.objects.filter(
            vat_category=category).first()
        if not vat_category:
            return Client.objects.filter(vat_category__isnull=False)

        clients = Client.objects.filter(vat_category=vat_category)

        if accountant:
            clients = clients.filter(accountant=accountant)

        return clients

    @staticmethod
    def get_vat_clients_for_month(month=None, accountant=None, filter_q=None):
        clients = []

        if not month or not isinstance(month, str):
            return clients

        month = month.lower()
        if month == "all":
            clients = Client.objects.filter(
                vat_category__isnull=False).order_by("name")
        else:
            index = settings.MONTHS_LIST.index(month) + 1

            if month in ["january", "march", "may", "july", "september", "november"]:
                clients = Client.objects.filter(
                    Q(vat_category__vat_category="A") |
                    Q(vat_category__vat_category="C") |
                    Q(vat_category__vat_category="E", month_end=index)
                )

            elif month in ["february", "august"]:
                clients = Client.objects.filter(
                    Q(vat_category__vat_category="B") |
                    Q(vat_category__vat_category="C") |
                    Q(vat_category__vat_category="D") |
                    Q(vat_category__vat_category="E", month_end=index)
                )

            elif month in ["april", "june", "october", "december"]:
                clients = Client.objects.filter(
                    Q(vat_category__vat_category="B") |
                    Q(vat_category__vat_category="C") |
                    Q(vat_category__vat_category="E", month_end=index)
                )

        if accountant:
            clients = clients.filter(accountant=accountant)
        if clients:
            clients = clients.order_by("name")
        if filter_q:
            clients = clients.filter(name__icontains=filter_q)
        return clients

    @staticmethod
    def count_clients_of_type(the_type=None):
        if not the_type:
            return Client.objects.count()
        if the_type and not isinstance(the_type, str):
            raise ValueError("Wrong type supplied")
        c_type = ClientType.objects.filter(name=the_type).first()
        if not c_type:
            return 0
        return Client.objects.filter(client_type=c_type).count()

    @staticmethod
    def get_clients_of_type(service_name, as_of_date, filter_q=None):
        all_clients = []
        try:
            service = Service.objects.get(name=service_name)
            clients = Client.objects.all().order_by("name")
            if filter_q:
                clients = clients.filter(name__icontains=filter_q)
            for client in clients:
                if ClientService.is_service_offered(client.id, service.id, as_of_date):
                    all_clients.append(client)
        except Service.DoesNotExist:
            return all_clients
        return all_clients


class ClientFinancialYear(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    schedule_date = models.DateField(null=True)
    finish_date = models.DateField(null=True)
    invoice_date = models.DateField(null=True)
    secretarial_start_date = models.DateField(null=True)
    secretarial_finish_date = models.DateField(null=True)
    itr14_start_date = models.DateField(null=True)
    itr14_date = models.DateField(null=True)
    wp_done = models.BooleanField(default=False)
    afs_done = models.BooleanField(default=False)
    posting_done = models.BooleanField(default=False)
    itr34c_issued = models.BooleanField(default=False)
    client_invoiced = models.BooleanField(default=False)
    comment = models.TextField(null=True)
    tax_comment = models.TextField(null=True)
    sec_comment = models.TextField(null=True)
    inv_comment = models.TextField(null=True)
    inv_number = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        unique_together = ('client', 'financial_year')
        ordering = ("client", "financial_year")
        permissions = [("change_invoice_date", "Can edit the invoice date"),
                       ("change_tax_date", "A User can change tax dates on financial statements progress"), ("change_acc_date", "Can change the start and finish date on financial"), ("change_sec_date", "A User can change secretarial date")]

    def __str__(self):
        return self.client.name

    def clean(self):
        if self.schedule_date and self.finish_date:
            if self.finish_date < self.schedule_date:
                raise ValidationError(
                    "Finish date must be greater than or equal to schedule date.")

    @staticmethod
    def setup_clients_afs_for_year(year, as_of_date=datetime.now().date()):
        created_clients = []
        if not isinstance(year, int):
            return created_clients
        all_clients = Client.objects.all().order_by("name")
        for client in all_clients:
            if client.is_afs_client(as_of_date) and client.is_year_after_afs_first(year, datetime.now().date()):
                fin_year = FinancialYear.objects.filter(the_year=year).first()

                if fin_year:
                    curr_client, created = ClientFinancialYear.objects.get_or_create(
                        client=client, financial_year=fin_year
                    )
                    created_clients.append(curr_client)
        return created_clients


class FinancialYearSetup(models.Model):
    financial_year = models.ForeignKey(
        FinancialYear, on_delete=models.SET_NULL, null=True)
    client_type = models.ForeignKey(
        ClientType, on_delete=models.SET_NULL, null=True)
    due_date = models.DateField(null=True)

    def __str__(self):
        return f"{self.financial_year}-{self.client_type.name}-{self.due_date}"

    class Meta:
        unique_together = ["financial_year", "client_type"]
        verbose_name_plural = "Financial years setup"


class VatSubmissionHistory(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, null=False, related_name="vat_client")
    year = models.ForeignKey(
        FinancialYear, on_delete=models.CASCADE, null=False)
    month = models.ForeignKey(Month, on_delete=models.CASCADE, null=False)
    submitted = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    client_notified = models.BooleanField(default=False)
    comment = models.TextField(null=True)
    marked_submitted_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="marked_submitted")
    date_marked_submitted = models.DateTimeField(null=True)
    date_invoiced = models.DateTimeField(null=True)
    marked_paid_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="marked_paid")
    marked_notified_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="marked_notified")

    class Meta:
        unique_together = ['client', 'year', 'month']
        verbose_name_plural = "Vat Submission History"
        permissions = [("change_vat201_status", "A user can change the VAT201 submission status"),
                       ("change_emp_201_invoice_date", "A User can change the invoice dates for VAT201")]

    @staticmethod
    def create_or_get_vat_clients(year, month):
        vat_clients = Client.get_vat_clients_for_month(month=month)
        created_clients = []
        for vat_client in vat_clients:
            month_instance = Month.objects.filter(name=month.title()).first()
            created_client, _ = VatSubmissionHistory.objects.get_or_create(
                client=vat_client, year=year, month=month_instance)
            created_clients.append(created_client)
        return created_clients

    def __str__(self):
        return f"{self.client.name}"


class Service(models.Model):
    name = models.CharField(max_length=150, unique=True, null=False)
    description = models.TextField(null=True)

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        self.name = self.name.title()
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        self.name = self.name.strip().title()
        if Service.objects.exclude(id=self.id).filter(name__iexact=self.name).exists():
            raise ValidationError(
                {'name': f'A service with that name "{self.name}" already exists.'})


class ClientService(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.SET_NULL, null=True, related_name="client_services")
    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, related_name="client_service")
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    comment = models.TextField(null=True)

    class Meta:
        unique_together = ["client", "service"]
        verbose_name_plural = "Client Services"
        permissions = [
            ("change_client_service", "A user can change a client service offering")]

    def __str__(self):
        return f"{self.client.name}-{self.service.name}"

    def clean(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError(
                    "Finish date must be greater than or equal to start date.")

    @staticmethod
    def is_service_offered(client_id, service_id, as_at_date):
        if not isinstance(as_at_date, date):
            raise ValueError("as_at_date must be a valid date")

        try:
            cs = ClientService.objects.get(
                client_id=client_id, service_id=service_id)
        except ClientService.DoesNotExist:
            return False

        if cs.start_date and cs.start_date > as_at_date:
            return False
        if cs.end_date and cs.end_date < as_at_date:
            return False

        return True


class ClientProvisionalTax(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    finish_date = models.DateField(null=True)
    invoice_date = models.DateField(null=True)
    prov_tax_numb = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)])
    comment = models.TextField(null=True)
    marked_finished_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="prov_tax_marked_finished")
    invoiced_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="prov_tax_marked_invoiced")

    class Meta:
        unique_together = ('client', 'financial_year', 'prov_tax_numb')
        permissions = [("change_invoice_date", "Can edit the invoice date"),
                       ("change_irp_date", "A User can change the IRP6 start and finish dates")]

    def __str__(self):
        return self.client.name


class ClientCipcReturnHistory(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    finish_date = models.DateField(null=True)
    invoice_date = models.DateField(null=True)
    comment = models.TextField(null=True)
    marked_finished_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="cipc_marked_finished")
    invoiced_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="cipc_marked_invoiced")

    class Meta:
        unique_together = ('client', 'financial_year')
        permissions = [("change_invoice_date", "Can edit the invoice date of a CIPC return"),
                       ("change_return_date", "A User can change the return date on the app")]

    def __str__(self):
        return self.client.name


"""
Starting new class for project managent to simplify the project management
A lot of the models above will become redudanct when this becomes live and successful
"""


class RecurringType(models.Model):
    recurring_type_name = models.CharField(
        max_length=20, unique=True, blank=False)

    def __str__(self):
        return self.recurring_type_name


class Event(models.Model):
    description = models.CharField(max_length=150, null=True, blank=True)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=True)
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    is_all_day_event = models.BooleanField(null=False, default=True)
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="user_events")
    is_recurring = models.BooleanField(null=False, default=False)
    created_date = models.DateTimeField(null=False, auto_now_add=True)
    client_service = models.ForeignKey(
        ClientService, on_delete=models.SET_NULL, related_name="client_service_events", null=True)
    parent_event = models.ForeignKey(
        "self", null=True, on_delete=models.SET_NULL, related_name="child_events")

    def __str__(self):
        client_service_name = "not a client service"
        if self.client_service:
            client_service_name = self.client_service.client.get_client_full_name + \
                " " + self.client_service.service.name
        return f"{self.start_date}-{self.is_all_day_event}-{self.created_by}-{self.created_date}-{client_service_name}"

    def has_event_end_date_passed(self, test_date):
        """Return True if the given date is after this event's end_date."""
        if isinstance(test_date, datetime):
            test_date = test_date.date()
        if not isinstance(test_date, date):
            raise ValueError("test_date must be a date or datetime instance.")
        if self.end_date:
            return test_date > self.end_date
        return False

    def is_active(self):
        """Return True if today falls within the event's date range."""
        today = timezone.now().date()
        if today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        return True

    def get_child_exceptions(self):
        """Return all exception/rescheduled instances branching from this event."""
        return self.child_events.all()

    def get_recurring_pattern(self):
        """Return the RecurringEvent pattern, or None for non-recurring events."""
        return self.recurring_events.first()

    def clean(self):
        errors = {}

        if self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "End date cannot be before start date."

        if self.is_all_day_event:
            if self.start_time or self.end_time:
                errors["start_time"] = (
                    "Start/end times must be empty for all-day events."
                )
        else:
            if not self.start_time:
                errors["start_time"] = (
                    "Start time is required for non-all-day events."
                )
            if not self.end_time:
                errors["end_time"] = (
                    "End time is required for non-all-day events."
                )
            if (
                self.start_time
                and self.end_time
                and self.start_date == self.end_date
                and self.end_time <= self.start_time
            ):
                errors["end_time"] = (
                    "End time must be after start time on the same day."
                )

        if not self.is_recurring and self.parent_event:
            pass

        if errors:
            raise ValidationError(errors)

    @classmethod
    def create_normal_event(cls, start_date, user, start_time=None, end_time=None, is_all_day_event=False):
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        elif start_date is None:
            raise TypeError(
                "Start date must be either datetime object or date")
        if start_time is None and is_all_day_event is None:
            raise ValueError(
                "Both start time and is_all_day_event can not be null")
        if start_time and not end_time:
            raise ValueError("You need end time")
        if start_time is not None and end_time is not None:
            if not isinstance(start_time, time) or not isinstance(end_time, time):
                raise TypeError(
                    "start_time and end_time must be datetime.time instances")

            if start_time > end_time:
                raise ValueError("Your start time is ahead of end time")
        if not start_time:
            is_all_day_event = True
        return cls.objects.create(start_date=start_date, created_by=user, start_time=start_time,
                                  end_time=end_time, is_all_day_event=is_all_day_event)


class RecurringEvent(models.Model):
    event = models.ForeignKey(
        Event, null=False, on_delete=models.CASCADE, related_name="recurring_events")
    recurring_type = models.ForeignKey(
        RecurringType, null=False, on_delete=models.CASCADE, related_name="all_recurring_events")
    separation_count = models.IntegerField(
        default=0, validators=[MinValueValidator(0)])
    max_numb_occurances = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)]
    )

    day_of_week = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )
    week_of_month = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(-4), MaxValueValidator(4)]
    )
    day_of_month = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(-31), MaxValueValidator(31)]
    )
    month_of_year = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

    def __str__(self):
        return f"{self.event}-{self.recurring_type.recurring_type_name}"

    def get_recurring_type_name(self):
        return self.recurring_type.recurring_type_name

    def clean(self):
        errors = {}
        rtype = self.get_recurring_type_name().lower()

        if self.event_id and not self.event.is_recurring:
            errors["event"] = (
                "The linked Event must have is_recurring=True."
            )
        if rtype == "weekly":
            if self.day_of_week is None:
                errors["day_of_week"] = (
                    "day_of_week is required for weekly recurrence."
                )

        elif rtype == "monthly":
            has_day_of_month = self.day_of_month is not None
            has_week_day = (
                self.week_of_month is not None and self.day_of_week is not None
            )
            if not has_day_of_month and not has_week_day:
                errors["day_of_month"] = (
                    "Monthly recurrence requires either day_of_month "
                    "or both week_of_month and day_of_week."
                )

        elif rtype == "yearly":
            if self.month_of_year is None:
                errors["month_of_year"] = (
                    "month_of_year is required for yearly recurrence."
                )
            if self.day_of_month is None:
                errors["day_of_month"] = (
                    "day_of_month is required for yearly recurrence."
                )

        event_has_end = self.event_id and self.event.end_date
        if not event_has_end and not self.max_numb_occurances:
            errors["max_numb_occurances"] = (
                "Provide either an end_date on the Event or "
                "max_numb_occurances to bound the recurrence."
            )

        if errors:
            raise ValidationError(errors)


class ProjectOccurence(models.Model):
    """
    One concrete instance of an Event.

    For non-recurring events: one row is created automatically (via signal
    or overridden save()) when the Event is saved.
    For recurring events: one row per generated occurrence date.

    Completion is gated by compulsory OccurrenceStageCompletion rows.
    """

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        RESCHEDULED = "rescheduled", "Rescheduled"
        MISSED = "missed", "Missed"

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="project_recurring_events"
    )
    original_date = models.DateField()
    original_start_time = models.TimeField(null=True, blank=True)

    rescheduled_date = models.DateField(null=True, blank=True)
    rescheduled_start_time = models.TimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )
    completed_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="completed_occurrences"
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "original_date")
        ordering = ["original_date"]

    def __str__(self):
        return f"{self.event} on {self.original_date} [{self.status}]"

    @property
    def effective_date(self):
        return self.rescheduled_date or self.original_date

    @property
    def effective_end_date(self):
        if self.event.end_date:
            return self.event.end_date

        return None

    def get_compulsory_incomplete_stages(self):
        """Return any compulsory stages not yet completed for this occurrence."""
        qs = ProjectStageCompletion.get_incomplete_stages(self.id, False)
        return qs

    def get_all_incomplete_stages(self):
        """Return all imcomplete stages not yet completed for this occurrence."""
        qs = ProjectStageCompletion.get_incomplete_stages(self.id, True)
        return qs

    def get_completion_summary(self):
        """
        Returns a dict useful for progress indicators in the UI.
        e.g. {"total": 4, "completed": 2, "compulsory_incomplete": 1}
        """
        stages = self.project_occurence_completion.all()
        total = stages.count()
        completed = stages.filter(is_stage_complete=False).count()
        compulsory_incomplete = self.get_compulsory_incomplete_stages().count()
        return {
            "total": total,
            "completed": completed,
            "compulsory_incomplete": compulsory_incomplete,
            "percent_complete": round((completed / total) * 100) if total else 0,
        }

    def clean(self):
        errors = {}

        if self.status == self.Status.RESCHEDULED and not self.rescheduled_date:
            errors["rescheduled_date"] = (
                "A rescheduled_date is required when status is 'rescheduled'."
            )

        if self.status == self.Status.COMPLETED:
            if not self.completed_by:
                errors["completed_by"] = (
                    "completed_by is required when marking an occurrence complete."
                )
            if not self.completed_at:
                errors["completed_at"] = (
                    "completed_at is required when marking an occurrence complete."
                )
            if self.pk:
                incomplete = self.get_compulsory_incomplete_stages()
                if incomplete.exists():
                    names = ", ".join(
                        incomplete.values_list("name", flat=True)
                    )
                    errors["status"] = (
                        f"Cannot mark complete — the following compulsory "
                        f"stages are unfinished: {names}."
                    )

        if errors:
            raise ValidationError(errors)

    def mark_complete(self, user):
        """Attempt to mark this occurrence complete. Raises ValidationError if
        compulsory stages are unfinished."""
        self.status = self.Status.COMPLETED
        self.completed_by = user
        self.completed_at = timezone.now()
        self.full_clean()
        self.save()

    def reschedule(self, new_date, new_start_time=None):
        if self.effective_end_date and new_date > self.effective_end_date:
            raise ValidationError(
                "Cannot reschedule to a date earlier than the end date."
            )
        if self.has_number_occurences_reached_limit():
            raise ValidationError(
                "Cannot reschedule, the maximum number of runs has been reached."
            )
        self.rescheduled_date = new_date
        self.rescheduled_start_time = new_start_time
        self.status = self.Status.RESCHEDULED
        self.full_clean()
        self.save()

    def has_number_occurences_reached_limit(self):
        if self.effective_end_date:
            return False
        if not self.event.is_recurring:
            return False
        recur_instance = RecurringEvent.objects.filter(
            event_id=self.event.id).first()
        if not recur_instance.max_numb_occurances:
            return False
        all_instances_count = ProjectOccurence.objects.filter(
            event=self.event).count()
        return all_instances_count >= recur_instance.max_numb_occurances


class Stage(models.Model):
    stage_name = models.CharField(
        max_length=100, unique=True, blank=False)

    def __str__(self):
        return self.stage_name

    def save(self, *args, **kwargs):
        self.stage_name = self.stage_name.title()
        super().save(*args, **kwargs)


class ProjectStage(models.Model):
    stage = models.ForeignKey(
        Stage, on_delete=models.SET_NULL, null=True, related_name="project_stages")
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, null=False, blank=False, related_name="event_project_stages")
    is_stage_compulsory = models.BooleanField(null=False, default=True)
    assigned_to = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="user_project_stages")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("stage", "event")
        ordering = ("event", "stage")

    def __str__(self):
        return f"stage-{self.stage}-event-{self.event}"


class ProjectStageCompletion(models.Model):
    project_occurence = models.ForeignKey(
        ProjectOccurence, on_delete=models.CASCADE, null=False, related_name="project_occurence_completion")
    project_stage = models.ForeignKey(
        ProjectStage, on_delete=models.CASCADE, null=False, related_name="project_stage_completion")
    is_stage_complete = models.BooleanField(null=False, default=False)
    completed_at = models.DateTimeField(auto_now_add=True)
    is_stage_compulsory = models.BooleanField(null=False, default=True)

    class Meta:
        unique_together = ("project_occurence", "project_stage")
        ordering = ("project_occurence", "project_stage")

    def mark_stage_complete(self):
        if not self.is_stage_complete:
            self.is_stage_complete = True
            self.save()
            return True
        return False

    def mark_stage_incomplete(self):
        if self.is_stage_complete:
            self.is_stage_complete = False
            self.save()
            return True
        return False

    def __str__(self):
        return f"project-{self.project_occurence}-project_stage-{self.project_stage}-status-{self.is_stage_complete}"

    @staticmethod
    def get_complete_stages(project_occurence_id):
        qs = ProjectStageCompletion.objects.filter(
            project_occurence=project_occurence_id,
            is_stage_complete=True
        )
        return qs

    @staticmethod
    def get_incomplete_stages(project_occurence_id, include_non_compulsory=True):
        """
        Given an project_occurence_id, get all of its stages that have
        is_stage_complete = False and include_non_compulsory will include stages that are not compulsory
        return a list of all instances
        """
        qs = ProjectStageCompletion.objects.filter(
            project_occurence=project_occurence_id,
            is_stage_complete=False
        )

        if not include_non_compulsory:
            qs = qs.filter(is_stage_compulsory=True)

        return qs
