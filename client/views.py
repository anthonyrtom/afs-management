from .models import ClientFinancialYear
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from . models import Client, FinancialYear, ClientType, VatCategory, VatSubmissionHistory, Service, ClientService
from users.models import JobTitle, CustomUser
from . forms import ClientFilterForm, AccountantFilterForm, ClientFinancialYear, CompletedAFSsForm, MissingAFSsForm, UserSearchForm, VatCategoryForm, VatClientsByMonthForm, VatClientsPeriodProcess, VatSubmissionUpdateForm, ClientFinancialYearProcessForm, ClientFinancialYearUpdateForm, CreateandViewVATForm, ClientFinancialYearGetForm, ClientForMonthForm, FilterByServiceForm


@login_required
def dashboard(request):
    headers = [c_type.name for c_type in ClientType.objects.all()]

    today = datetime.date(datetime.now())
    last_vat_month_date = today - relativedelta(months=1)
    data_list = []
    total_all = 0
    total_vendors = 0
    total_curr_vendors = 0
    total_cipc = 0
    total_curr_cipc = 0
    total_afs = 0
    total_curr_afs = 0
    total_provs = 0
    total_curr_provs = 0

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
            datadict = {}
            datadict["name"] = name
            datadict["count_all"] = count
            total_all += count

            cipc_count = sum(
                1 for cipc in cipc_clients if cipc.client_type.name == client_type.name and ClientService.is_service_offered(cipc.id, cipc_service.id, today) and cipc.is_client_cipc_reg_eligible())
            datadict["cipc_count"] = cipc_count
            total_cipc += cipc_count

            curr_cipc_count = sum(
                1 for cipc in cipc_clients if cipc.client_type == client_type and ClientService.is_service_offered(cipc.id, cipc_service.id, today) and cipc.is_client_cipc_reg_eligible() and cipc.get_birthday_in_year(today.year) and (cipc.get_birthday_in_year(today.year).month == today.month))

            datadict["curr_cipc_count"] = curr_cipc_count
            total_curr_cipc += curr_cipc_count

            vendor_count = sum(
                1 for vendor in all_vat_vendors
                if vendor.client_type == client_type and vendor.is_vat_vendor(as_at_date=today, service_name="Vat Submission")
            )
            datadict["vendor_count"] = vendor_count
            total_vendors += vendor_count

            curr_vendor_count = sum(
                1 for vendor in vat_vendors_due_this_month if vendor.client_type == client_type and vendor.is_vat_vendor(as_at_date=today, service_name="Vat Submission")
            )
            datadict["curr_vendor_count"] = curr_vendor_count
            total_curr_vendors += curr_vendor_count

            afs_count = sum(
                1 for client in afs_clients if client.client_type == client_type)
            datadict["afs_count"] = afs_count
            total_afs += afs_count

            curr_afs_count = sum(
                1 for client in afs_clients if client.client_type == client_type and client.month_end == today.month)
            datadict["curr_afs_count"] = curr_afs_count
            total_curr_afs += curr_afs_count

            prov_count = sum(
                1 for client in prov_clients if client.client_type == client_type)
            datadict["prov_count"] = prov_count
            total_provs += prov_count

            curr_prov_count = sum(
                1 for client in prov_clients if client.client_type == client_type and (client.is_first_prov_tax_month(today) or client.is_second_prov_tax_month(today)))
            datadict["curr_prov_count"] = curr_prov_count
            total_curr_provs += curr_prov_count

            data_list.append(datadict)

        return render(request, "client/dashboard.html", {
            "headers": headers,
            "data_list": data_list,
            "total_all": total_all,
            "total_vendors": total_vendors,
            "total_curr_vendors": total_curr_vendors,
            "total_cipc": total_cipc,
            "total_curr_cipc": total_curr_cipc,
            "total_afs": total_afs,
            "total_curr_afs": total_curr_afs,
            "total_provs": total_provs,
            "total_curr_provs": total_curr_provs
        })
    except Exception as e:
        print(e)
        messages.error(request, "There was an error")
        return redirect(reverse('home'))


