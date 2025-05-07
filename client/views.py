from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from . models import Client, FinancialYear, ClientType, VatCategory, VatSubmissionHistory, Service, ClientService
from users.models import JobTitle, CustomUser
from . forms import ClientFilterForm, AccountantFilterForm, ClientFinancialYear, CompletedAFSsForm, MissingAFSsForm, ClientSearchForm, UserSearchForm, VatCategoryForm, VatClientsByMonthForm, VatClientsPeriodProcess, VatSubmissionUpdateForm, ClientFinancialYearProcessForm, ClientFinancialYearUpdateForm, CreateandViewVATForm, ClientFinancialYearGetForm, ClientForMonthForm


@login_required
def dashboard(request):
    headers = [c_type.name for c_type in ClientType.objects.all()]
    total_all = 0
    total_vendors = 0
    total_curr_vendors = 0
    total_cipc = 0
    total_afs = 0
    total_provs = 0
    total_curr_afs = 0
    total_curr_provs = 0
    total_curr_cipc = 0

    today = datetime.date(datetime.now())
    last_vat_month_date = today - relativedelta(months=1)
    all_counts = []
    vendor_counts = []
    curr_vendor_counts = []
    cipc_counts = []
    afs_counts = []
    curr_afs_counts = []
    prov_tax_counts = []
    curr_prov_tax_counts = []
    curr_cipc_counts = []
    try:
        all_vat_vendors = Client.get_vat_clients_for_category()
        vat_vendors_due_this_month = Client.get_vat_clients_for_month(
            month=last_vat_month_date.strftime("%B"))
        cipc_clients = Client.get_clients_of_type("Cipc Returns", today)
        afs_clients = Client.get_afs_clients(today)
        prov_clients = Client.get_prov_tax_clients(today)
        cipc_service = Service.objects.get(name="Cipc Returns")
        for name in headers:
            client_type = ClientType.objects.get(name=name)
            count = Client.count_clients_of_type(name)
            total_all += count
            all_counts.append(count)
            cipc_count = sum(
                1 for cipc in cipc_clients if cipc.client_type == client_type and ClientService.is_service_offered(cipc.id, cipc_service.id, today) and cipc.is_client_cipc_reg_eligible())

            curr_cipc_count = sum(
                1 for cipc in cipc_clients if cipc.client_type == client_type and ClientService.is_service_offered(cipc.id, cipc_service.id, today) and cipc.is_client_cipc_reg_eligible() and cipc.get_birthday_in_year(today.year) and (cipc.get_birthday_in_year(today.year).month == today.month))
            total_cipc += cipc_count

            vendor_count = sum(
                1 for vendor in all_vat_vendors
                if vendor.client_type == client_type and vendor.is_vat_vendor(as_at_date=today, service_name="Vat Submission")
            )
            curr_vendor_count = sum(
                1 for vendor in vat_vendors_due_this_month if vendor.client_type == client_type and vendor.is_vat_vendor(as_at_date=today, service_name="Vat Submission")
            )
            afs_count = sum(
                1 for client in afs_clients if client.client_type == client_type)
            curr_afs_count = sum(
                1 for client in afs_clients if client.client_type == client_type and client.month_end == today.month)
            prov_count = sum(
                1 for client in prov_clients if client.client_type == client_type)

            curr_prov_count = sum(
                1 for client in prov_clients if client.client_type == client_type and (client.is_first_prov_tax_month(today) or client.is_second_prov_tax_month(today)))

            total_afs += afs_count
            total_vendors += vendor_count
            total_curr_vendors += curr_vendor_count
            total_provs += prov_count
            total_curr_afs += curr_afs_count
            total_curr_provs += curr_prov_count
            total_curr_cipc += curr_cipc_count

            vendor_counts.append(vendor_count)
            cipc_counts.append(cipc_count)
            curr_vendor_counts.append(curr_vendor_count)
            afs_counts.append(afs_count)
            prov_tax_counts.append(prov_count)
            curr_afs_counts.append(curr_afs_count)
            curr_prov_tax_counts.append(curr_prov_count)
            curr_cipc_counts.append(curr_cipc_count)

        return render(request, "client/dashboard.html", {
            "headers": headers,
            "all_counts": all_counts,
            "vendor_counts": vendor_counts,
            "total_all": total_all,
            "total_vendors": total_vendors,
            "cipc_counts": cipc_counts,
            "total_cipc": total_cipc,
            "total_provs": total_provs,
            "total_curr_afs": total_curr_afs,
            "total_curr_provs": total_curr_provs,
            "total_curr_cipc": total_curr_cipc,
            "curr_vendor_counts": curr_vendor_counts,
            "total_curr_vendors": total_curr_vendors,
            "afs_counts": afs_counts,
            "total_afs": total_afs,
            "prov_tax_counts": prov_tax_counts,
            "curr_afs_counts": curr_afs_counts,
            "curr_prov_tax_counts": curr_prov_tax_counts,
            "curr_cipc_counts": curr_cipc_counts
        })
    except Exception as e:
        print(e)
        messages.error(request, "There was an error")
        return redirect(reverse('home'))


