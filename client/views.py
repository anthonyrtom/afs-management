from django.shortcuts import render
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from . models import Client, FinancialYear, ClientType, VatCategory, VatSubmissionHistory, Month
from users.models import JobTitle, CustomUser
from . forms import ClientFilterForm, AccountantFilterForm, ClientFinancialYear, CompletedAFSsForm, MissingAFSsForm, ClientSearchForm, UserSearchForm, VatCategoryForm, VatClientsByMonthForm, VatClientsPeriodProcess, VatSubmissionUpdateForm, ClientFinancialYearProcessForm, ClientFinancialYearUpdateForm, CreateandViewVATForm


def dashboard(request):
    client_information = {}
    client_count = Client.objects.count()
    client_information["client_count"] = client_count
    financial_years = FinancialYear.objects.count()
    client_information["financial_years"] = financial_years
    client_types = ClientType.objects.count()
    client_information["client_types"] = client_types
    vat_categories = VatCategory.objects.count()
    client_information["vat_categories"] = vat_categories
    accountants = CustomUser.objects.filter(
        job_title__title="Accountant").count()
    client_information["accountants"] = accountants
    noaccountant = Client.objects.filter(accountant__isnull=True).count()
    client_information["noaccountant"] = noaccountant
    vatvendors = Client.objects.filter(vat_category__isnull=False).count()
    client_information["vatvendors"] = vatvendors
    return render(request, "client/dashboard.html", {"client_information": client_information})


@login_required
def reports(request):
    return render(request, "client/reports.html")


@login_required
def view_all_clients(request):
    all_clients = Client.objects.all()
    headers = ["Client Name", "Client Type",
               "Month End", "VAT No", "Accountant"]
    return render(request, "client/all_clients.html", {"clients": all_clients, "headers": headers})


@login_required
def client_filter_view(request):
    form = ClientFilterForm(request.GET or None)
    with_without = "without"
    if form.is_valid():
        field = form.cleaned_data['field']
        null_filter = form.cleaned_data['null_filter']

        if null_filter == 'null':
            filter_kwargs = {f"{field}__isnull": True}
        else:
            filter_kwargs = {f"{field}__isnull": False}
            with_without = "with"
        clients = Client.objects.all()
        clients = clients.filter(**filter_kwargs)
        headers = ["Client Name", "Client Type",
                   "Month End", "VAT No"]
        return render(request, 'client/filtered_clients.html', {'form': form, "clients": clients, "statutory_type": field, "with_without": with_without, "headers": headers})
    else:
        return render(request, 'client/get_clients.html', {'form': form})


@login_required
def filter_clients_by_accountant(request):
    form = AccountantFilterForm()
    clients = None
    headers = ["Client Name", "Client Type",
               "Month End", "VAT No", "Accountant"]
    if 'accountant' in request.GET:
        form = AccountantFilterForm(request.GET)
        if form.is_valid():
            accountant = form.cleaned_data['accountant']
            clients = Client.objects.filter(accountant=accountant)

    return render(request, 'client/accountant_clients.html', {
        'form': form if CustomUser.objects.filter(clients__isnull=False).exists() else None,
        'clients': clients, "headers": headers
    })


@login_required
def scheduled_financials(request):
    scheduled = ClientFinancialYear.objects.filter(
        schedule_date__isnull=False, finish_date__isnull=True)
    return render(request, "client/scheduled_financials.html", {"scheduled": scheduled})


@login_required
def completed_financials(request):
    finished_afs = ClientFinancialYear.objects.filter(
        schedule_date__isnull=False, finish_date__isnull=False)
    headers = ["Client Name", "Financial Year",
               "Start Date", "Finish Date"]
    return render(request, "client/finished_financials.html", {"finished_afs": finished_afs, "headers": headers})