@login_required
def dashboard_list(request, filter_type, client_type):
    query = request.GET.get("q", "")
    today = date.today()
    clients = Client.objects.all().order_by("name")

    clients = clients.filter(client_type__name=client_type)
    cipc_service = Service.objects.get(name="Cipc Returns")

    if filter_type == "all_clients":
        pass

    if query:
        clients = clients.filter(name__icontains=query)

    elif filter_type == "vat_vendors":
        clients = [client for client in clients if client.is_vat_vendor(
            today, "Vat Submission")]

    elif filter_type == "current_vat_vendors":
        last_month = today - relativedelta(months=1)
        clients = Client.get_vat_clients_for_month(
            last_month.strftime("%B")).filter(client_type__name=client_type)
        clients = [client for client in clients if client.is_vat_vendor(
            today, "Vat Submission")]

    elif filter_type == "afs_clients":
        clients = Client.get_afs_clients(today)
        clients = [
            client for client in clients if client.client_type.name == client_type]

    elif filter_type == "current_afs_clients":
        clients = Client.get_afs_clients(today, today.month, client_type)

    elif filter_type == "prov_tax_clients":
        clients = Client.get_prov_tax_clients(
            today, client_type=client_type)

    elif filter_type == "curr_prov_tax_clients":
        clients = Client.get_prov_tax_clients(
            today, month=today.month, client_type=client_type)

    elif filter_type == "cipc_clients":
        clients = Client.get_clients_of_type(
            "Cipc Returns", today)
        # service = ClientService.objects.filter()
        clients = [
            client for client in clients if client.client_type.name == client_type and ClientService.is_service_offered(client.id, cipc_service.id, today) and client.is_client_cipc_reg_eligible()]

    elif filter_type == "current_cipc_clients":
        clients = Client.get_clients_of_type(
            "Cipc Returns", today)
        clients = [client for client in clients if ClientService.is_service_offered(client.id, cipc_service.id, today) and client.get_birthday_in_year(
            today.year) and client.get_birthday_in_year(today.year).month == today.month and client.client_type.name == client_type]

    return render(request, "client/dashboard_list.html", {
        "clients": clients,
        "filter_type": filter_type.replace("_", " ").title(),
        "client_type": client_type,
        "query": query,
        "count": len(clients)
    })


@login_required
def view_service_overview(request):
    form = FilterByServiceForm(request.GET or None)
    is_form_bound = False
    if form.is_valid():
        is_form_bound = True
        search_term = form.cleaned_data.get("query", None)
        selected_a_service = form.cleaned_data["select_a_service"]
        month = form.cleaned_data["month"]
        client_type = form.cleaned_data["client_type"]

        today = date.today()

        if selected_a_service == "vat clients":
            clients = Client.get_vat_clients_for_month(
                month=month, filter_q=search_term)
            if client_type != "all":
                clients = clients.filter(client_type__name=client_type)
            clients = [client for client in clients if client.is_vat_vendor(
                today, "Vat Submission")]

        elif selected_a_service == "financial statements clients":
            if month == "all":
                month = None
            else:
                month = settings.MONTHS_LIST.index(month) + 1
            if client_type == "all":
                client_type = None

            clients = Client.get_afs_clients(
                today, month=month, client_type=client_type, filter_q=search_term)
        elif selected_a_service == "provisional tax clients":
            if month == "all":
                month = None
            else:
                month = settings.MONTHS_LIST.index(month) + 1
            if client_type == "all":
                client_type = None

            clients = Client.get_prov_tax_clients(
                today, month=month, client_type=client_type, filter_q=search_term)
        elif selected_a_service == "cipc clients":
            cipc_service = Service.objects.get(name="Cipc Returns")

            clients = Client.get_clients_of_type(
                "Cipc Returns", today, search_term)
            # clients = [client for client in clients if ClientService.is_service_offered(
            #     client.id, cipc_service.id, today)]
            if client_type != "all":
                clients = [
                    client for client in clients if client.client_type.name == client_type]
            if month != "all":
                month = settings.MONTHS_LIST.index(month) + 1
                clients = [client for client in clients if client.get_birthday_in_year(
                    today.year) and client.get_birthday_in_year(today.year).month == month]
        count = len(clients)
        headers = ["Name", "Registration Number"]
        return render(request, "client/service_overview.html", {"form": form, "clients": clients, "is_form_bound": is_form_bound, "count": count, "headers": headers})
    return render(request, "client/service_overview.html", {"form": form, "is_form_bound": is_form_bound})


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
def get_finished_or_scheduled_afs(request):
    form = ClientFinancialYearGetForm(request.GET or None)
    data = False
    query = request.GET.get("q", "").strip()
    if form.is_valid():
        data = True
        financial_year = form.cleaned_data["financial_year"]
        afs_done = form.cleaned_data.get("afs_done", False)
        itr34c_issued = form.cleaned_data.get("itr34c_issued", False)
        wp_done = form.cleaned_data.get("wp_done", False)
        posting_done = form.cleaned_data.get("posting_done", False)
        client_invoiced = form.cleaned_data.get("client_invoiced", False)

        financials = ClientFinancialYear.objects.filter(
            financial_year=financial_year).order_by("client__name")

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

        if query:
            financials = financials.filter(client__name__icontains=query)
        today = date.today()
        all_afs_eligible_clients = Client.get_afs_clients(today)
        total = len(all_afs_eligible_clients)
        count = len(financials)

        headers = ["Name", "Fin Year", "Schedule Date", "Finish Date"]
        return render(request, "client/filtered_financials.html", {"financials": financials, "count": count, "total": total, "headers": headers, "form": form, "data": data})
    return render(request, "client/filtered_financials.html", {"form": form, "data": data})


