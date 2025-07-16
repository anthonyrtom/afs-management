# Make sure all models are imported
from .models import ClientType, CustomUser, Service
from django.forms.widgets import DateInput, DateTimeInput
from django import forms
from django.conf import settings
from .models import ClientType, Client, ClientFinancialYear, VatSubmissionHistory, VatCategory, FinancialYear, Service, ClientService
from users.models import CustomUser, JobTitle


class ClientTypeForm(forms.ModelForm):
    class Meta:
        model = ClientType
        fields = ['name']


class ClientFilter(forms.Form):
    client_type = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Select a client type or leave blank",
        required=False
    )
    accountant = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "form-control"}),
        required=False,
        label="Select accountant or leave blank"
    )
    year_end = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "form-control"}),
        required=False,
        label="Select year end"
    )
    service_offered = forms.ChoiceField(
        widget=forms.Select(attrs={"class": "form-control"}),
        required=False,
        label="Select a service or leave blank"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['client_type'].choices = [("all", "ALL")] + \
                                             [(ct.id, ct.name) for ct in ClientType.objects.all().order_by(
                                                 "name")]

        accountant_job_title = JobTitle.objects.filter(
            title="Accountant").first()

        accountant_choices = [("all", "ALL")]
        if accountant_job_title:
            accountant_users = CustomUser.objects.filter(
                job_title=accountant_job_title).order_by('first_name', 'last_name')
            accountant_choices.extend(
                [(user.id, user.get_full_name() or user.email) for user in accountant_users])
        self.fields['accountant'].choices = accountant_choices

        # year_end choices
        months_list = settings.MONTHS_LIST
        self.fields['year_end'].choices = [("all", "ALL")] + \
                                          [(month, month.upper())
                                           for month in months_list]

        # service_offered choices
        self.fields['service_offered'].choices = [("all", "All services")] + \
            [(s.id, s.name) for s in Service.objects.all().order_by("name")]


class ClientAddForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        accountant_job_title = JobTitle.objects.filter(
            title="Accountant").first()
        try:
            if accountant_job_title:
                self.fields['accountant'].queryset = CustomUser.objects.filter(
                    job_title=accountant_job_title)
        except:
            pass

        for field_name in self.fields:
            if field_name not in ['name', 'client_type', 'month_end', 'last_day']:
                self.fields[field_name].required = False


class ClientFinancialYearForm(forms.ModelForm):
    class Meta:
        model = ClientFinancialYear
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.fields:
            if field_name in ["schedule_date", "finish_date", "comment"]:
                self.fields[field_name].required = False


class ClientFinancialYearGetForm(forms.ModelForm):
    class Meta:
        model = ClientFinancialYear
        fields = ["financial_year", "afs_done", "itr34c_issued",
                  "wp_done", "posting_done", "client_invoiced"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            if field_name in ["afs_done", "itr34c_issued", "wp_done", "posting_done", "client_invoiced"]:
                self.fields[field_name].required = False

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                # Use 'form-check-input' for checkboxes
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

        if 'financial_year' in self.fields:
            self.fields['financial_year'].queryset = FinancialYear.objects.all().order_by(
                '-the_year')


class ClientFilterForm(forms.Form):
    NULLABLE_FIELDS = [
        ('income_tax_number', 'Income Tax Number'),
        ('paye_reg_number', 'PAYE Registration Number'),
        ('uif_reg_number', 'UIF Registration Number'),
        ('entity_reg_number', 'CIPC Registration Number'),
        ('vat_reg_number', 'VAT Registration Number'),
        ('vat_category', 'VAT Category'),
        ('registered_address', 'Registered Address'),
        ('coida_reg_number', 'COIDA Registration Number'),
        ('internal_id_number', 'Internal ID Number'),
        ('uif_dept_reg_number', 'UIF Department Registration Number'),
        ('accountant', 'Accountant'),
        ("first_financial_year", "First Financial Year"),
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
    year = forms.IntegerField(min_value=settings.FIRST_FINANCIAL_YEAR, max_value=settings.LAST_FINANCIAL_YEAR,
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


class ClientFilterForm(forms.Form):
    client_type = forms.ChoiceField(
        choices=[], required=True, widget=forms.Select(attrs={"class": "form-control"}))
    query = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Search Clients...'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client_type'].choices = [("all", "ALL")] + [
            (c.name, c.name.upper()) for c in ClientType.objects.all()
        ]


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


class VatClientSearchForm(forms.Form):
    client_type = forms.ChoiceField(
        required=False,
        label="Select Client Type",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    vat_category = forms.ChoiceField(
        required=False,
        label="Select VAT Category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    months_list = settings.MONTHS_LIST
    choices = [("all", "ALL")] + [(month, month.upper())
                                  for month in months_list]

    month = forms.ChoiceField(
        choices=choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="VAT Period"
    )
    accountant = forms.ChoiceField(
        required=False,
        label="All Accountants",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client_type'].choices = [("all", "ALL")] + \
                                             [(ct.id, ct.name) for ct in ClientType.objects.all().order_by(
                                                 "name")]
        accountant_job_title = JobTitle.objects.filter(
            title="Accountant").first()

        accountant_choices = [("all", "ALL")]
        if accountant_job_title:
            accountant_users = CustomUser.objects.filter(
                job_title=accountant_job_title).order_by('first_name', 'last_name')
            accountant_choices.extend(
                [(user.id, user.get_full_name() or user.email) for user in accountant_users])
        self.fields['accountant'].choices = accountant_choices
        cat = [("all", "ALL")] + [(ct.id, ct.vat_category)
                                  for ct in VatCategory.objects.all().order_by("vat_category")]
        self.fields["vat_category"].choices = cat


class VatClientsByMonthForm(forms.Form):
    months_list = settings.MONTHS_LIST
    choices = [("all", "ALL")] + [(month, month.upper())
                                  for month in months_list]

    month = forms.ChoiceField(
        choices=choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    accountant = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(job_title__title="Accountant"),
        required=False,
        empty_label="All Accountants",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class VatClientsPeriodProcess(forms.Form):
    client = forms.ModelChoiceField(
        queryset=Client.objects.filter(
            vat_category__isnull=False).order_by("name"),
        required=False,
        empty_label="All VAT Vendors",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    year = forms.ModelChoiceField(
        queryset=FinancialYear.objects.all().order_by("-the_year"),
        required=True,
        empty_label="Select a year",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    months_list = settings.MONTHS_LIST
    choices = [("all", "ALL")] + [(month, month.upper())
                                  for month in months_list]

    month = forms.ChoiceField(
        choices=choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    accountant = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(job_title__title="Accountant"),
        required=False,
        empty_label="All Accountants",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    radio_choices = [("all", "All"), ("complete",
                                      "Completed"), ("incomplete", "Incomplete")]
    radio_option = forms.ChoiceField(
        label="Select",
        choices=radio_choices,
        widget=forms.RadioSelect(
            attrs={"class": "form-check-inline"}),
        initial="all",
    )


class VatSubmissionUpdateForm(forms.ModelForm):
    class Meta:
        model = VatSubmissionHistory
        fields = ['submitted', 'client_notified', 'paid', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            if field_name in ["submitted", "paid", "client_notified", "comment"]:
                self.fields[field_name].required = False


class ClientFinancialYearProcessForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=Client.objects.all().order_by("name"),
        required=False,
        empty_label="All Clients",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    financial_year = forms.ModelChoiceField(
        queryset=FinancialYear.objects.all().order_by("-the_year"),
        required=True,
        empty_label="Select a year",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    accountant = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(job_title__title="Accountant"),
        required=False,
        empty_label="All Accountants",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    radio_choices = [("all", "View all Clients"), ("complete", "View with all choices complete"),
                     ("incomplete", "View all choices not complete")]
    radio_input = forms.ChoiceField(
        label="Select one of the choices below",
        choices=radio_choices,
        widget=forms.RadioSelect(attrs={"class": "form-check"}),
        initial="all"
    )


class ClientFinancialYearUpdateForm(forms.ModelForm):
    class Meta:
        model = ClientFinancialYear
        fields = ['schedule_date', 'finish_date',
                  'wp_done', 'afs_done', 'posting_done', 'itr34c_issued', 'client_invoiced', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["finish_date"].required = False
        self.fields["comment"].required = False
        self.fields["schedule_date"].required = False


class CreateandViewVATForm(forms.Form):
    months_list = settings.MONTHS_LIST
    choices = [("all", "ALL")] + [(month, month.upper())
                                  for month in months_list]

    year = forms.ModelChoiceField(
        queryset=FinancialYear.objects.none(),  # placeholder
        required=True,
        empty_label="Select a year",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    month = forms.ChoiceField(
        choices=choices,
        required=True,
        widget=forms.Select(attrs={"class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['year'].queryset = FinancialYear.objects.all().order_by(
            "-the_year")


class ClientForMonthForm(forms.Form):
    months_list = settings.MONTHS_LIST
    choices = [("all", "ALL")] + [(month, month.upper())
                                  for month in months_list]

    month = forms.ChoiceField(
        choices=choices,
        required=True,
        widget=forms.Select(attrs={"class": "form-control"})
    )


class ServiceAddForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].required = False


class ClientServiceAddForm(forms.ModelForm):
    class Meta:
        model = ClientService
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_date"].required = False
        self.fields["end_date"].required = False
        self.fields["comment"].required = False


class FilterByServiceForm(forms.Form):
    client_type = forms.ChoiceField(
        choices=[], widget=forms.Select(attrs={"class": "form-control"}))

    # select_a_service = forms.ChoiceField(
    #     widget=forms.Select(attrs={"class": "form-control"}),
    #     required=False,
    #     label="Select a service or leave blank"
    # )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client_type'].choices = [("all", "ALL")] + [
            (c.name, c.name.upper()) for c in ClientType.objects.all()
        ]
        # self.fields["select_a_service"].choices = [
        #     ("all", "All services")] + [(s.id, s.name) for s in Service.objects.all().order_by("name")]

    months_list = settings.MONTHS_LIST
    choices = [("all", "ALL")] + [(month, month.upper())
                                  for month in months_list]

    services = [("vat clients", "VAT Clients"), ("financial statements clients", "Financial Statements Clients"),
                ("provisional tax clients", "Provisional Tax Clients"), ("cipc clients", "CIPC Clients")]
    select_a_service = forms.ChoiceField(
        choices=services, required=True, label="Select a service to filter", widget=forms.Select(attrs={"class": "form-control"}))

    month = forms.ChoiceField(
        choices=choices,
        required=True,
        widget=forms.Select(attrs={"class": "form-control"})
    )
    query = forms.CharField(
        max_length=150,
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Search by client Name'})
    )
