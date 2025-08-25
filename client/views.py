from django.views.generic import ListView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django import forms
from django.db.models import Q
from django.utils import timezone
from .models import ClientFinancialYear
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import View
from . models import Client, FinancialYear, ClientType, VatCategory, VatSubmissionHistory, Service, ClientService, ClientCipcReturnHistory, ClientProvisionalTax
from utilities.helpers import construct_client_dict, calculate_unique_days_from_dict, calculate_max_days_from_dict, get_client_model_fields, export_to_csv, get_optional_fields_for_client
from users.models import CustomUser
from . forms import ClientFinancialYear, UserSearchForm, VatClientSearchForm,  VatClientsPeriodProcess, ClientFinancialYearProcessForm, CreateandViewVATForm,  FilterByServiceForm, ClientFilter, FilterFinancialClient, FilterAllFinancialClient, BookServiceForm, FinancialProductivityForm, CreateUpdateProvCipcForm, ClientServiceForm, VatClientPeriodUpdateForm


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
                1 for cipc in cipc_clients if cipc.client_type and cipc.client_type.name == client_type.name and ClientService.is_service_offered(cipc.id, cipc_service.id, today) and cipc.is_client_cipc_reg_eligible())
            datadict["cipc_count"] = cipc_count
            total_cipc += cipc_count

            curr_cipc_count = sum(
                1 for cipc in cipc_clients if cipc.client_type and cipc.client_type == client_type and ClientService.is_service_offered(cipc.id, cipc_service.id, today) and cipc.is_client_cipc_reg_eligible() and cipc.get_birthday_in_year(today.year) and (cipc.get_birthday_in_year(today.year).month == today.month))

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
            client for client in clients if client.client_type and client.client_type.name == client_type]

    elif filter_type == "current_afs_clients":
        clients = Client.get_afs_clients(today, today.month, client_type)

    elif filter_type == "prov_tax_clients":
        clients = Client.get_prov_tax_clients(
            today, client_type=client_type)

    elif filter_type == "curr_prov_tax_clients":
        clients = Client.get_prov_tax_clients(
            today, client_type=client_type)
        clients = [client for client in clients if client.is_first_prov_tax_month(
            today) or client.is_second_prov_tax_month(today)]

    elif filter_type == "cipc_clients":
        clients = Client.get_clients_of_type(
            "Cipc Returns", today)

        clients = [
            client for client in clients if client.client_type and client.client_type.name == client_type and ClientService.is_service_offered(client.id, cipc_service.id, today) and client.is_client_cipc_reg_eligible()]

    elif filter_type == "current_cipc_clients":
        clients = Client.get_clients_of_type(
            "Cipc Returns", today)
        clients = [client for client in clients if ClientService.is_service_offered(client.id, cipc_service.id, today) and client.get_birthday_in_year(
            today.year) and client.get_birthday_in_year(today.year).month == today.month and client.client_type and client.client_type.name == client_type]
    if request.GET.get("export") == "csv":
        headers = ["Name", "Registration Number",
                   "Internal ID", "CIPC Birthday", "Accountant"]
        rows = [
            [c.get_client_full_name(), c.entity_reg_number, c.internal_id_number,
             c.birthday_of_entity, c.accountant]
            for c in clients
        ]
        return export_to_csv("dashboard_export.csv", headers, rows)

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
        search_term = form.cleaned_data.get("searchterm", None)
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

            if client_type != "all":
                clients = [
                    client for client in clients if client.client_type.name == client_type]
            if month != "all":
                month = settings.MONTHS_LIST.index(month) + 1
                clients = [client for client in clients if client.get_birthday_in_year(
                    today.year) and client.get_birthday_in_year(today.year).month == month]
        if request.GET.get("export") == "csv":
            headers_export = ["Name", "Registration Number",
                              "Internal ID", "Client Type"]
            rows = [
                [c.get_client_full_name(), c.entity_reg_number,
                 c.internal_id_number, c.client_type.name]
                for c in clients
            ]
            return export_to_csv(f"{selected_a_service}_clients_export.csv", headers_export, rows)

        count = len(clients)
        headers = ["Name", "Registration Number"]
        return render(request, "client/service_overview.html", {"form": form, "clients": clients, "is_form_bound": is_form_bound, "count": count, "headers": headers})
    return render(request, "client/service_overview.html", {"form": form, "is_form_bound": is_form_bound})


@login_required
def reports(request):
    return render(request, "client/reports.html")


@login_required
def view_all_clients(request):
    form = ClientFilter(request.GET or None)
    if form.is_valid():
        client_type = form.cleaned_data.get("client_type", None)
        accountant = form.cleaned_data.get("accountant", None)
        service_offered = form.cleaned_data.get("service_offered", None)
        year_end = form.cleaned_data.get("year_end", None)

        all_clients = Client.objects.all().order_by("name")
        if client_type and client_type != "all":
            all_clients = all_clients.filter(
                client_type__id=client_type)
        if accountant and accountant != "all":
            all_clients = all_clients.filter(
                accountant__id=accountant)
        if service_offered and service_offered != "all":
            all_clients = all_clients.filter(
                client_service__id=service_offered).distinct()
        if year_end and year_end != "all":
            month = settings.MONTHS_LIST.index(year_end) + 1
            all_clients = all_clients.filter(month_end=month)

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
        if request.GET.get("export") == "csv":
            headers_export = ["Name", "Registration Number",
                              "Internal ID", "First Year AFS", "Accountant", "Year End"]
            rows = [
                [c.get_client_full_name(), c.entity_reg_number,
                 c.internal_id_number, c.first_financial_year, c.accountant, c.get_month_end_as_string(), ]
                for c in all_clients
            ]
            return export_to_csv("all_clients_export.csv", headers_export, rows)

        count = len(all_clients)
        return render(request, "client/all_clients.html", {"clients": all_clients, "headers": headers, "count": count, "form": form})
    return render(request, "client/all_clients.html", {"form": form})