@login_required
def scheduled_financials(request):
    form = ClientFinancialYearGetForm(request.POST or None)
    data = False
    if form.is_valid():
        query = request.GET.get("q", "").strip()
        data = True
        financial_year = form.cleaned_data["financial_year"]
        scheduled = ClientFinancialYear.objects.filter(
            schedule_date__isnull=False, finish_date__isnull=True, financial_year=financial_year).order_by("client__name")
        if query:
            scheduled = scheduled.filter(client__name__icontains=query)
        count = len(scheduled)
        today = date.today()
        total = len(Client.get_afs_clients(today))
        headers = ["Name", "Fin Year", "Schedule Date", "Finish Date"]
        return render(request, "client/scheduled_financials.html", {"scheduled": scheduled, "count": count, "total": total, "headers": headers, "data": data})

    return render(request, "client/scheduled_financials.html", {"form": form, "data": data})


@login_required
def completed_financials_month(request):
    form = CompletedAFSsForm(request.GET or None)
    finished_afs = []
    count = 0
    month = request.GET.get("month")
    query = request.GET.get("q", "").strip()
    headers = ["Client Name", "Financial Year", "Start Date", "Finish Date"]

    if form.is_valid():
        month = int(form.cleaned_data["month"])
        finished_afs = ClientFinancialYear.objects.filter(
            finish_date__month=month
        ).order_by("client__name")

        if query:
            finished_afs = finished_afs.filter(client__name__icontains=query)

        count = finished_afs.count()

    return render(request, "client/finished_financials_month.html", {
        "finished_afs": finished_afs,
        "month": month,
        "headers": headers,
        "count": count,
        "form": form,
        "query": query,
    })


