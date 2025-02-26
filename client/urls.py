from django.urls import path
from . views import dashboard, reports, view_all_clients, client_filter_view, filter_clients_by_accountant, scheduled_financials, completed_financials, completed_financials_month, get_unfinished_financials, search_clients, get_all_accountants, search_users, get_clients_for_category, get_clients_for_month

urlpatterns = [
    path('dashboard/', dashboard, name="dashboard"),
    path('reports/', reports, name="reports"),
    path('all-clients/', view_all_clients, name="all-clients"),
    path('statutory-clients/', client_filter_view, name="statutory-clients"),
    path('get-accountant-clients/', filter_clients_by_accountant,
         name="get_accountant_clients"),
    path('view-scheduled/', scheduled_financials,
         name="view-scheduled"),
    path('completed-financials/', completed_financials,
         name="completed-financials"),
    path('completed-financials-month/', completed_financials_month,
         name="completed-financials-month"),
    path('unfinished-financials/', get_unfinished_financials,
         name="unfinished-financials"),
    path('search-client/', search_clients,
         name="search-client"),
    path('get-accountants/', get_all_accountants,
         name="get-accountants"),
    path('search-users/', search_users,
         name="search-users"),
    path('get-clients-for-category/', get_clients_for_category,
         name="get-clients-for-category"),
    path('get-clients-for-month/', get_clients_for_month,
         name="get-clients-for-month"),
]