@login_required
def scheduled_financials(request):
    form = FilterFinancialClient(request.GET or None)
    data = False
    if form.is_valid():
        client_type = form.cleaned_data["client_type"]
        query = form.cleaned_data["searchterm"]
        data = True
        year = form.cleaned_data["year"]
        accountant = form.cleaned_data["accountant"]
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
        scheduled = []
        if year != "all":
            scheduled = ClientFinancialYear.objects.filter(
                schedule_date__range=(start_date, end_date),  financial_year=year).order_by("client__name")
        else:
            scheduled = ClientFinancialYear.objects.filter(
                schedule_date__range=(start_date, end_date)).order_by("client__name")
        if query:
            scheduled = scheduled.filter(client__name__icontains=query)
        if accountant != "all":
            scheduled = scheduled.filter(client__accountant=accountant)
        if client_type != "all":
            scheduled = scheduled.filter(client__client_type=client_type)
        count = len(scheduled)
        today = date.today()
        afs_complete = len(scheduled.filter(finish_date__isnull=False))
        itr14_complete = len(scheduled.filter(itr14_date__isnull=False))
        invoiced = len(scheduled.filter(invoice_date__isnull=False))
        if not count:
            data = False
        unique_years = sorted(
            {obj.financial_year.the_year for obj in scheduled if obj.financial_year},
            reverse=True
        )
        if request.GET.get("export") == "csv":
            headers = ["Name", "Registration Number", "Internal ID",
                       "Year", "Schedule Date", "AFSs Finish Date", "Sec Start Date", "Sec Finish Date", "ITR14 Start Date", "ITR14 Finish Date", "Invoice Date"]
            rows = [
                [c.client.get_client_full_name(), c.client.entity_reg_number,
                 c.client.internal_id_number, c.financial_year.the_year, c.schedule_date, c.finish_date, c.secretarial_start_date, c.secretarial_finish_date, c.itr14_start_date, c.itr14_date, c.invoice_date]
                for c in scheduled
            ]
            return export_to_csv("scheduled_export.csv", headers, rows)

        headers = ["Name", "Fin Year", "Schedule Date",
                   "Financials Status", "ITR14 Status", "Invoicing Status"]
        return render(request, "client/scheduled_financials.html", {"clients": scheduled, "count": count, "afs_complete": afs_complete, "headers": headers, "data": data, "itr14_complete": itr14_complete, "invoiced": invoiced, "form": form, "unique_years": unique_years, })

    return render(request, "client/scheduled_financials.html", {"form": form, "data": data})


@login_required
def financials_progress(request):
    form = FilterAllFinancialClient(request.GET or None)
    data = []
    headers = ["Client Name", "Year",
               "Scheduled Date", "AFS", "ITR14", "Invoice"]
    unique_years = set()
    afs_complete = itr14_complete = invoiced = 0
    is_valid = False
    if form.is_valid():
        selected_year_ids = form.cleaned_data.get("years", [])
        accountants = form.cleaned_data.get("accountant", [])
        searchterm = form.cleaned_data.get("searchterm", "")
        month = form.cleaned_data.get("month", [])
        client_type = form.cleaned_data.get("client_type", [])

        month = list(map(int, month))

        client_type = list(map(int, client_type))
        is_valid = True
        today = datetime.now().date()

        selected_year_ids = list(map(int, selected_year_ids))
        financial_years = FinancialYear.objects.filter(
            id__in=selected_year_ids)

        valid_clients = [
            c for c in Client.objects.all() if c.is_afs_client(today) and c.month_end in month]

        data = ClientFinancialYear.objects.filter(
            client__in=valid_clients, financial_year__in=financial_years, client__client_type__id__in=client_type)
        if "None" in accountants:
            accountant_ids_list = [int(aid)
                                   for aid in accountants if aid != 'None']
            data = data.filter(
                Q(client__accountant__isnull=True) | Q(
                    client__accountant__id__in=accountant_ids_list)
            )
        else:
            accountant_ids_list = [int(aid) for aid in accountants]
            data = data.filter(client__accountant__id__in=accountant_ids_list)
        if searchterm:
            data = data.filter(
                client__name__icontains=searchterm)
        unique_years = sorted(
            set(r.financial_year.the_year for r in data), reverse=True)

        afs_complete = sum(1 for r in data if r.finish_date)
        itr14_complete = sum(1 for r in data if r.itr14_date)
        invoiced = sum(1 for r in data if r.invoice_date)

        if request.GET.get("export") == "csv":
            headers = ["Name", "Registration Number", "Internal ID",
                       "Year", "Schedule Date", "AFSs Finish Date", "Sec Start Date", "Sec Finish Date", "ITR14 Start Date", "ITR14 Finish Date", "Invoice Date"]
            rows = [
                [c.client.get_client_full_name(), c.client.entity_reg_number,
                 c.client.internal_id_number, c.financial_year.the_year, c.schedule_date, c.finish_date, c.secretarial_start_date, c.secretarial_finish_date, c.itr14_start_date, c.itr14_date, c.invoice_date]
                for c in data
            ]
            return export_to_csv("All_AFS_progress_export.csv", headers, rows)

    return render(request, "client/financials_progress.html", {
        "form": form,
        "clients": data,
        "scheduled": data,
        "count": len(data),
        "headers": headers,
        "unique_years": unique_years,
        "afs_complete": afs_complete,
        "itr14_complete": itr14_complete,
        "invoiced": invoiced,
        "is_valid": is_valid
    })