@login_required
def get_unfinished_financials(request):
    form = MissingAFSsForm(request.GET or None)
    data = False
    first_time = True
    query = request.GET.get("q", "").strip()

    if form.is_valid():
        data = True
        first_time = False
        client = form.cleaned_data.get("client_select", None)
        year = int(form.cleaned_data["year"])
        client_data = []
        today = datetime.now()

        clients = Client.objects.all().order_by("name")
        if client:
            clients = clients.filter(id=client.id)
        elif query:
            clients = clients.filter(name__icontains=query)

        counter = 0
        for curr_client in clients:
            if curr_client.is_afs_client(today) and curr_client.is_year_after_afs_first(year, today):
                counter += 1
                financial_year = FinancialYear.objects.filter(
                    the_year=year).first()
                has_record = ClientFinancialYear.objects.filter(
                    client=curr_client,
                    financial_year=financial_year,
                    afs_done=True
                ).exists()
                if not has_record:
                    client_data.append({
                        "client": curr_client,
                        "status": "NO"
                    })

        count = len(client_data)
        return render(request, "client/unfinished_financials.html", {
            "client_data": client_data,
            "year": year,
            "data": data,
            "first_time": first_time,
            "count": count,
            "counter": counter,
            "form": form,
            "query": query
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
def search_clients(request):
    form = ClientFilterForm(request.GET or None)
    clients = Client.objects.all().order_by("name")
    count = len(clients)

    if form.is_valid():
        query = form.cleaned_data.get("query", "")

        if query:
            clients = clients.filter(
                Q(name__icontains=query)
            )
        client_type = form.cleaned_data.get("client_type", "")
        if client_type != "all":
            clients = clients.filter(client_type__name=client_type)

        headers = ["Name", "Internal No.", "Reg Number", "Type", "Year End"]
        count = len(clients)
        return render(request, "client/found_clients.html", {"form": form, "clients": clients, "count": count, "headers": headers})
    return render(request, "client/found_clients.html", {"form": form, "clients": clients, "count": count})


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


@login_required
@permission_required("client.can_change", raise_exception=True)
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
        radio_option = form.cleaned_data["radio_option"]

        vat_clients = []
        if radio_option == "complete":
            vat_clients = VatSubmissionHistory.objects.filter(
                year=year, submitted=True, client_notified=True, paid=True).order_by("client__name")
        elif radio_option == "incomplete":
            vat_clients = VatSubmissionHistory.objects.filter(
                year=year, submitted=False, client_notified=False, paid=False).order_by("client__name")
        else:
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
        metrics = {}
        metrics["submitted"] = len(vat_clients.filter(submitted=True))
        metrics["client_notified"] = len(
            vat_clients.filter(client_notified=True))
        metrics["paid"] = len(vat_clients.filter(paid=True))

        headers = ["Mark Complete", "Name", "Period", "Submitted",
                   "Client Notified", "Paid", "Comment", "Update Comment"]
        search_query = request.POST.get("search")
        if search_query:
            vat_clients = vat_clients.filter(
                client__name__icontains=search_query)

        count = len(vat_clients)
        return render(request, "client/vat_clients_list.html", {
            "vat_clients": vat_clients,
            "headers": headers, "count": count,
            "metrics": metrics,
            "form": form,
        })

    return render(request, "client/vat_clients_form.html", {"form": form})


@require_POST
@login_required
def ajax_update_comment(request):
    client_id = request.POST.get("client_id")
    comment = request.POST.get("comment", "")

    try:
        client = VatSubmissionHistory.objects.get(id=client_id)
        client.comment = comment
        # client.schedule_date = schedule_date
        client.save()
        return JsonResponse({"success": True})
    except VatSubmissionHistory.DoesNotExist:
        return JsonResponse({"success": False, "error": "Client not found"})


@require_POST
@login_required
def ajax_update_vat_status(request):
    client_id = request.POST.get("client_id")

    try:
        client = VatSubmissionHistory.objects.get(id=client_id)

        # Check for individual field update
        # This block should be first to handle the most common case from single checkboxes
        if "field" in request.POST and "value" in request.POST:
            field_name = request.POST.get("field")
            # Convert 'true'/'false' string to boolean
            value = request.POST.get("value") == 'true'

            # Ensure the field name is one we expect to update for security
            if field_name in ['submitted', 'client_notified', 'paid']:
                setattr(client, field_name, value)
                client.save()
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "Invalid field name"})

        # Support bulk update (from mark-complete checkbox)
        # This block will only execute if 'field' and 'value' are NOT present (i.e., it's a bulk update)
        # Or, you can make this an 'elif' if you want to prioritize the individual update
        updated_any_field_in_bulk = False
        for field in ['submitted', 'client_notified', 'paid']:
            if field in request.POST:
                value = request.POST.get(field) == 'true'
                setattr(client, field, value)
                updated_any_field_in_bulk = True

        if updated_any_field_in_bulk:
            client.save()
            return JsonResponse({"success": True})
        else:
            # If no specific 'field' or known bulk fields were in the POST,
            # it might be an invalid request or missing parameters.
            return JsonResponse({"success": False, "error": "No valid fields to update specified"})

    except VatSubmissionHistory.DoesNotExist:
        return JsonResponse({"success": False, "error": "Client not found"})
    except Exception as e:
        # Catch any other unexpected errors
        return JsonResponse({"success": False, "error": f"An error occurred: {str(e)}"})


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
        accountant = form.cleaned_data['accountant']
        radio_input = form.cleaned_data["radio_input"]

        financial_clients = []
        if radio_input == "complete":
            financial_clients = ClientFinancialYear.objects.filter(
                financial_year=financial_year, wp_done=True, afs_done=True, posting_done=True, itr34c_issued=True).order_by("client__name")
        elif radio_input == "incomplete":
            financial_clients = ClientFinancialYear.objects.filter(
                financial_year=financial_year, wp_done=False, afs_done=False, posting_done=False, itr34c_issued=False).order_by("client__name")
        else:
            financial_clients = ClientFinancialYear.objects.filter(
                financial_year=financial_year).order_by("client__name")

        if client and client != "all":
            financial_clients = financial_clients.filter(client=client)

        if accountant:
            financial_clients = financial_clients.filter(
                client__accountant=accountant)
        metrics = {}
        metrics["wp_done"] = len(financial_clients.filter(wp_done=True))
        metrics["afs_done"] = len(financial_clients.filter(afs_done=True))
        metrics["posting_done"] = len(
            financial_clients.filter(posting_done=True))
        metrics["itr34c_issued"] = len(
            financial_clients.filter(itr34c_issued=True))
        metrics["client_invoiced"] = len(
            financial_clients.filter(client_invoiced=True))

        headers = ["Mark Complete", "Client Name", "Financial Year", "Schedule Date",
                   "Finish Date", "WP Done", "AFS Done", "Posting Done", "ITR14", "Update"]
        search_query = request.POST.get("search")
        if search_query:
            financial_clients = financial_clients.filter(
                client__name__icontains=search_query)

        count = len(financial_clients)

        return render(request, "client/client_financial_years_list.html", {
            "client_financial_years": financial_clients,
            "headers": headers, "count": count,
            "metrics": metrics,
            "form": form,
        })

    return render(request, "client/client_financial_years_form.html", {"form": form})


