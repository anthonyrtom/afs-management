from datetime import date, datetime
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.conf import settings
from users.models import CustomUser
from django.core.exceptions import ValidationError


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
        self.full_clean()  # Ensure clean() is called before saving
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


class Client(models.Model):
    name = models.CharField(max_length=150, null=False)
    client_type = models.ForeignKey(
        ClientType, on_delete=models.SET_NULL, null=True, related_name='clients')
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

    def __str__(self):
        return self.name

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
            raise ValueError("Mont can not be blank")
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

    class Meta:
        unique_together = ('client', 'financial_year')
        permissions = [("change_invoice_date", "Can edit the invoice date")]

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
        permissions = [("change_invoice_date", "Can edit the invoice date")]

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
        permissions = [("change_invoice_date", "Can edit the invoice date")]

    def __str__(self):
        return self.client.name
