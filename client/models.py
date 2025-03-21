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
    name = models.CharField(max_length=150, null=False, unique=True)
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
    uif_reg_number = models.CharField(max_length=15, null=True, unique=True)
    entity_reg_number = models.CharField(max_length=15, null=True, unique=True)
    vat_reg_number = models.CharField(max_length=15, null=True, unique=True)
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

    def is_afs_client(self):
        if self.client_type and self.client_type.name == "Individual":
            return False
        if not self.is_active:
            return False
        if not (self.month_end and self.last_day):
            return False
        if not self.first_financial_year:
            return False
        return True

    def is_year_after_afs_first(self, year):
        if not self.is_afs_client():
            return False
        if int(self.first_financial_year.the_year) > year:
            return False
        return True

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
    def get_vat_clients_for_month(month=None, accountant=None):
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
        clients = clients.order_by("name")
        return clients


class ClientFinancialYear(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    schedule_date = models.DateField(null=True)
    finish_date = models.DateField(null=True)
    wp_done = models.BooleanField(default=False)
    afs_done = models.BooleanField(default=False)
    posting_done = models.BooleanField(default=False)
    itr34c_issued = models.BooleanField(default=False)
    client_invoiced = models.BooleanField(default=False)
    comment = models.TextField(null=True)

    class Meta:
        unique_together = ('client', 'financial_year')

    def __str__(self):
        return self.client.name

    def clean(self):
        if self.schedule_date and self.finish_date:
            if self.finish_date < self.schedule_date:
                raise ValidationError(
                    "Finish date must be greater than or equal to schedule date.")

    @staticmethod
    def setup_clients_afs_for_year(year):
        created_clients = []
        if not isinstance(year, int):
            return created_clients
        all_clients = Client.objects.all().order_by("name")
        for client in all_clients:
            if client.is_afs_client() and client.is_year_after_afs_first(year):
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
