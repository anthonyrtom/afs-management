from django.db.models import Q
from .models import ClientFinancialYear
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
from utilities.helpers import construct_client_dict, calculate_unique_days_from_dict, calculate_max_days_from_dict
from users.models import CustomUser
from . forms import ClientFinancialYear, UserSearchForm, VatClientSearchForm,  VatClientsPeriodProcess, ClientFinancialYearProcessForm, CreateandViewVATForm,  FilterByServiceForm, ClientFilter, FilterFinancialClient, FilterAllFinancialClient, BookServiceForm, FinancialProductivityForm


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
            today, month=today.month, client_type=client_type)

    elif filter_type == "cipc_clients":
        clients = Client.get_clients_of_type(
            "Cipc Returns", today)
        # service = ClientService.objects.filter()
        clients = [
            client for client in clients if client.client_type and client.client_type.name == client_type and ClientService.is_service_offered(client.id, cipc_service.id, today) and client.is_client_cipc_reg_eligible()]

    elif filter_type == "current_cipc_clients":
        clients = Client.get_clients_of_type(
            "Cipc Returns", today)
        clients = [client for client in clients if ClientService.is_service_offered(client.id, cipc_service.id, today) and client.get_birthday_in_year(
            today.year) and client.get_birthday_in_year(today.year).month == today.month and client.client_type and client.client_type.name == client_type]

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

        headers = ["Name", "Fin Year", "Schedule Date",
                   "Financials Status", "ITR14 Status", "Invoicing Status"]
        return render(request, "client/scheduled_financials.html", {"scheduled": scheduled, "count": count, "afs_complete": afs_complete, "headers": headers, "data": data, "itr14_complete": itr14_complete, "invoiced": invoiced, "form": form, "unique_years": unique_years, })

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

    return render(request, "client/financials_progress.html", {
        "form": form,
        "data": data,
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
    return render(request, "client/created_financial_years_form.html", {"form": form})


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