@require_POST
@login_required
def ajax_update_afs_status(request):
    if request.method == "POST":
        client_id = request.POST.get("client_id")
        try:
            instance = ClientFinancialYear.objects.get(id=client_id)

            if 'field' in request.POST:
                # Single field update
                field = request.POST.get("field")
                value = request.POST.get("value") == "true"
                if hasattr(instance, field):
                    setattr(instance, field, value)
                else:
                    return JsonResponse({"success": False, "error": f"Invalid field: {field}"})
            else:
                # Bulk update for "mark-complete"
                for field in ['wp_done', 'afs_done', 'posting_done', 'itr34c_issued']:
                    val = request.POST.get(field)
                    if val is not None:
                        setattr(instance, field, val == "true")

            instance.save()
            return JsonResponse({"success": True})

        except ClientFinancialYear.DoesNotExist:
            return JsonResponse({"success": False, "error": "Client not found"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method"})


@require_POST
@login_required
def ajax_update_afs_comment(request):
    if request.method == "POST":
        client_id = request.POST.get("client_id")
        comment = request.POST.get("comment", "").strip()
        schedule_date_str = request.POST.get(
            "scheduleDate", None)
        finish_date_str = request.POST.get(
            "finishDate", None)
        schedule_date_obj = None
        finish_date_obj = None

        if schedule_date_str:
            try:

                schedule_date_obj = datetime.strptime(
                    schedule_date_str, "%Y-%m-%d").date()

            except ValueError:
                # Handle cases where the date string might not be in the expected format
                return JsonResponse({"success": False, "error": "Invalid date format. Expected YYYY-MM-DD."})
        if finish_date_str:
            try:
                finish_date_obj = datetime.strptime(
                    finish_date_str, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"success": False, "error": "Invalid date format. Expected YYYY-MM-DD."})
        try:
            instance = ClientFinancialYear.objects.get(id=client_id)
            instance.comment = comment
            if (finish_date_obj and schedule_date_obj) and (finish_date_obj < schedule_date_obj):
                return JsonResponse({"success": False, "error": "Finish date ca not be before start date, nothing saved"})
            instance.schedule_date = schedule_date_obj
            instance.finish_date = finish_date_obj
            instance.save()
            return JsonResponse({"success": True})

        except ClientFinancialYear.DoesNotExist:  # More specific error for not found
            return JsonResponse({"success": False, "error": "ClientFinancialYear instance not found."})
        except Exception as e:
            # Catch other potential errors during save or database interaction
            return JsonResponse({"success": False, "error": str(e)})

    # Use a more specific error message
    return JsonResponse({"success": False, "error": "Invalid request method."})


@login_required
def update_client_financial_year(request):
    """Handles updating the financial year entry."""
    if request.method == "POST" and 'client_id' in request.POST:
        client_id = request.POST.get('client_id')
        client_instance = get_object_or_404(ClientFinancialYear, id=client_id)

        update_form = ClientFinancialYearUpdateForm(
            request.POST, instance=client_instance)
        # print("POST data keys:", request.POST.keys())
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
                   "Month End", "VAT No", "Accountant"]
        count = len(clients)
        return render(request, "client/clients_with_monthend.html", {"clients": clients, "headers": headers, "count": count, "total": len(Client.objects.all()), "month": month.title()})
    return render(request, "client/clients_with_monthend.html", {"form": form})