@login_required
def dashboard_list(request, filter_type, client_type):
    query = request.GET.get("q", "")
    today = datetime.date.today()
    clients = Client.objects.all()

    # Filter by client_type
    clients = clients.filter(client_type__name=client_type)

    # Apply additional filter depending on "filter_type"
    if filter_type == "all_clients":
        pass  # Already filtered by client_type

    elif filter_type == "vat_vendors":
        clients = clients.filter(vat_registration_number__isnull=False)

    elif filter_type == "current_vat_vendors":
        last_month = today - relativedelta(months=1)
        clients = Client.get_vat_clients_for_month(
            last_month.strftime("%B")).filter(client_type__name=client_type)

    elif filter_type == "afs_clients":
        clients = Client.get_afs_clients(today).filter(
            client_type__name=client_type)

    elif filter_type == "prov_tax_clients":
        clients = Client.get_prov_tax_clients(
            today).filter(client_type__name=client_type)

    elif filter_type == "cipc_clients":
        clients = Client.get_clients_of_type(
            "Cipc Returns", today).filter(client_type__name=client_type)

    elif filter_type == "current_cipc_clients":
        clients = Client.get_clients_of_type(
            "Cipc Returns", today).filter(client_type__name=client_type)
        clients = [client for client in clients if client.get_birthday_in_year(
            today.year) and client.get_birthday_in_year(today.year).month == today.month]

    # Apply search
    if query:
        clients = clients.filter(name__icontains=query)

    return render(request, "client/dashboard_list.html", {
        "clients": clients,
        "filter_type": filter_type.replace("_", " ").title(),
        "client_type": client_type,
        "query": query
    })


@login_required
def reports(request):
    return render(request, "client/reports.html")


@login_required
def view_all_clients(request):
    all_clients = Client.objects.all().order_by("name")
    headers = ["Name", "Internal ID", "Registration No.",
               "Entity Type", "Year End",  "Accountant"]

    query = request.GET.get("searchterm", "")
    if query:
        all_clients = all_clients.filter(Q(name__icontains=query) |
                                         Q(surname__icontains=query) |
                                         Q(income_tax_number__icontains=query) |
                                         Q(paye_reg_number__icontains=query) |
                                         Q(uif_reg_number__icontains=query) |
                                         Q(entity_reg_number__icontains=query) |
                                         Q(vat_reg_number__icontains=query) |
                                         Q(internal_id_number__icontains=query))
    count = len(all_clients)
    return render(request, "client/all_clients.html", {"clients": all_clients, "headers": headers, "count": count})


@login_required
def client_filter_view(request):
    form = ClientFilterForm(request.GET or None)
    with_without = "without"

    if form.is_valid():
        field = form.cleaned_data['field']
        null_filter = form.cleaned_data['null_filter']

        filter_kwargs = {f"{field}__isnull": null_filter == 'null'}
        with_without = "without" if null_filter == 'null' else "with"

        clients = Client.objects.filter(**filter_kwargs)
        total = Client.objects.count()
        headers = ["Client Name", "Internal ID", "Reg No.",
                   "Client Type", "Year End", "VAT No", "Accountant"]

        search_term = request.GET.get("searchterm", "")
        if search_term:
            clients = clients.filter(
                Q(name__icontains=search_term) |
                Q(surname__icontains=search_term) |
                Q(income_tax_number__icontains=search_term) |
                Q(paye_reg_number__icontains=search_term) |
                Q(uif_reg_number__icontains=search_term) |
                Q(entity_reg_number__icontains=search_term) |
                Q(vat_reg_number__icontains=search_term) |
                Q(internal_id_number__icontains=search_term)
            )

        clients = clients.order_by("name")
        count = clients.count()
        field_display = field.replace("_", " ")

        return render(request, 'client/filtered_clients.html', {
            'form': form,
            'clients': clients,
            'statutory_type': field_display,
            'with_without': with_without,
            'headers': headers,
            'count': count,
            'total': total
        })

    return render(request, 'client/get_clients.html', {'form': form})


