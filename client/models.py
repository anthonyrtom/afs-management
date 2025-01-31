from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import CustomUser


class ClientType(models.Model):
    name = models.CharField(max_length=50, null=False, unique=True)

    def __str__(self):
        return self.name


class VatCategories(models.Model):
    vat_category = models.CharField(max_length=10, null=False, unique=True)
    category_descr = models.CharField(max_length=150, null=True)

    def __str__(self):
        return self.vat_category


class FinancialYear(models.Model):
    the_year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(9999)], unique=True)

    def __str__(self):
        return f"{self.the_year}"


class Client(models.Model):
    name = models.CharField(max_length=150, null=False)
    client_type = models.ForeignKey(
        ClientType, on_delete=models.SET_NULL, null=True, related_name='clients')
    surname = models.CharField(max_length=150, null=True)
    month_end = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)])
    last_day = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)])
    income_tax_number = models.CharField(max_length=15, null=True)
    paye_reg_number = models.CharField(max_length=15, null=True)
    uif_reg_number = models.CharField(max_length=15, null=True)
    cipc_reg_number = models.CharField(max_length=15, null=True)
    vat_reg_number = models.CharField(max_length=15, null=True)
    vat_category = models.ForeignKey(
        VatCategories, on_delete=models.SET_NULL, related_name="clients", null=True)
    registered_address = models.CharField(max_length=150, null=True)
    coida_reg_number = models.CharField(max_length=15, null=True)
    internal_id_number = models.CharField(max_length=15, null=True)
    uif_dept_reg_number = models.CharField(max_length=15, null=True)
    accountant = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="clients")
    financial_years = models.ManyToManyField(
        FinancialYear, through='ClientFinancialYear', related_name='clients')


class ClientFinancialYear(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    schedule_date = models.DateField(null=True)
    finish_date = models.DateField(null=True)

    class Meta:
        unique_together = ('client', 'financial_year')