@login_required
def search_users(request):
    form = UserSearchForm(request.GET or None)
    users = CustomUser.objects.all().order_by("email")
    count = 0

    if form.is_valid():
        query = form.cleaned_data.get("searchterm", "")
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
def search_vat_clients(request):
    form = VatClientSearchForm(request.GET or None)
    clients = None
    count = 0
    headers = ["Client Name", "Client Type",
               "Month End", "VAT No", "Accountant", "Category"]
    searchterm = request.GET.get("searchterm", "")

    if form.is_valid():
        selected_category = form.cleaned_data["vat_category"]
        selected_accountant = form.cleaned_data["accountant"]
        month = form.cleaned_data["month"]
        client_type = form.cleaned_data["client_type"]

        clients = Client.objects.filter(
            vat_category__isnull=False).order_by("name")
        if selected_accountant and selected_accountant != "all":
            clients = clients.filter(accountant=selected_accountant)

        if searchterm:
            clients = clients.filter(
                Q(name__icontains=searchterm) |
                Q(surname__icontains=searchterm) |
                Q(vat_reg_number__icontains=searchterm)
            )
        if client_type and client_type != "all":
            clients = clients.filter(client_type=client_type)

        if selected_category and selected_category != "all":
            vat_cat = VatCategory.objects.get(id=selected_category)
            clients = clients.filter(vat_category=vat_cat)

        if month and month != "all":
            index = settings.MONTHS_LIST.index(month) + 1
            if month in ["january", "march", "may", "july", "september", "november"]:
                clients = clients.filter(
                    Q(vat_category__vat_category="A") |
                    Q(vat_category__vat_category="C") |
                    Q(vat_category__vat_category="E", month_end=index)
                )

            elif month in ["february", "august"]:
                clients = clients.filter(
                    Q(vat_category__vat_category="B") |
                    Q(vat_category__vat_category="C") |
                    Q(vat_category__vat_category="D") |
                    Q(vat_category__vat_category="E", month_end=index)
                )

            elif month in ["april", "june", "october", "december"]:
                clients = clients.filter(
                    Q(vat_category__vat_category="B") |
                    Q(vat_category__vat_category="C") |
                    Q(vat_category__vat_category="E", month_end=index)
                )
        if request.GET.get("export") == "csv":
            headers = ["Name", "Registration Number",
                       "Internal ID", "Vat Number"]
            rows = [
                [c.get_client_full_name(), c.entity_reg_number,
                 c.internal_id_number, c.vat_reg_number]
                for c in clients
            ]
            return export_to_csv("vat_export.csv", headers, rows)
        count = clients.count()

        return render(request, "client/search_vat_client.html", {
            "form": form,
            "clients": clients,
            "headers": headers,
            "vat_category": selected_category,
            "selected_accountant": selected_accountant,
            "searchterm": searchterm,
            "count": count
        })

    return render(request, "client/search_vat_client.html", {"form": form})


@login_required
def process_dashboard(request):
    return render(request, "client/process_dashboard.html")


@login_required
@permission_required("client.change_vatsubmissionhistory", raise_exception=True)
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

# deprecated
# @login_required
# def process_vat_clients_for_period(request):
#     """Handles form submission and displays filtered VAT clients."""
#     form = VatClientsPeriodProcess(request.GET or None)

#     if form.is_valid():
#         client = form.cleaned_data['client']
#         year = form.cleaned_data['year']
#         month = form.cleaned_data['month']
#         accountant = form.cleaned_data['accountant']
#         radio_option = form.cleaned_data["radio_option"]

#         vat_clients = []
#         if radio_option == "complete":
#             vat_clients = VatSubmissionHistory.objects.filter(
#                 year=year, submitted=True, client_notified=True, paid=True).order_by("client__name")
#         elif radio_option == "incomplete":
#             vat_clients = VatSubmissionHistory.objects.filter(
#                 year=year, submitted=False, client_notified=False, paid=False).order_by("client__name")
#         else:
#             vat_clients = VatSubmissionHistory.objects.filter(
#                 year=year).order_by("client__name")

#         if client and client != "all":
#             vat_clients = vat_clients.filter(client=client)
#         if month and month != "all":
#             month = month.lower()
#             month = settings.MONTHS_LIST.index(month) + 1
#             vat_clients = vat_clients.filter(month=month)
#         if accountant:
#             vat_clients = vat_clients.filter(client__accountant=accountant)
#         metrics = {}
#         metrics["submitted"] = len(vat_clients.filter(submitted=True))
#         metrics["client_notified"] = len(
#             vat_clients.filter(client_notified=True))
#         metrics["paid"] = len(vat_clients.filter(paid=True))