@login_required
def filter_clients_by_accountant(request):
    form = AccountantFilterForm(request.GET or None)
    clients = None
    count = 0
    headers = ["Client Name", "Client Type",
               "Month End", "VAT No.", "Accountant"]
    search_term = request.GET.get("search", "")

    if form.is_valid() and form.cleaned_data.get('accountant'):
        accountant = form.cleaned_data['accountant']
        clients = Client.objects.filter(accountant=accountant)

        if search_term:
            clients = clients.filter(
                Q(name__icontains=search_term) |
                Q(vat_reg_number__icontains=search_term) |
                Q(internal_id_number__icontains=search_term) |
                Q(entity_reg_number__icontains=search_term) |
                Q(paye_reg_number__icontains=search_term)
            )

        clients = clients.order_by("name")
        count = clients.count()

    has_accountants = CustomUser.objects.filter(clients__isnull=False).exists()

    return render(request, 'client/accountant_clients.html', {
        'form': form if has_accountants else None,
        'clients': clients,
        'headers': headers,
        'count': count,
        'search_term': search_term
    })


@login_required
def get_finished_or_scheduled_afs(request):  # method to replace two of them
    form = ClientFinancialYearGetForm(request.GET or None)
    if form.is_valid():
        financial_year = form.cleaned_data["financial_year"]
        afs_done = form.cleaned_data.get("afs_done", False)
        itr34c_issued = form.cleaned_data.get("itr34c_issued", False)
        wp_done = form.cleaned_data.get("wp_done", False)
        posting_done = form.cleaned_data.get("posting_done", False)
        client_invoiced = form.cleaned_data.get("client_invoiced", False)

        financials = ClientFinancialYear.objects.filter(
            financial_year=financial_year).order_by("client__name")
        total = len(financials)
        if afs_done:
            financials = financials.filter(afs_done=True)
        if itr34c_issued:
            financials = financials.filter(itr34c_issued=True)
        if wp_done:
            financials = financials.filter(wp_done=True)
        if posting_done:
            financials = financials.filter(posting_done=True)
        if client_invoiced:
            financials = financials.filter(client_invoiced=True)
        count = len(financials)

        headers = ["Name", "Fin Year", "Schedule Date", "Finish Date"]
        return render(request, "client/filtered_financials.html", {"financials": financials, "count": count, "total": total, "headers": headers})
    return render(request, "client/get_scheduled_or_finished.html", {"form": form})


@login_required
def scheduled_financials(request):
    form = ClientFinancialYearGetForm(request.POST or None)
    if form.is_valid():
        financial_year = form.cleaned_data["financial_year"]
        scheduled = ClientFinancialYear.objects.filter(
            schedule_date__isnull=False, finish_date__isnull=True, financial_year=financial_year).order_by("client__name")
        count = len(scheduled)
        total = len(ClientFinancialYear.objects.filter(
            financial_year=financial_year))
        headers = ["Name", "Fin Year", "Schedule Date", "Finish Date"]
        return render(request, "client/scheduled_financials.html", {"scheduled": scheduled, "count": count, "total": total, "headers": headers})

    return render(request, "client/scheduled_financials.html", {"form": form})


@login_required
def completed_financials_month(request):
    form = CompletedAFSsForm(request.GET or None)
    if form.is_valid():
        month = int(form.cleaned_data["month"])
        headers = ["Client Name", "Financial Year",
                   "Start Date", "Finish Date"]
        finished_afs = ClientFinancialYear.objects.filter(
            finish_date__month=month).order_by("client__name")
        count = len(finished_afs)
        return render(request, "client/finished_financials_month.html", {"finished_afs": finished_afs, "month": month, "headers": headers, "count": count})
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

        if start_year > end_year:
            start_year, end_year = end_year, start_year

        missing_years = list(range(start_year, end_year + 1))
        client_data = []

        clients = Client.objects.filter(
            id=client.id) if client else Client.objects.all().order_by("name")
        counter = 0
        for curr_client in clients:
            if curr_client.is_afs_client():
                for year in missing_years:
                    if curr_client.is_year_after_afs_first(year):
                        counter = counter + 1
                        row = [curr_client.name]
                        financial_year = FinancialYear.objects.filter(
                            the_year=year).first()
                        has_record = ClientFinancialYear.objects.filter(
                            client=curr_client, financial_year=financial_year, afs_done=True
                        ).exists()
                        if not has_record:
                            row.append("NO")
                            client_data.append(row)
        count = len(client_data)
        headers = ["Client Name"] + missing_years

        return render(request, "client/unfinished_financials.html", {
            "client_data": client_data,
            "headers": headers,
            "data": data,
            "first_time": first_time,
            "count": count, "counter": counter
        })

    return render(request, "client/unfinished_financials.html", {
        "form": form,
        "first_time": first_time,
    })


