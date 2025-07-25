from django.urls import path
from . import views

urlpatterns = [
    path('process/', views.process_dashboard, name="process"),
    path('dashboard/list/<str:filter_type>/<str:client_type>/',
         views.dashboard_list, name='dashboard_list'),
    path('reports/', views.reports, name="reports"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('all-clients/', views.view_all_clients, name="all-clients"),
    path('view-scheduled/', views.scheduled_financials,
         name="view-scheduled"),
    path('filter-financials/', views.get_finished_or_scheduled_afs,
         name="filter-financials"),
    path('completed-financials-month/', views.completed_financials_month,
         name="completed-financials-month"),
    path('unfinished-financials/', views.get_unfinished_financials,
         name="unfinished-financials"),
    path('get-accountants/', views.get_all_accountants,
         name="get-accountants"),
    path('search-users/', views.search_users,
         name="search-users"),
    path('search-vat-clients/', views.search_vat_clients,
         name="search-vat-clients"),
    path('get-clients-for-month-or-accountant/', views.process_vat_clients_for_period,
         name="process_vat_clients_for_period"),
    path('vat-clients/update/', views.update_vat_client_status,
         name='update_vat_client_status'),
    path('process-clients-for-financial-years/', views.process_client_financial_years,
         name="process_client_financial_years"),
    path('create-or-update-vat/', views.create_or_update_vat,
         name="create-or-update-vat"),
    path('client-financial-years/update/', views.update_client_financial_year,
         name='update_client_financial_year'),
    path('client-financial-years/create/', views.create_clients_for_financial_year,
         name='create_client_financial_year'),
    path("client/<int:id>/", views.ClientDetailView.as_view(), name="client-detail"),
    path("ajax/update-vat-status/", views.ajax_update_vat_status,
         name="ajax_update_vat_status"),
    path("ajax/update-afs-status/", views.ajax_update_afs_status,
         name="ajax_update_afs_status"),
    path("ajax/update-comment/", views.ajax_update_comment,
         name="ajax_update_comment"),
    path("ajax/update-comment-afs/", views.ajax_update_afs_comment,
         name="ajax_update_afs_comment"),
    path("overview/",
         views.view_service_overview, name="view-service-overview"),
]