@login_required
def completed_financials_month(request):
    form = CompletedAFSsForm(request.GET or None)
    if form.is_valid():
        month = int(form.cleaned_data["month"])
        headers = ["Client Name", "Financial Year",
                   "Start Date", "Finish Date"]
        finished_afs = ClientFinancialYear.objects.filter(
            finish_date__month=month)
        return render(request, "client/finished_financials_month.html", {"finished_afs": finished_afs, "month": month, "headers": headers})
    return render(request, "client/finished_financials_month.html", {"form": form})


@login_required
def get_unfinished_financials(request):
    form = MissingAFSsForm(request.GET or None)
    data = False
    first_time = True

    if form.is_valid():
        data = True
        first_time = False
        client = form.cleaned_data.get("client_select", None)
        start_year = int(form.cleaned_data["start_year"])
        end_year = int(form.cleaned_data["end_year"])

        # Ensure start_year <= end_year
        if start_year > end_year:
            start_year, end_year = end_year, start_year

        # List of years in range
        missing_years = list(range(start_year, end_year + 1))
        client_data = []  # Store clients and their missing years in a list

        # Get the selected client or all clients
        clients = Client.objects.filter(
            id=client.id) if client else Client.objects.all()

        for curr_client in clients:
            row = [curr_client.name]  # Start with client name
            for year in missing_years:
                financial_year = FinancialYear.objects.filter(
                    the_year=year).first()
                has_record = ClientFinancialYear.objects.filter(
                    client=curr_client, financial_year=financial_year
                ).exists()
                # Append "YES" or "NO"
                row.append("YES" if has_record else "NO")
            client_data.append(row)

        headers = ["Client Name"] + missing_years  # Table headers

        return render(request, "client/unfinished_financials.html", {
            "client_data": client_data,
            "headers": headers,
            "data": data,
            "first_time": first_time,
        })

    return render(request, "client/unfinished_financials.html", {
        "form": form,
        "first_time": first_time,
    })


@login_required
def search_clients(request):
    form = ClientSearchForm(request.GET or None)
    clients = Client.objects.all()  # Default to all clients

    if form.is_valid():
        query = form.cleaned_data.get("query", "")
        if query:
            # Perform search using OR conditions
            clients = clients.filter(
                Q(name__icontains=query) |
                Q(surname__icontains=query) |
                Q(income_tax_number__icontains=query) |
                Q(paye_reg_number__icontains=query) |
                Q(uif_reg_number__icontains=query) |
                Q(entity_reg_number__icontains=query) |
                Q(vat_reg_number__icontains=query) |
                Q(internal_id_number__icontains=query)
            )

    return render(request, "client/search_clients.html", {"form": form, "clients": clients})


@login_required
def get_all_accountants(request):
    accountant = JobTitle.objects.filter(title="Accountant").first()
    if accountant:
        accountants = CustomUser.objects.filter(job_title=accountant)
        return render(request, "client/accountants.html", {"accountants": accountants})
    return render(request, "client/accountants.html")


@login_required
def search_users(request):
    form = UserSearchForm(request.GET or None)
    users = CustomUser.objects.all()  # Default to all users

    if form.is_valid():
        query = form.cleaned_data.get("query", "")
        job_title = form.cleaned_data.get("job_title", None)

        if query:
            users = users.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            )

        if job_title:
            users = users.filter(job_title=job_title)

    return render(request, "client/search_users.html", {"form": form, "users": users})


@login_required
def get_clients_for_category(request):
    form = VatCategoryForm(request.GET or None)
    if form.is_valid():
        selected_category = form.cleaned_data["vat_category"]
        selected_accountant = form.cleaned_data["accountant"]

        clients = Client.get_vat_clients_for_category(
            selected_category.vat_category if selected_category else None,
            selected_accountant if selected_accountant else None
        )

        headers = ["Client Name", "Client Type",
                   "Month End", "VAT No", "Accountant", "Category"]

        return render(request, "client/vat_client_for_category.html", {
            "clients": clients,
            "headers": headers,
            "vat_category": selected_category,
            "selected_accountant": selected_accountant
        })

    return render(request, "client/vat_client_for_category.html", {"form": form})


