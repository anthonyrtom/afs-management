from django.contrib import admin
from django.db.models import Q
from .models import VatCategories, Client, FinancialYear, ClientType, ClientFinancialYear, Months, VatSubmissionHistory
from . forms import ClientAddForm, ClientFinancialYearForm, VatSubmissionHistoryForm


class VatCategoryAdmin(admin.ModelAdmin):
    model = VatCategories
    list_display = ["vat_category", "category_descr"]


class ClientFinancialYearAdmin(admin.ModelAdmin):
    model = ClientFinancialYear
    form = ClientFinancialYearForm
    list_display = ["client__name", "financial_year",
                    "schedule_date", "finish_date"]


class ClientAdmin(admin.ModelAdmin):
    model = Client
    form = ClientAddForm
    list_display = ["name", "month_end", "last_day", "cipc_reg_number"]
    search_fields = ('name', 'surname')


class VatSubmissionHistoryAdmin(admin.ModelAdmin):
    model = VatSubmissionHistory
    list_display = ["client", "year", "month",
                    "submitted", "paid", "client_notified"]
    form = VatSubmissionHistoryForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "client":
            kwargs["queryset"] = Client.objects.filter(
                Q(vat_category__isnull=False) & Q(
                    first_month_for_vat_sub__isnull=False)
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(VatCategories, VatCategoryAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(ClientFinancialYear, ClientFinancialYearAdmin)
admin.site.register(VatSubmissionHistory, VatSubmissionHistoryAdmin)
admin.site.register(FinancialYear)
admin.site.register(ClientType)
admin.site.register(Months)