#         headers = ["Mark Complete", "Name", "Period", "Submitted",
#                    "Client Notified", "Paid", "Comment", "Update Comment"]
#         search_query = request.POST.get("search")
#         if search_query:
#             vat_clients = vat_clients.filter(
#                 client__name__icontains=search_query)
#         if request.GET.get("export") == "csv":
#             headers = ["Name", "Registration Number", "Internal ID",
#                        "Year", "Month", "Submitted", "Client Notified", "Client Paid", "Comment", "Marked Notified by", "Marked Submitted By", "Marked Paid By", "Date Submitted"]
#             rows = [
#                 [c.client.get_client_full_name(), c.client.vat_reg_number,
#                  c.client.internal_id_number, c.year.the_year, c.month.name, c.submitted, c.client_notified, c.paid, c.comment, c.marked_notified_by, c.marked_submitted_by, c.marked_paid_by, c.date_marked_submitted]
#                 for c in vat_clients
#             ]
#             return export_to_csv(f"vat_submission_{year}0{month}.csv", headers, rows)

#         count = len(vat_clients)
#         return render(request, "client/vat_clients_list.html", {
#             "clients": vat_clients,
#             "headers": headers, "count": count,
#             "metrics": metrics,
#             "form": form,
#         })

#     return render(request, "client/vat_clients_form.html", {"form": form})


@login_required
def update_vat_status_submission(request):
    """Handles form submission and displays filtered VAT clients."""
    form = VatClientPeriodUpdateForm(request.GET or None)

    if form.is_valid():
        client_type = form.cleaned_data['client_type']
        year = form.cleaned_data['year']
        month = form.cleaned_data['month']
        accountant = form.cleaned_data['accountant']
        radio_option = form.cleaned_data["radio_option"]

        client_type = list(map(int, client_type))
        year = int(year)
        month = int(month)

        fin_year = FinancialYear.objects.get(id=year)
        month_str = settings.MONTHS_LIST[(month-1)]
        returned_clients = VatSubmissionHistory.create_or_get_vat_clients(
            year=fin_year, month=month_str)

        vat_clients = VatSubmissionHistory.objects.filter(
            year=year, client__client_type_id__in=client_type, month=month).order_by("client__name")
        if radio_option == "complete":
            vat_clients = vat_clients.filter(
                submitted=True, client_notified=True, paid=True)
        elif radio_option == "incomplete":
            vat_clients = vat_clients.filter(
                year=year, submitted=False, client_notified=False, paid=False)

        if "None" in accountant:
            accountant_ids_list = [int(aid)
                                   for aid in accountant if aid != 'None']
            vat_clients = vat_clients.filter(
                Q(client__accountant__isnull=True) | Q(
                    client__accountant__id__in=accountant_ids_list)
            )
        else:
            accountant_ids_list = [int(aid) for aid in accountant]
            vat_clients = vat_clients.filter(
                client__accountant__id__in=accountant_ids_list)

        metrics = {}
        metrics["submitted"] = len(vat_clients.filter(submitted=True))
        metrics["client_notified"] = len(
            vat_clients.filter(client_notified=True))
        metrics["paid"] = len(vat_clients.filter(paid=True))

        headers = ["Mark Complete", "Name", "Period", "Submitted",
                   "Client Notified", "Paid", "Comment", "Update Comment"]
        search_query = request.GET.get("search")
        if search_query:
            vat_clients = vat_clients.filter(
                client__name__icontains=search_query)
        if request.GET.get("export") == "csv":
            headers_export = ["Name", "Registration Number", "Internal ID",
                              "Year", "Month", "Submitted", "Client Notified", "Client Paid", "Comment", "Marked Notified by", "Marked Submitted By", "Marked Paid By", "Date Submitted"]
            rows = [
                [c.client.get_client_full_name(), c.client.vat_reg_number,
                 c.client.internal_id_number, c.year.the_year, c.month.name, c.submitted, c.client_notified, c.paid, c.comment, c.marked_notified_by, c.marked_submitted_by, c.marked_paid_by, c.date_marked_submitted]
                for c in vat_clients
            ]
            return export_to_csv(f"vat_submission_{year}0{month}.csv", headers_export, rows)

        count = len(vat_clients)
        return render(request, "client/vat_clients_list.html", {
            "clients": vat_clients,
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

        if "field" in request.POST and "value" in request.POST:
            field_name = request.POST.get("field")
            value = request.POST.get("value") == 'true'
            if field_name in ['submitted', 'client_notified', 'paid']:
                setattr(client, field_name, value)
                if field_name == 'submitted':
                    client.marked_submitted_by = request.user
                    client.date_marked_submitted = timezone.now().date()
                elif field_name == 'client_notified':
                    client.marked_notified_by = request.user
                elif field_name == 'paid':
                    client.marked_paid_by = request.user

                client.save()
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "Invalid field name"})

        updated_any_field_in_bulk = False
        for field in ['submitted', 'client_notified', 'paid']:
            if field in request.POST:
                value = request.POST.get(field) == 'true'
                setattr(client, field, value)
                updated_any_field_in_bulk = True
                if field == "submitted":
                    client.marked_submitted_by = request.user
                    client.date_marked_submitted = timezone.now().date()
                elif field == 'client_notified':
                    client.marked_notified_by = request.user
                elif field == 'paid':
                    client.marked_paid_by = request.user
        if updated_any_field_in_bulk:
            client.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": "No valid fields to update specified"})

    except VatSubmissionHistory.DoesNotExist:
        return JsonResponse({"success": False, "error": "Client not found"})
    except Exception as e:
        return JsonResponse({"success": False, "error": f"An error occurred: {str(e)}"})


