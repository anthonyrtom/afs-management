from django import forms
from django.conf import settings
from .models import ClientType, Client, ClientFinancialYear, VatSubmissionHistory, VatCategories
from users.models import CustomUser, JobTitle


class ClientTypeForm(forms.ModelForm):
    class Meta:
        model = ClientType
        fields = ['name']


class ClientAddForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        accountant_job_title = JobTitle.objects.filter(
            title="Accountant").first()

        if accountant_job_title:  # Check if the job title exists
            self.fields['accountant'].queryset = CustomUser.objects.filter(
                job_title=accountant_job_title)
        else:
            pass

        for field_name in self.fields:
            if field_name not in ['name', 'client_type', 'month_end', 'last_day']:
                self.fields[field_name].required = False

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class ClientFinancialYearForm(forms.ModelForm):
    class Meta:
        model = ClientFinancialYear
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.fields:
            if field_name in ["schedule_date", "finish_date"]:
                self.fields[field_name].required = False


class ClientFilterForm(forms.Form):
    NULLABLE_FIELDS = [
        ('income_tax_number', 'Income Tax Number'),
        ('paye_reg_number', 'PAYE Registration Number'),
        ('uif_reg_number', 'UIF Registration Number'),
        ('cipc_reg_number', 'CIPC Registration Number'),
        ('vat_reg_number', 'VAT Registration Number'),
        ('vat_category', 'VAT Category'),
        ('registered_address', 'Registered Address'),
        ('coida_reg_number', 'COIDA Registration Number'),
        ('internal_id_number', 'Internal ID Number'),
        ('uif_dept_reg_number', 'UIF Department Registration Number'),
        ('accountant', 'Accountant'),
    ]

    field = forms.ChoiceField(choices=NULLABLE_FIELDS,
                              required=True, label="Select Field", widget=forms.Select(attrs={'class': 'form-control m-2'}))
    null_filter = forms.ChoiceField(choices=[('null', 'Null'), ('not_null', 'Not Null')], required=True,
                                    label='Select null if you want the field selected above to show not registered for the tax type or other selected above else select Not Null', widget=forms.Select(attrs={'class': 'form-control m-2'}))


class AccountantFilterForm(forms.Form):
    accountant = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(clients__isnull=False).distinct(),
        empty_label="Select an Accountant",
        required=True,
        widget=forms.Select(attrs={"class": "form-control"})
    )


class CompletedAFSsForm(forms.Form):
    month = forms.IntegerField(max_value=12, min_value=1, required=True, widget=forms.NumberInput(
        attrs={'class': 'form-control'}))


class MissingAFSsForm(forms.Form):
    start_year = forms.IntegerField(min_value=settings.FIRST_FINANCIAL_YEAR, max_value=settings.LAST_FINANCIAL_YEAR,
                                    required=True, widget=forms.NumberInput(attrs={"class": "form-control"}))
    end_year = forms.IntegerField(min_value=settings.FIRST_FINANCIAL_YEAR, max_value=settings.LAST_FINANCIAL_YEAR,
                                  required=True, widget=forms.NumberInput(attrs={"class": "form-control"}))
    client_select = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        empty_label="Select a Client",
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )


class ClientSearchForm(forms.Form):
    query = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Search Clients...'})
    )


class UserSearchForm(forms.Form):
    query = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Search Users...'})
    )
    job_title = forms.ModelChoiceField(
        queryset=JobTitle.objects.all(),
        required=False,
        empty_label="Select Job Title",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class VatSubmissionHistoryForm(forms.ModelForm):
    class Meta:
        model = VatSubmissionHistory
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            if field_name in ["submitted", "paid", "client_notified", "comment"]:
                self.fields[field_name].required = False


class VatCategoryForm(forms.Form):
    vat_category = forms.ModelChoiceField(
        queryset=VatCategories.objects.all(),
        required=False,
        empty_label="Select Vat Category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class VatClientsByMonthForm(forms.Form):
    months_list = settings.MONTHS_LIST
    choices = [("all", "ALL")] + [(month, month.upper())
                                  for month in months_list]
    month = forms.ChoiceField(choices=choices, required=False, widget=forms.Select(
        attrs={"class": "form-control"}))