@login_required
def get_clients_for_month(request):
    form = VatClientsByMonthForm(request.GET or None)

    if form.is_valid():
        month = form.cleaned_data["month"]
        selected_accountant = form.cleaned_data["accountant"]

        clients = Client.get_vat_clients_for_month(
            month=month,
            accountant=selected_accountant if selected_accountant else None
        )

        headers = ["Client Name", "Client Type",
                   "Month End", "VAT No", "Accountant", "Category"]

        return render(request, "client/vat_clients_for_month.html", {
            "clients": clients,
            "month": month.title() if month else "All",
            "selected_accountant": selected_accountant,
            "headers": headers
        })

    return render(request, "client/vat_clients_for_month.html", {"form": form})


@login_required
def process_dashboard(request):
    return render(request, "client/process_dashboard.html")


@login_required
def process_vat_clients_for_period(request):
    form = VatClientsPeriodProcess(request.POST or None)

    if form.is_valid():
        client = form.cleaned_data['client']
        year = form.cleaned_data['year']
        month = form.cleaned_data['month']
        accountant = form.cleaned_data['accountant']

        vat_clients = VatSubmissionHistory.objects.filter(year=year)

        if client and client != "all":
            vat_clients = vat_clients.filter(client=client)
        if month and month != "all":
            month = month.lower()
            month = settings.MONTHS_LIST.index(month) + 1
            vat_clients = vat_clients.filter(month=month)
        if accountant:
            vat_clients = vat_clients.filter(client__accountant=accountant)

        headers = ["Name", "Period", "Submitted",
                   "Client Notified", "Paid", "Comment", "Update"]

        return render(request, "client/process_vat_clients_for_month.html", {
            "vat_clients": vat_clients,
            "headers": headers
        })

    if request.method == "POST" and 'client_id' in request.POST:
        client_id = request.POST.get('client_id')
        client_instance = VatSubmissionHistory.objects.get(id=client_id)
        update_form = VatSubmissionUpdateForm(
            request.POST, instance=client_instance)

        if update_form.is_valid():
            update_form.save()
            messages.success(
                request, "Client VAT status and comment updated successfully!")
        else:
            messages.error(
                request, "Failed to update client data. Please try again.")

    return render(request, "client/process_vat_clients_for_month.html", {"form": form})


@login_required
def process_client_financial_years(request):
    form = ClientFinancialYearProcessForm(request.POST or None)

    if form.is_valid():
        client = form.cleaned_data['client']
        financial_year = form.cleaned_data['financial_year']

        client_financial_years = ClientFinancialYear.objects.filter(
            financial_year=financial_year)
        if client:
            client_financial_years = client_financial_years.filter(
                client=client)

        headers = ["Client Name", "Financial Year", "Schedule Date",
                   "Finish Date", "WP Done", "AFS Done", "Posting Done", "Update"]

        return render(request, "client/process_client_financial_years.html", {
            "client_financial_years": client_financial_years,
            "headers": headers
        })

    if request.method == "POST" and 'client_id' in request.POST:
        client_id = request.POST.get('client_id')
        client_instance = ClientFinancialYear.objects.get(id=client_id)
        update_form = ClientFinancialYearUpdateForm(
            request.POST, instance=client_instance)

        if update_form.is_valid():
            update_form.save()
            messages.success(
                request, "Client financial year updated successfully!")
        else:
            messages.error(
                request, "Failed to update client data. Please try again.")
            # print(update_form.errors)

    return render(request, "client/process_client_financial_years.html", {"form": form})


def create_or_update_vat(request):
    form = CreateandViewVATForm(request.POST or None)
    if form.is_valid():
        year = form.cleaned_data["year"]
        month = form.cleaned_data["month"]
        created_clients = VatSubmissionHistory.create_or_get_vat_clients(
            year, month)
        count = len(created_clients)
        headers = ["Name", "Month", "Year", "Update"]
        return render(request, "client/create_or_view_vat.html", {"created_clients": created_clients, "count": count, "headers": headers})
    return render(request, "client/create_or_view_vat.html", {"form": form})