@login_required
@require_POST
def update_client_financial(request, financial_year_id):
    try:
        financial_year = ClientFinancialYear.objects.get(id=financial_year_id)

        # Update fields if they exist in POST data
        if 'finish_date' in request.POST:
            finish_date = request.POST['finish_date']
            financial_year.finish_date = finish_date if finish_date else None

        if 'itr14_date' in request.POST:
            itr14_date = request.POST['itr14_date']
            financial_year.itr14_date = itr14_date if itr14_date else None

        if 'invoice_date' in request.POST:
            invoice_date = request.POST['invoice_date']
            financial_year.invoice_date = invoice_date if invoice_date else None

        financial_year.save()

        return JsonResponse({'success': True})
    except ClientFinancialYear.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Record not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# deprecated
# @login_required
# @permission_required("client.change_clientfinancialyear", raise_exception=True)
# def create_clients_for_financial_year(request):
#     form = ClientFinancialYearProcessForm(request.POST or None)
#     if form.is_valid():
#         year = form.cleaned_data["financial_year"]
#         created_clients = ClientFinancialYear.setup_clients_afs_for_year(
#             year.the_year)
#         messages.success(
#             request, f"{len(created_clients)} created or returned")
#         return redirect(reverse("process"))
#     return render(request, "client/created_financial_years_form.html", {"form": form})


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = "client/client_detail.html"
    context_object_name = "client"

    def get_object(self):
        return get_object_or_404(Client, id=self.kwargs["id"])


@login_required
def book_service_dates(request):
    form = BookServiceForm(request.POST or None)
    data = []
    headers = ["Client Name", "Year"]
    unique_years = set()
    update_type = None
    is_valid = False
    if form.is_valid():
        selected_year_ids = form.cleaned_data.get("years", [])
        accountants = form.cleaned_data.get("accountant", [])
        month = form.cleaned_data.get("month", [])
        client_type = form.cleaned_data.get("client_type", [])
        service = form.cleaned_data.get("service", None)

        month = list(map(int, month))
        client_type = list(map(int, client_type))
        is_valid = True
        today = datetime.now().date()
        selected_year_ids = list(map(int, selected_year_ids))

        financial_years = FinancialYear.objects.filter(
            id__in=selected_year_ids)

        eligible_clients = Client.objects.filter(
            client_type__in=client_type, month_end__in=month)

        valid_clients = [
            c.id for c in eligible_clients if c.is_afs_client(today)]

        for year in financial_years:
            created_clients = ClientFinancialYear.setup_clients_afs_for_year(
                year.the_year)

        data = ClientFinancialYear.objects.filter(
            client_id__in=valid_clients, financial_year__in=financial_years, client__client_type__id__in=client_type)

        if "None" in accountants:
            accountant_ids_list = [int(aid)
                                   for aid in accountants if aid != 'None']
            data = data.filter(
                Q(client__accountant__isnull=True) | Q(
                    client__accountant__id__in=accountant_ids_list)
            )
        else:
            accountant_ids_list = [int(aid) for aid in accountants]
            data = data.filter(client__accountant__id__in=accountant_ids_list)

        unique_years = sorted(
            set(r.financial_year.the_year for r in data), reverse=True)
        update_type = service.title() if service else ""
        if service and service.title() == "Accounting":
            headers.extend(["Acc Schedule Date",
                           "Acc Finish Date", "Save"])
        elif service and service.title() == "Taxation":
            headers.extend(["Tax Schedule Date",
                           "Tax Finish Date", "Save"])
        else:
            headers.extend(["Secretarial Schedule Date",
                           "Secretarial Finish Date", "Save"])

    return render(request, "client/book_service.html", {
        "form": form,
        "data": data,
        "scheduled": data,
        "count": len(data),
        "headers": headers,
        "unique_years": unique_years,
        "is_valid": is_valid,
        "update_type": update_type
    })


@require_POST
@login_required
def progress_update_financials(request, client_id):
    try:
        department = request.POST.get("department")
        start_date = request.POST.get("start_date", None)
        end_date = request.POST.get("finish_date", None)

        if not start_date and not end_date:
            return JsonResponse({"success": False, "message": "Nothing to update here!, enter values"})
        client_financial_year = ClientFinancialYear.objects.get(id=client_id)

        start_date_as_date = None
        end_date_as_date = None
        if start_date:
            start_date_as_date = datetime.strptime(
                start_date, '%Y-%m-%d').date()
        if end_date:
            end_date_as_date = datetime.strptime(
                end_date, '%Y-%m-%d').date()
        if start_date and end_date and start_date_as_date > end_date_as_date:
            return JsonResponse({"success": False, "message": "Schedule date can not be greater than end date"})
        elif end_date and not start_date:
            return JsonResponse({"success": False, "message": "You can not have an end date before a start date"})
        if department == "accounting":
            client_financial_year.schedule_date = start_date if start_date else None
            client_financial_year.finish_date = end_date if end_date else None
        elif department == "taxation":
            client_financial_year.itr14_start_date = start_date if start_date else None
            client_financial_year.itr14_date = end_date if end_date else None
        elif department == "secretarial":
            client_financial_year.secretarial_start_date = start_date if start_date else None
            client_financial_year.secretarial_finish_date = end_date if end_date else None
        client_financial_year.save()
    except Exception as e:
        # exc_tp, exc_obj, exc_tb = sys.exc_info()
        # line_number = exc_tb.tb_lineno
        # print(line_number)
        return JsonResponse({"success": False, "message": "Could not update"})

    return JsonResponse({"success": True, "message": "Was updated successfully"})