class ClientServiceListView(LoginRequiredMixin, View):
    def get(self, request):
        service_id = request.GET.get('service')
        query = request.GET.get('q', "").strip()
        services = Service.objects.all()
        clients = []

        if service_id:
            try:
                selected_service = Service.objects.get(id=service_id)
                clients = ClientService.objects.filter(
                    service=selected_service
                ).select_related('client').order_by("client__name")

                if query:
                    clients = clients.filter(client__name__icontains=query)

            except Service.DoesNotExist:
                selected_service = None

        count = len(clients) if hasattr(clients, 'count') else len(clients)

        return render(request, 'client/client_services.html', {
            'services': services,
            'clients': clients,
            'count': count
        })


"""
The below view is for more than one financial year
"""
# @login_required
# def get_unfinished_financials(request):
#     form = MissingAFSsForm(request.GET or None)
#     data = False
#     first_time = True
#     query = request.GET.get("q", "").strip()

#     if form.is_valid():
#         data = True
#         first_time = False
#         client = form.cleaned_data.get("client_select", None)
#         start_year = int(form.cleaned_data["start_year"])
#         end_year = int(form.cleaned_data["end_year"])

#         if start_year > end_year:
#             start_year, end_year = end_year, start_year

#         missing_years = list(range(start_year, end_year + 1))
#         client_data = []
#         today = datetime.now()

#         # Initial queryset
#         clients = Client.objects.all().order_by("name")

#         if client:
#             clients = clients.filter(id=client.id)
#         elif query:
#             clients = clients.filter(name__icontains=query)

#         counter = 0
#         for curr_client in clients:
#             if curr_client.is_afs_client(today):
#                 for year in missing_years:
#                     if curr_client.is_year_after_afs_first(year, today):
#                         counter += 1
#                         row = [curr_client.name]
#                         financial_year = FinancialYear.objects.filter(
#                             the_year=year).first()
#                         has_record = ClientFinancialYear.objects.filter(
#                             client=curr_client, financial_year=financial_year, afs_done=True
#                         ).exists()
#                         if not has_record:
#                             row.append("NO")
#                             client_data.append(row)

#         count = len(client_data)
#         headers = ["Client Name"] + missing_years

#         return render(request, "client/unfinished_financials.html", {
#             "client_data": client_data,
#             "headers": headers,
#             "data": data,
#             "first_time": first_time,
#             "count": count,
#             "counter": counter,
#             "form": form,
#             "query": query
#         })

#     return render(request, "client/unfinished_financials.html", {
#         "form": form,
#         "first_time": first_time,
#     })
"""
End of method for two financial years
"""

# @login_required
# def process_client_financial_years(request):
#     """Handles the form selection and renders the results."""
#     form = ClientFinancialYearProcessForm(request.POST or None)

#     if form.is_valid():
#         client = form.cleaned_data['client']
#         financial_year = form.cleaned_data['financial_year']

#         client_financial_years = ClientFinancialYear.objects.filter(
#             financial_year=financial_year
#         ).order_by("client__name")
#         if client:
#             client_financial_years = client_financial_years.filter(
#                 client=client)

#         headers = ["Client Name", "Financial Year", "Schedule Date",
#                    "Finish Date", "WP Done", "AFS Done", "Posting Done", "ITR14", "Update"]
#         count = len(client_financial_years)
#         return render(request, "client/client_financial_years_list.html", {
#             "client_financial_years": client_financial_years,
#             "headers": headers, "count": count
#         })

#     return render(request, "client/client_financial_years_form.html", {"form": form})
