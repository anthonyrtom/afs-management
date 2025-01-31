from django.contrib import admin
from .models import VatCategories, Client, FinancialYear, ClientType
from . forms import ClientAddForm


class VatCategoryAdmin(admin.ModelAdmin):
    model = VatCategories
    list_display = ["vat_category", "category_descr"]


class ClientAdmin(admin.ModelAdmin):
    model = Client
    form = ClientAddForm
    list_display = ["name", "month_end", "last_day", "cipc_reg_number"]
    search_fields = ('name', 'surname')


admin.site.register(VatCategories, VatCategoryAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(FinancialYear)
admin.site.register(ClientType)