@login_required
def financials_productivity_monitor(request):
    form = FinancialProductivityForm(request.GET or None)
    is_valid = False
    unique_years = set()
    unique_fin_days = set()
    unique_tax_days = set()
    unique_sec_days = set()
    unique_inv_days = set()

    returned_data = []
    headers = ["Client Name", "Year", "Fin Days",
               "AFSs Completed", "Sec Days", "Sec Completed", "Tax Days", "Tax Completed", "Invoicing Days", "Invoicing Completed"]
    count = 0

    max_dict = {}
    if form.is_valid():
        selected_year_ids = form.cleaned_data.get("years", [])
        accountants = form.cleaned_data.get("accountant", [])
        searchterm = form.cleaned_data.get("searchterm", "")
        month = form.cleaned_data.get("month", [])
        client_type = form.cleaned_data.get("client_type", [])

        month = list(map(int, month))

        client_type = list(map(int, client_type))
        is_valid = True
        today = datetime.now().date()

        selected_year_ids = list(map(int, selected_year_ids))
        financial_years = FinancialYear.objects.filter(
            id__in=selected_year_ids)

        for year in selected_year_ids:
            created_clients = ClientFinancialYear.setup_clients_afs_for_year(
                year, today)

        valid_clients = [c for c in Client.objects.all() if
                         c.is_afs_client(today) and c.month_end in month]

        data = ClientFinancialYear.objects.filter(
            client__in=valid_clients, financial_year__in=financial_years, client__client_type__id__in=client_type).order_by("financial_year", "client__name")
        if "None" in accountants:
            accountant_ids_list = [int(aid)
                                   for aid in accountants if aid != 'None']
            data = data.filter(
                Q(client__accountant__isnull=True) | Q(
                    client__accountant__id__in=accountant_ids_list)
            )
        else:
            accountant_ids_list = [int(aid) for aid in accountants]
            data = data.filter(client__accountant__id__in=accountant_ids_list)
        if searchterm:
            data = data.filter(
                client__name__icontains=searchterm)
        unique_years = sorted(
            set(r.financial_year.the_year for r in data), reverse=True)
        returned_data = {}
        for client_fy in data:
            returned_data = construct_client_dict(returned_data, client_fy)
        count = len(returned_data)
        unique_fin_days = calculate_unique_days_from_dict(
            "fin_days", returned_data)
        unique_sec_days = calculate_unique_days_from_dict(
            "sec_days", returned_data)
        unique_tax_days = calculate_unique_days_from_dict(
            "tax_days", returned_data)
        unique_inv_days = calculate_unique_days_from_dict(
            "invoicing_days", returned_data)
        max_dict = calculate_max_days_from_dict(returned_data)
        if request.GET.get("export") == "csv":
            headers = ["Name", "Registration Number", "Internal ID",
                       "Year", "Schedule Date", "AFSs Finish Date", "Sec Start Date", "Sec Finish Date", "ITR14 Start Date", "ITR14 Finish Date", "Invoice Date"]
            rows = [
                [c.client.get_client_full_name(), c.client.entity_reg_number,
                 c.client.internal_id_number, c.financial_year.the_year, c.schedule_date, c.finish_date, c.secretarial_start_date, c.secretarial_finish_date, c.itr14_start_date, c.itr14_date, c.invoice_date]
                for c in data
            ]
            return export_to_csv("financial_prog_monitor_export.csv", headers, rows)
    context = {
        "form": form,
        "is_valid": is_valid,
        "unique_years": unique_years,
        "data": returned_data,
        "headers": headers,
        "unique_fin_days": unique_fin_days,
        "unique_sec_days": unique_sec_days,
        "unique_tax_days": unique_tax_days,
        "unique_inv_days": unique_inv_days,
        "count": count,
        "max_dict": max_dict
    }
    return render(request, "client/financials_accountability.html", context)


class ClientUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Client
    template_name = "client/edit_client.html"
    context_object_name = "client"
    fields = get_client_model_fields()
    permission_required = "client.change_client"
    pk_url_kwarg = "id"

    def get_success_url(self):
        return reverse_lazy('client-detail', kwargs={'id': self.object.pk})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        optional_fields = []
        boolean_fields = ['is_active', 'is_sa_resident']
        date_fields = ['birthday_of_entity']

        for field_name, field in form.fields.items():

            if field_name not in optional_fields:
                field.required = False

            if field_name in boolean_fields:
                field.widget.attrs.update({
                    'class': 'form-check-input',
                })

            elif field_name in date_fields:

                form.fields[field_name].widget = forms.DateInput(
                    attrs={
                        "class": "form-control",
                        "type": "date"
                    },
                    format="%Y-%m-%d"
                )

                if self.object and getattr(self.object, field_name):
                    form.fields[field_name].initial = getattr(
                        self.object, field_name).strftime('%Y-%m-%d'
                                                          )

            else:
                field.widget.attrs.update({
                    'class': 'form-control',
                })

            if not field.widget.attrs.get('placeholder'):
                field.widget.attrs['placeholder'] = field.label

        return form