@login_required
def get_all_accountants(request):
    accountant_title = JobTitle.objects.filter(title="Accountant").first()
    accountants = CustomUser.objects.none()
    count = 0
    query = request.GET.get("search", "")

    if accountant_title:
        accountants = CustomUser.objects.filter(job_title=accountant_title)

        if query:
            accountants = accountants.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            )

        accountants = accountants.order_by("email")
        count = accountants.count()

    return render(request, "client/accountants.html", {
        "accountants": accountants,
        "count": count,
        "query": query
    })


@login_required
def search_users(request):
    form = UserSearchForm(request.GET or None)
    users = CustomUser.objects.all().order_by("email")  # Default to all users
    count = 0

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
    count = len(users)
    return render(request, "client/search_users.html", {"form": form, "users": users, "count": count})


@login_required
def get_clients_for_category(request):
    form = VatCategoryForm(request.GET or None)
    clients = None
    count = 0
    headers = ["Client Name", "Client Type",
               "Month End", "VAT No", "Accountant", "Category"]
    searchterm = request.GET.get("searchterm", "")

    if form.is_valid():
        selected_category = form.cleaned_data["vat_category"]
        selected_accountant = form.cleaned_data["accountant"]

        clients = Client.get_vat_clients_for_category(
            selected_category.vat_category if selected_category else None,
            selected_accountant if selected_accountant else None
        ).order_by("name")

        if searchterm:
            clients = clients.filter(
                Q(name__icontains=searchterm) |
                Q(surname__icontains=searchterm) |
                Q(income_tax_number__icontains=searchterm) |
                Q(vat_reg_number__icontains=searchterm)
            )

        count = clients.count()

        return render(request, "client/vat_client_for_category.html", {
            "form": form,
            "clients": clients,
            "headers": headers,
            "vat_category": selected_category,
            "selected_accountant": selected_accountant,
            "searchterm": searchterm,
            "count": count
        })

    return render(request, "client/vat_client_for_category.html", {"form": form})


@login_required
def get_clients_for_month(request):
    form = VatClientsByMonthForm(request.GET or None)
    clients = None
    count = 0
    headers = ["Client Name", "Client Type",
               "Month End", "VAT No", "Accountant", "Category"]
    searchterm = request.GET.get("searchterm", "")

    if form.is_valid():
        month = form.cleaned_data["month"]
        selected_accountant = form.cleaned_data["accountant"]

        clients = Client.get_vat_clients_for_month(
            month=month,
            accountant=selected_accountant if selected_accountant else None
        )

        if searchterm:
            clients = clients.filter(
                Q(name__icontains=searchterm) |
                Q(surname__icontains=searchterm) |
                Q(income_tax_number__icontains=searchterm) |
                Q(vat_reg_number__icontains=searchterm)
            )

        count = clients.count()
        return render(request, "client/vat_clients_for_month.html", {
            "form": form,
            "clients": clients,
            "month": month.title() if month else "All",
            "selected_accountant": selected_accountant,
            "headers": headers,
            "count": count,
            "searchterm": searchterm
        })

    return render(request, "client/vat_clients_for_month.html", {"form": form})


@login_required
def process_dashboard(request):
    return render(request, "client/process_dashboard.html")


def create_or_update_vat(request):
    form = CreateandViewVATForm(request.POST or None)
    if form.is_valid():
        year = form.cleaned_data["year"]
        month = form.cleaned_data["month"]
        created_clients = []
        if month.lower() == "all":
            months = settings.MONTHS_LIST
            for one_month in months:
                instance_clients = VatSubmissionHistory.create_or_get_vat_clients(
                    year, one_month)
                created_clients.extend(instance_clients)
        else:
            created_clients = VatSubmissionHistory.create_or_get_vat_clients(
                year, month)
        count = len(created_clients)
        headers = ["Name", "Month", "Year", "Update"]
        return render(request, "client/create_or_view_vat.html", {"created_clients": created_clients, "count": count, "headers": headers})
    return render(request, "client/create_or_view_vat.html", {"form": form})


