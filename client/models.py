from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.conf import settings
from users.models import CustomUser


class ClientType(models.Model):
    name = models.CharField(max_length=50, null=False, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.title()
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
        super().save(*args, **kwargs)


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

    def __str__(self):
        return self.name

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
            clients = Client.objects.filter(vat_category__isnull=False)
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

        return clients


class ClientFinancialYear(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    schedule_date = models.DateField(null=True)
    finish_date = models.DateField(null=True)
    wp_done = models.BooleanField(default=False)
    afs_done = models.BooleanField(default=False)
    posting_done = models.BooleanField(default=False)

    class Meta:
        unique_together = ('client', 'financial_year')

    def __str__(self):
        return self.client.name

    def clean(self):
        if self.schedule_date and self.finish_date:
            if self.finish_date < self.schedule_date:
                raise ValidationError(
                    "Finish date must be greater than or equal to schedule date.")


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
            # year_instance = FinancialYear.objects.filter(the_year=year).first()
            month_instance = Month.objects.filter(name=month.title()).first()
            created_client, _ = VatSubmissionHistory.objects.get_or_create(
                client=vat_client, year=year, month=month_instance)
            created_clients.append(created_client)
        return created_clients

    def __str__(self):
        return f"{self.client.name}"
