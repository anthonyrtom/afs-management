# Make sure all models are imported
from .models import ClientType, CustomUser, Service
from django.forms.widgets import DateInput, DateTimeInput
from django import forms
from django.conf import settings
from .models import ClientType, Client, ClientFinancialYear, VatSubmissionHistory, VatCategory, FinancialYear, Service, ClientService
from users.models import CustomUser, JobTitle


def get_month_as_index(month_list):
    i = 0
    month_index = []
    for c in month_list:
        i += 1
        month_index.append(i)
    # print(month_index)
    return month_index


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
    searchterm = forms.CharField(
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
        widget=forms.Select(attrs={"class": "form-control"}),
        label="VAT Period"
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


class VatClientPeriodUpdateForm(forms.Form):
    client = forms.MultipleChoiceField(
        required=True,
        widget=forms.SelectMultiple(attrs={'class':
                                           'form-control selectpicker',
                                           "data-live-search": "true",
                                           "data-actions-box": "true", })
    )
    year = forms.ChoiceField(
        choices=[],
        label="Select Year",
        required=True,
        widget=forms.Select(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select Year",
        })
    )
    months_list = settings.MONTHS_LIST
    months_indexes_of = get_month_as_index(months_list)
    choices = [(i, month.upper())
               for month, i in zip(months_list, months_indexes_of)]

    month = forms.ChoiceField(
        choices=choices,
        required=True,
        widget=forms.Select(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select year end"}),
        label="VAT Period",
    )

    accountant = forms.MultipleChoiceField(
        choices=[],
        label="Select Accountant(s)",
        required=True,
        widget=forms.SelectMultiple(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select Accountant(s), you can select multiple"}))

    radio_choices = [("all", "All"), ("complete",
                                      "Completed"), ("incomplete", "Incomplete")]
    radio_option = forms.ChoiceField(
        label="Select",
        choices=radio_choices,
        widget=forms.RadioSelect(
            attrs={"class": "form-check-inline"}),
        initial="all",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].choices = [
            (c.id, c.name.upper()) for c in Client.objects.all().order_by("name")
        ]
        self.fields['year'].choices = [
            (c.id, c.the_year) for c in FinancialYear.objects.all().order_by("-the_year")
        ]
        accountant_job_title = JobTitle.objects.filter(
            title="Accountant").first()

        accountant_choices = [("None", "Not Assigned")]
        if accountant_job_title:
            accountant_users = CustomUser.objects.filter(
                job_title=accountant_job_title).order_by('first_name', 'last_name')
            accountant_choices.extend(
                [(user.id, user.get_full_name() or user.email) for user in accountant_users])
            self.fields['accountant'].choices = accountant_choices


class ClientFinancialYearProcessForm(forms.Form):
    client_type = forms.ModelChoiceField(
        queryset=ClientType.objects.all().order_by("name"),
        required=False,
        empty_label="All Clients",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    financial_year = forms.ModelChoiceField(
        queryset=FinancialYear.objects.all().order_by("-the_year"),
        required=False,
        empty_label="Select a year",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    accountant = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(job_title__title="Accountant"),
        required=False,
        empty_label="All Accountants",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    months_list = settings.MONTHS_LIST
    choices = [("all", "ALL")] + [(month, month.upper())
                                  for month in months_list]

    month_ending = forms.ChoiceField(
        choices=choices,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Year End",
    )
    query = forms.CharField(
        max_length=150,
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Search by client Name'})
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
        widget=forms.Select(attrs={"class": "form-control"}),
        label="VAT Period"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['year'].queryset = FinancialYear.objects.all().order_by(
            "-the_year")


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client_type'].choices = [("all", "ALL")] + [
            (c.name, c.name.upper()) for c in ClientType.objects.all()
        ]

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
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Period",
    )
    searchterm = forms.CharField(
        max_length=150,
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Search by client Name'})
    )


class FilterAllFinancialClient(forms.Form):
    client_type = forms.MultipleChoiceField(
        choices=[],
        label="Select Client Type(s)",
        required=True, widget=forms.SelectMultiple(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select Client Type(s), you can select multiple"}))

    years = forms.MultipleChoiceField(
        choices=[],
        label="Select Financial Year(s)",
        required=True,
        widget=forms.SelectMultiple(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select financial year(s), you can select multiple"
        })
    )

    accountant = forms.MultipleChoiceField(
        choices=[],
        label="Select Accountant(s)",
        required=True,
        widget=forms.SelectMultiple(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select Accountant(s), you can select multiple"}))

    months_list = settings.MONTHS_LIST
    months_indexes_of = get_month_as_index(months_list)
    choices = [(i, month.upper())
               for month, i in zip(months_list, months_indexes_of)]

    month = forms.MultipleChoiceField(
        choices=choices,
        required=True,
        widget=forms.SelectMultiple(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select Year end, you can select multiple"}),
        label="Year Ending",
    )
    searchterm = forms.CharField(
        max_length=150,
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Search by client Name'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client_type'].choices = [
            (c.id, c.name.upper()) for c in ClientType.objects.all()
        ]
        self.fields['years'].choices = [(cy.id, cy.the_year) for cy in FinancialYear.objects.all().order_by(
            "-the_year")]

        accountant_job_title = JobTitle.objects.filter(
            title="Accountant").first()

        accountant_choices = [("None", "Not Assigned")]
        if accountant_job_title:
            accountant_users = CustomUser.objects.filter(
                job_title=accountant_job_title).order_by('first_name', 'last_name')
            accountant_choices.extend(
                [(user.id, user.get_full_name() or user.email) for user in accountant_users])
            self.fields['accountant'].choices = accountant_choices


class BookServiceForm(forms.Form):
    client_type = forms.MultipleChoiceField(
        choices=[],
        label="Select Client Type",
        required=True,
        widget=forms.SelectMultiple(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select Years"}))

    years = forms.MultipleChoiceField(
        choices=[],
        label="Select Years",
        required=True,
        widget=forms.SelectMultiple(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select Years"
        })
    )

    accountant = forms.MultipleChoiceField(
        choices=[],
        label="Select Accountant",
        required=True,
        widget=forms.SelectMultiple(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select Years"}))

    months_list = settings.MONTHS_LIST
    months_indexes_of = get_month_as_index(months_list)
    choices = [(i, month.upper())
               for month, i in zip(months_list, months_indexes_of)]

    month = forms.MultipleChoiceField(
        choices=choices,
        required=True,
        widget=forms.SelectMultiple(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select Years"}),
        label="Year Ending",
    )

    service = forms.ChoiceField(
        choices=[("accounting", "Accounting"), ("secretarial",
                                                "Secretarial"), ("taxation", "Taxation")],
        required=True,
        label="Department",
        widget=forms.Select(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "title": "Select a service"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client_type'].choices = [
            (c.id, c.name.upper()) for c in ClientType.objects.all()
        ]
        self.fields['years'].choices = [(cy.id, cy.the_year) for cy in FinancialYear.objects.all().order_by(
            "-the_year")]

        accountant_job_title = JobTitle.objects.filter(
            title="Accountant").first()

        accountant_choices = [("None", "Not Assigned")]
        if accountant_job_title:
            accountant_users = CustomUser.objects.filter(
                job_title=accountant_job_title).order_by('first_name', 'last_name')
            accountant_choices.extend(
                [(user.id, user.get_full_name() or user.email) for user in accountant_users])
            self.fields['accountant'].choices = accountant_choices


class FilterFinancialClient(forms.Form):
    client_type = forms.ChoiceField(choices=[], label="Select Client Type",
                                    required=True, widget=forms.Select(attrs={"class": "form-control"}))
    year = forms.ChoiceField(choices=[], label="Select Financial year",
                             required=True, widget=forms.Select(attrs={"class": "form-control"}))
    start_date = forms.DateField(label="Select start date", required=True, input_formats=['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y'], widget=forms.DateInput(
        attrs={"type": "date", "class": "form-control", "id": "start-date"},))
    end_date = forms.DateField(label="Select end date", required=True, input_formats=['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y'], widget=forms.DateInput(
        attrs={"type": "date", "class": "form-control", "id": "end-date"}))
    accountant = forms.ChoiceField(choices=[], label="Select Accountant",
                                   required=True, widget=forms.Select(attrs={"class": "form-control"}))
    searchterm = forms.CharField(
        max_length=150,
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Search by client Name'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client_type'].choices = [("all", "ALL")] + [
            (c.name, c.name.upper()) for c in ClientType.objects.all()
        ]
        self.fields['year'].choices = [("all", "ALL")] + [(cy.id, cy.the_year) for cy in FinancialYear.objects.all().order_by(
            "-the_year")]

        accountant_job_title = JobTitle.objects.filter(
            title="Accountant").first()

        accountant_choices = [("all", "ALL")]
        if accountant_job_title:
            accountant_users = CustomUser.objects.filter(
                job_title=accountant_job_title).order_by('first_name', 'last_name')
            accountant_choices.extend(
                [(user.id, user.get_full_name() or user.email) for user in accountant_users])
            self.fields['accountant'].choices = accountant_choices


class FinancialProductivityForm(forms.Form):
    client_type = forms.MultipleChoiceField(
        choices=[],
        label="Select Client Type(s)",
        required=True,
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control selectpicker",
                "data-live-search": "true",
                "data-actions-box": "true",
                "title": "Select Client type(s), you can select multiple"}))
    years = forms.MultipleChoiceField(
        choices=[],
        label="Select Financial Year(s)",
        required=True,
        widget=forms.SelectMultiple(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select Financial Year(s), you can select multiple"
        })
    )

    accountant = forms.MultipleChoiceField(
        choices=[],
        label="Select Accountant(s)",
        required=True,
        widget=forms.SelectMultiple(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select Accountant(s), you can select multiple"}))

    months_list = settings.MONTHS_LIST
    months_indexes_of = get_month_as_index(months_list)
    choices = [(i, month.upper())
               for month, i in zip(months_list, months_indexes_of)]

    month = forms.MultipleChoiceField(
        choices=choices,
        required=True,
        widget=forms.SelectMultiple(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select year end, you can select multiple"}),
        label="Year Ending",
    )
    searchterm = forms.CharField(
        max_length=150,
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Search by client Name'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client_type'].choices = [
            (c.id, c.name.upper()) for c in ClientType.objects.all()
        ]
        self.fields['years'].choices = [(cy.id, cy.the_year) for cy in FinancialYear.objects.all().order_by(
            "-the_year")]

        accountant_job_title = JobTitle.objects.filter(
            title="Accountant").first()

        accountant_choices = [("None", "Not Assigned")]
        if accountant_job_title:
            accountant_users = CustomUser.objects.filter(
                job_title=accountant_job_title).order_by('first_name', 'last_name')
            accountant_choices.extend(
                [(user.id, user.get_full_name() or user.email) for user in accountant_users])
            self.fields['accountant'].choices = accountant_choices


class CreateUpdateProvCipcForm(forms.Form):
    client_type = forms.MultipleChoiceField(
        choices=[],
        label="Select Client Type(s)",
        required=True,
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control selectpicker",
                "data-live-search": "true",
                "data-actions-box": "true",
                "title": "Select Client type(s), you can select multiple"}))
    years = forms.ChoiceField(
        choices=[],
        label="Select Financial Year",
        required=True,
        widget=forms.Select(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select Financial Year, you CAN NOT select multiple"
        })
    )
    return_type = forms.ChoiceField(
        choices=[("cipc", "CIPC Annual Return"), ("first",
                                                  "First Provisional Tax"), ("second", "Second Provisional Tax")],
        label="Select return type",
        required=True,
        widget=forms.Select(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select return type"
        })
    )

    accountant = forms.MultipleChoiceField(
        choices=[],
        label="Select Accountant(s)",
        required=True,
        widget=forms.SelectMultiple(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select Accountant(s), you can select multiple"}))

    months_list = settings.MONTHS_LIST
    months_indexes_of = get_month_as_index(months_list)
    choices = [(i, month.upper())
               for month, i in zip(months_list, months_indexes_of)]

    month = forms.ChoiceField(
        choices=choices,
        required=True,
        widget=forms.Select(attrs={
            "class": "form-control selectpicker",
            "data-live-search": "true",
            "data-actions-box": "true",
            "title": "Select year end, you CAN NOT select multiple"}),
        label="Year Ending",
    )
    searchterm = forms.CharField(
        max_length=150,
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Search by client Name'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client_type'].choices = [
            (c.id, c.name.upper()) for c in ClientType.objects.all().order_by("name")
        ]
        self.fields['years'].choices = [(cy.id, cy.the_year) for cy in FinancialYear.objects.all().order_by(
            "-the_year")]

        accountant_job_title = JobTitle.objects.filter(
            title="Accountant").first()

        accountant_choices = [("None", "Not Assigned")]
        if accountant_job_title:
            accountant_users = CustomUser.objects.filter(
                job_title=accountant_job_title).order_by('first_name', 'last_name')
            accountant_choices.extend(
                [(user.id, user.get_full_name() or user.email) for user in accountant_users])
            self.fields['accountant'].choices = accountant_choices


class ClientServiceForm(forms.Form):
    service = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
        error_messages={
            "required": "Please select a service before submitting."
        }
    )
    searchterm = forms.CharField(
        max_length=150,
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Search by client Name'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].choices = [
            (c.id, c.name.title()) for c in Service.objects.all().order_by("name")
        ]