@login_required
def process_vat_clients_for_period(request):
    """Handles form submission and displays filtered VAT clients."""
    form = VatClientsPeriodProcess(request.POST or None)

    if form.is_valid():
        client = form.cleaned_data['client']
        year = form.cleaned_data['year']
        month = form.cleaned_data['month']
        accountant = form.cleaned_data['accountant']

        vat_clients = VatSubmissionHistory.objects.filter(
            year=year).order_by("client__name")

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
        count = len(vat_clients)
        return render(request, "client/vat_clients_list.html", {
            "vat_clients": vat_clients,
            "headers": headers, "count": count
        })

    return render(request, "client/vat_clients_form.html", {"form": form})


@login_required
def update_vat_client_status(request):
    """Handles updating VAT client status and comments."""
    if request.method == "POST" and 'client_id' in request.POST:
        client_id = request.POST.get('client_id')
        client_instance = get_object_or_404(VatSubmissionHistory, id=client_id)

        update_form = VatSubmissionUpdateForm(
            request.POST, instance=client_instance)

        if update_form.is_valid():
            update_form.save()
            messages.success(
                request, "Client VAT status and comment updated successfully!")
        else:
            messages.error(
                request, "Failed to update client data. Please try again.")

        return redirect('process_vat_clients_for_period')

    return redirect('process_vat_clients_for_period')


@login_required
def process_client_financial_years(request):
    """Handles the form selection and renders the results."""
    form = ClientFinancialYearProcessForm(request.POST or None)

    if form.is_valid():
        client = form.cleaned_data['client']
        financial_year = form.cleaned_data['financial_year']

        client_financial_years = ClientFinancialYear.objects.filter(
            financial_year=financial_year
        ).order_by("client__name")
        if client:
            client_financial_years = client_financial_years.filter(
                client=client)

        headers = ["Client Name", "Financial Year", "Schedule Date",
                   "Finish Date", "WP Done", "AFS Done", "Posting Done", "ITR14", "Update"]
        count = len(client_financial_years)
        return render(request, "client/client_financial_years_list.html", {
            "client_financial_years": client_financial_years,
            "headers": headers, "count": count
        })

    return render(request, "client/client_financial_years_form.html", {"form": form})


@login_required
def update_client_financial_year(request):
    """Handles updating the financial year entry."""
    if request.method == "POST" and 'client_id' in request.POST:
        client_id = request.POST.get('client_id')
        client_instance = get_object_or_404(ClientFinancialYear, id=client_id)

        update_form = ClientFinancialYearUpdateForm(
            request.POST, instance=client_instance)

        if update_form.is_valid():
            update_form.save()
            messages.success(
                request, "Client financial year updated successfully!")
        else:
            messages.error(
                request, "Failed to update client data. Please try again.")

        return redirect(reverse('process_client_financial_years'))

    return redirect(reverse('process_client_financial_years'))


@login_required
def create_clients_for_financial_year(request):
    form = ClientFinancialYearProcessForm(request.POST or None)
    if form.is_valid():
        year = form.cleaned_data["financial_year"]
        created_clients = ClientFinancialYear.setup_clients_afs_for_year(
            year.the_year)
        messages.success(
            request, f"{len(created_clients)} created or returned")
        return redirect(reverse("process"))
    return render(request, "client/financial_years_form.html", {"form": form})


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = "client/client_detail.html"
    context_object_name = "client"

    def get_object(self):
        return get_object_or_404(Client, id=self.kwargs["id"])


@login_required
def get_clients_with_certain_month_end(request):
    form = ClientForMonthForm(request.GET or None)
    if form.is_valid():
        month = form.cleaned_data["month"].lower()
        clients = []
        if month == "all":
            clients = Client.objects.all().order_by("name")
        else:
            month_index = settings.MONTHS_LIST.index(month) + 1
            clients = Client.objects.filter(
                month_end=month_index).order_by("name")
        headers = ["Client Name", "Client Type",
                   "Month End", "VAT No"]
        count = len(clients)
        return render(request, "client/clients_with_monthend.html", {"clients": clients, "headers": headers, "count": count, "total": len(Client.objects.all()), "month": month.title()})
    return render(request, "client/clients_with_monthend.html", {"form": form})


@method_decorator(login_required, name='dispatch')
class ClientServiceListView(View):
    def get(self, request):
        service_id = request.GET.get('service', None)
        services = Service.objects.all()  # Get all available services
        clients = []

        if service_id:
            try:
                selected_service = Service.objects.get(id=service_id)
                clients = ClientService.objects.filter(
                    service=selected_service).select_related('client').order_by("client__name")
            except Service.DoesNotExist:
                selected_service = None
        count = len(clients)
        return render(request, 'client/client_services.html', {
            'services': services,
            'clients': clients,
            "count": count
        })
