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
    all_clients = Client.objects.all().order_by("name")
    headers = ["Client Name", "Client Type",
               "Month End", "VAT No", "Accountant"]
    count = len(all_clients)
    return render(request, "client/all_clients.html", {"clients": all_clients, "headers": headers, "count": count})


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
        total = len(clients)
        clients = clients.filter(**filter_kwargs)
        clients = clients.order_by("name")
        count = len(clients)
        headers = ["Client Name", "Client Type",
                   "Month End", "VAT No"]
        field = field.replace("_", " ")
        return render(request, 'client/filtered_clients.html', {'form': form, "clients": clients, "statutory_type": field, "with_without": with_without, "headers": headers, "count": count, "total": total})
    else:
        return render(request, 'client/get_clients.html', {'form': form})


@login_required
def filter_clients_by_accountant(request):
    form = AccountantFilterForm()
    clients = None
    count = 0
    headers = ["Client Name", "Client Type",
               "Month End", "VAT No", "Accountant"]
    if 'accountant' in request.GET:
        form = AccountantFilterForm(request.GET)
        if form.is_valid():
            accountant = form.cleaned_data['accountant']
            clients = Client.objects.filter(
                accountant=accountant).order_by("name")
            count = len(clients)
    return render(request, 'client/accountant_clients.html', {
        'form': form if CustomUser.objects.filter(clients__isnull=False).exists() else None,
        'clients': clients, "headers": headers, "count": count
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
def search_clients(request):
    form = ClientSearchForm(request.GET or None)
    clients = Client.objects.all().order_by("name")  # Default to all clients
    count = 0

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
    count = len(clients)
    return render(request, "client/search_clients.html", {"form": form, "clients": clients, "count": count})


@login_required
def get_all_accountants(request):
    accountant = JobTitle.objects.filter(title="Accountant").first()
    count = 0
    if accountant:
        accountants = CustomUser.objects.filter(
            job_title=accountant).order_by("email")
        count = len(accountants)
        return render(request, "client/accountants.html", {"accountants": accountants, "count": count})
    return render(request, "client/accountants.html")


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
    if form.is_valid():
        selected_category = form.cleaned_data["vat_category"]
        selected_accountant = form.cleaned_data["accountant"]

        clients = Client.get_vat_clients_for_category(
            selected_category.vat_category if selected_category else None,
            selected_accountant if selected_accountant else None
        ).order_by("name")

        headers = ["Client Name", "Client Type",
                   "Month End", "VAT No", "Accountant", "Category"]
        count = len(clients)
        return render(request, "client/vat_client_for_category.html", {
            "clients": clients,
            "headers": headers,
            "vat_category": selected_category,
            "selected_accountant": selected_accountant, "count": count
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
        count = len(clients)
        return render(request, "client/vat_clients_for_month.html", {
            "clients": clients,
            "month": month.title() if month else "All",
            "selected_accountant": selected_accountant,
            "headers": headers, "count": count
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