@login_required
def update_prov_cipc_return(request):
    form = CreateUpdateProvCipcForm(request.GET or None)
    return_caption = "Select the return type"
    if form.is_valid():
        return_type = form.cleaned_data.get("return_type", None)
        selected_year_ids = form.cleaned_data.get("years", None)
        accountants = form.cleaned_data.get("accountant", [])
        searchterm = form.cleaned_data.get("searchterm", "")
        month = form.cleaned_data.get("month", None)
        client_type = form.cleaned_data.get("client_type", [])

        month = int(month)
        client_type = list(map(int, client_type))

        selected_year_ids = int(selected_year_ids)

        client_list = []
        today = timezone.now().date()
        data = []
        selected_year = FinancialYear.objects.get(
            id=selected_year_ids)
        client_obj = Client.objects.filter(
            client_type__id__in=client_type)
        if "None" in accountants:
            accountant_ids_list = [int(aid)
                                   for aid in accountants if aid != 'None']
            client_obj = client_obj.filter(
                Q(accountant__isnull=True) | Q(
                    accountant__id__in=accountant_ids_list)
            )
        else:
            accountant_ids_list = [int(aid) for aid in accountants]
            client_obj = client_obj.filter(
                accountant__id__in=accountant_ids_list)
        if searchterm:
            client_obj = client_obj.filter(
                name__icontains=searchterm)
        if return_type == "cipc":
            return_caption = "CIPC Annual return Submission"
            client_list = [
                c.id for c in client_obj if c.is_client_cipc_reg_eligible()]
            for client_id in client_list:
                cipc_return, created = ClientCipcReturnHistory.objects.get_or_create(
                    client_id=client_id, financial_year_id=selected_year_ids)
            data = ClientCipcReturnHistory.objects.filter(
                client_id__in=client_list, financial_year_id=selected_year_ids, client__birthday_of_entity__month=month)
        elif return_type == "first" or return_type == "second":
            return_caption = return_type.capitalize() + " Provisional Tax Submission"

            month_end_of_prov = datetime(
                selected_year.the_year, month, 28).date()
            prov_numb = 1
            if return_type == "first":
                client_list = [
                    c.id for c in client_obj if c.is_first_prov_tax_month(month_end_of_prov)]
            elif return_type == "second":
                prov_numb = 2
                client_list = [
                    c.id for c in client_obj if c.is_second_prov_tax_month(month_end_of_prov)]

            for client_id in client_list:
                prov_return, created = ClientProvisionalTax.objects.get_or_create(
                    client_id=client_id, financial_year_id=selected_year_ids, prov_tax_numb=prov_numb
                )
            data = ClientProvisionalTax.objects.filter(
                client_id__in=client_list, financial_year_id=selected_year_ids, prov_tax_numb=prov_numb
            ).order_by("client__name")
        headers = ["Client Name", "Year", "Month", "Finished",
                   "Finish Date", "Invoiced", "Invoice Date", "Comment", "Actions"]
        month_str = settings.MONTHS_LIST[month - 1].title()
        if request.GET.get("export") == "csv":
            print_headers = ["Client No", "Client Name", "Year", "Month",
                             "Finish Date", "Invoice Date", "Comment"]
            rows = [
                [c.client.internal_id_number, c.client.get_client_full_name(), selected_year.the_year,
                 month_str, c.finish_date, c.invoice_date, c.comment]
                for c in data
            ]
            return export_to_csv(f"{return_type}_return_export_{month_str}.csv", print_headers, rows)
        data_context = {
            "clients": data,
            "form": form,
            "count": len(data),
            "return_caption": return_caption,
            "headers": headers,
            "month": month_str,
            "return_type": return_type
        }
        return render(request, "client/prov_cipc_sub.html", data_context)
    return render(request, "client/prov_cipc_sub.html", {"form": form, "return_type": return_caption})


@require_POST
@login_required
def clear_save_cipc_prov(request):
    trans_id = request.POST.get("transId")
    return_type = request.POST.get("returnType")
    button_clicked = request.POST.get("buttonClicked")
    try:
        if return_type == "cipc":
            trans_id = int(trans_id)
            cipc_trans = ClientCipcReturnHistory.objects.get(id=trans_id)
            if button_clicked == "cancel":
                cipc_trans.finish_date = None
                cipc_trans.invoice_date = None
                cipc_trans.comment = ""
                cipc_trans.save()
            else:
                finish_date = request.POST.get("finishDate", None)
                invoice_date = request.POST.get("invoiceDate", None)
                comment = request.POST.get("comment", "")
                cipc_trans = ClientCipcReturnHistory.objects.get(id=trans_id)
                if comment:
                    cipc_trans.comment = comment
                if finish_date:
                    finish_date_dt = datetime.strptime(finish_date, "%Y-%m-%d")
                    cipc_trans.finish_date = finish_date_dt
                    cipc_trans.marked_finished_by = request.user
                if invoice_date:
                    invoice_date_dt = datetime.strptime(
                        invoice_date, "%Y-%m-%d")
                    cipc_trans.invoice_date = invoice_date_dt
                    cipc_trans.invoiced_by = request.user
                cipc_trans.save()
        elif return_type == "first" or return_type == "second":
            trans_id = int(trans_id)
            prov_trans = ClientProvisionalTax.objects.get(id=trans_id)
            if button_clicked == "cancel":
                prov_trans.finish_date = None
                prov_trans.invoice_date = None
                prov_trans.comment = ""
                prov_trans.save()
            else:
                finish_date = request.POST.get("finishDate", None)
                invoice_date = request.POST.get("invoiceDate", None)
                comment = request.POST.get("comment", "")
                prov_trans = ClientProvisionalTax.objects.get(id=trans_id)
                if comment:
                    prov_trans.comment = comment
                if finish_date:
                    finish_date_dt = datetime.strptime(finish_date, "%Y-%m-%d")
                    prov_trans.finish_date = finish_date_dt
                    prov_trans.marked_finished_by = request.user
                if invoice_date:
                    invoice_date_dt = datetime.strptime(
                        invoice_date, "%Y-%m-%d")
                    prov_trans.invoice_date = invoice_date_dt
                    prov_trans.invoiced_by = request.user
                prov_trans.save()
        return JsonResponse({"success": True, "message": "Updated successfully"})
    except Exception as e:
        return JsonResponse({"success": False, "message": "Error occured"})


class ClientCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Client
    template_name = "client/edit_client.html"
    context_object_name = "client"
    fields = get_client_model_fields()
    permission_required = "client.add_client"

    def get_success_url(self):
        return reverse_lazy("client-detail", kwargs={"id": self.object.pk})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        optional_fields = get_optional_fields_for_client()
        boolean_fields = ["is_active", "is_sa_resident"]
        date_fields = ["birthday_of_entity"]

        for field_name, field in form.fields.items():
            if field_name in optional_fields:
                field.required = False

            if field_name in boolean_fields:
                field.widget.attrs.update({
                    "class": "form-check-input",
                })

            elif field_name in date_fields:
                form.fields[field_name].widget = forms.DateInput(
                    attrs={
                        "class": "form-control",
                        "type": "date",
                    },
                    format="%Y-%m-%d",
                )
            else:
                field.widget.attrs.update({
                    "class": "form-control",
                })

            if not field.widget.attrs.get("placeholder"):
                field.widget.attrs["placeholder"] = field.label

        return form


@login_required
def update_client_service(request):
    form = ClientServiceForm(request.GET or None)
    if form.is_valid():
        service = form.cleaned_data["service"]
        search_q = form.cleaned_data.get("searchterm", "")

        clients = ClientService.objects.filter(service=service)
        if search_q:
            clients = clients.filter(client__name__icontains=search_q)
        count = len(clients)
        headers = ["Client Name", "Status",
                   "Start Date", "End Date", "Comment", "Actions"]
        context = {"clients": clients, "count": count,
                   "form": form, "headers": headers}
        if request.GET.get("export") == "csv":
            csvheaders = ["Name", "Registration Number", "Internal ID",
                          "Service Start", "Service End", "Comment"]
            rows = [
                [c.client.get_client_full_name(), c.client.entity_reg_number, c.client.internal_id_number,
                 c.start_date, c.end_date, c.comment]
                for c in clients
            ]
            service = Service.objects.get(id=service)
            return export_to_csv(f"{service.name}_client_service_export.csv", csvheaders, rows)
        return render(request, "client/client_service.html", context)
    return render(request, "client/client_service.html", {"form": form})


@login_required
@require_POST
def update_client_service_ajax(request):
    trans_id = request.POST.get("transId", None)
    if not trans_id:
        return JsonResponse({"success": False, "message": "No transaction found"})
    comment = request.POST.get("comment", None)
    start_date = request.POST.get("startDate", None)
    end_date = request.POST.get("finishDate", None)

    try:
        trans_id = int(trans_id)
        client_service = ClientService.objects.get(id=trans_id)
        if comment:
            client_service.comment = comment
        if start_date and end_date:
            start_date_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            if start_date_date > end_date_date:
                return JsonResponse({"success": False, "message": "Start date can not be after end date"})
            client_service.start_date = start_date_date
            client_service.end_date = end_date_date
        if start_date:
            start_date_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            client_service.start_date = start_date_date
        if end_date:
            end_date_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            client_service.end_date = end_date_date
        client_service.save()
        return JsonResponse({"success": True, "message": "Updated successfully"})
    except Exception as e:
        return JsonResponse({"success": False, "message": "An Error occured"})


class ClientServiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ClientService
    fields = ["client", "service", "start_date", "end_date", "comment"]
    template_name = "client/client_service_form.html"
    success_url = reverse_lazy("process")
    permission_required = "client.change_client_service"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        for field_name, field in form.fields.items():
            field.widget.attrs.update({"class": "form-control"})

        form.fields["client"].queryset = Client.objects.all().order_by("name")

        form.fields["service"].queryset = form.fields["service"].queryset.order_by(
            "name")

        form.fields["start_date"].widget.input_type = "date"
        form.fields["end_date"].widget.input_type = "date"

        form.fields["start_date"].required = False
        form.fields["end_date"].required = False
        form.fields["comment"].required = False

        return form

    def form_valid(self, form):
        return super().form_valid(form)


class ClientServiceListView(LoginRequiredMixin, ListView):
    model = ClientService
    template_name = "client/client_service_list.html"
    context_object_name = "client_services"
    ordering = ["client__name"]


@login_required
def adjust_individual(request):
    client_id = request
    all_individuals = Client.objects.filter(client_type__name="Individual")
    today = datetime.now().date()
    # all_individuals = [
    #     c for c in all_individuals if c.is_afs_client(today)]
    context = {"clients": all_individuals, "count": len(all_individuals)}
    return render(request, "client/temp.html", context)


@login_required
@require_POST
def ajax_update_individual_fin_start_year(request):
    trans_id = request.POST.get("transId")
    financial_year = request.POST.get("financialYear")
    if not trans_id and not financial_year:
        return JsonResponse({"success": False, "message": "Transaction Id or financial year can not be empty"})
    try:
        trans_id = int(trans_id)
        financial_year = int(financial_year)
        client = Client.objects.filter(id=trans_id).first()
        fin_year_inst = FinancialYear.objects.get(the_year=financial_year)
        client.first_financial_year = fin_year_inst
        client.save()
    except Exception as e:
        # print(e)
        return JsonResponse({"success": False, "message": "There was an error"})
    return JsonResponse({"success": True, "message": "Updated successfully"})
