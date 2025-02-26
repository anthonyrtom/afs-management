from django.shortcuts import render
from django.db.models import Q
from . models import Client, FinancialYear, ClientType, VatCategories
from users.models import JobTitle, CustomUser
from . forms import ClientFilterForm, AccountantFilterForm, ClientFinancialYear, CompletedAFSsForm, MissingAFSsForm, ClientSearchForm, UserSearchForm, VatCategoryForm, VatClientsByMonthForm


def dashboard(request):
    client_information = {}
    client_count = Client.objects.count()
    client_information["client_count"] = client_count
    financial_years = FinancialYear.objects.count()
    client_information["financial_years"] = financial_years
    client_types = ClientType.objects.count()
    client_information["client_types"] = client_types
    vat_categories = VatCategories.objects.count()
    client_information["vat_categories"] = vat_categories
    accountants = JobTitle.objects.filter(title="Accountant").count()
    client_information["accountants"] = accountants
    noaccountant = Client.objects.filter(accountant__isnull=True).count()
    client_information["noaccountant"] = noaccountant
    vatvendors = Client.objects.filter(vat_category__isnull=False).count()
    client_information["vatvendors"] = vatvendors
    return render(request, "client/dashboard.html", {"client_information": client_information})


def reports(request):
    return render(request, "client/reports.html")


def view_all_clients(request):
    all_clients = Client.objects.all()
    headers = ["Client Name", "Client Type",
               "Month End", "VAT No", "Accountant"]
    return render(request, "client/all_clients.html", {"clients": all_clients, "headers": headers})


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
        return render(request, 'client/filtered_clients.html', {'form': form, "clients": clients, "statutory_type": field, "with_without": with_without})
    else:
        return render(request, 'client/get_clients.html', {'form': form})


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


def scheduled_financials(request):
    scheduled = ClientFinancialYear.objects.filter(
        schedule_date__isnull=False, finish_date__isnull=True)
    return render(request, "client/scheduled_financials.html", {"scheduled": scheduled})


def completed_financials(request):
    finished_afs = ClientFinancialYear.objects.filter(
        schedule_date__isnull=False, finish_date__isnull=False)
    headers = ["Client Name", "Financial Year",
               "Start Date", "Finish Date"]
    return render(request, "client/finished_financials.html", {"finished_afs": finished_afs, "headers": headers})


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
                Q(cipc_reg_number__icontains=query) |
                Q(vat_reg_number__icontains=query) |
                Q(internal_id_number__icontains=query)
            )

    return render(request, "client/search_clients.html", {"form": form, "clients": clients})


def get_all_accountants(request):
    accountant = JobTitle.objects.filter(title="Accountant").first()
    if accountant:
        accountants = CustomUser.objects.filter(job_title=accountant)
        return render(request, "client/accountants.html", {"accountants": accountants})
    return render(request, "client/accountants.html")


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


def get_clients_for_category(request):
    form = VatCategoryForm(request.GET or None)
    if form.is_valid():
        selected_category = form.cleaned_data["vat_category"]
        if selected_category:
            clients = Client.get_vat_clients_for_category(
                selected_category.vat_category)
        else:
            clients = Client.get_vat_clients_for_category()
        headers = ["Client Name", "Client Type",
                   "Month End", "VAT No", "Accountant", "Category"]
        return render(request, "client/vat_client_for_category.html", {"clients": clients, "headers": headers, "vat_category": selected_category})
    return render(request, "client/vat_client_for_category.html", {"form": form})


def get_clients_for_month(request):
    form = VatClientsByMonthForm(request.GET or None)
    if form.is_valid():
        month = form.cleaned_data["month"]
        clients = Client.get_vat_clients_for_month(month=month)
        headers = ["Client Name", "Client Type",
                   "Month End", "VAT No", "Accountant", "Category"]
        return render(request, "client/vat_clients_for_month.html", {"clients": clients, "month": month.title(), "headers": headers})
    return render(request, "client/vat_clients_for_month.html", {"form": form})
