from django.urls import path

from apps.tables.ticket_logging import ticket_logging_views as views

urlpatterns = [
    path('ticket_logging/', views.ticket_logging, name="ticket_logging"),
    path('create_ticket_logging/', views.create_ticket_logging, name="create_ticket_logging"),
    path('create-ticket-logging-filter/', views.create_ticket_logging_filter, name="create_ticket_logging_filter"),
    path('create-ticket-logging-page-items/', views.create_ticket_logging_page_items, name="create_ticket_logging_page_items"),
    path('create-ticket-logging-hide-show-items/', views.create_ticket_logging_hide_show_filter, name="create_ticket_logging_hide_show_filter"),
    path('delete-ticket-logging-filter/<int:id>/', views.delete_ticket_logging_filter, name="delete_ticket_logging_filter"),
    path('delete-ticket-logging-daterange-filter/<int:id>/', views.delete_ticket_logging_daterange_filter, name="delete_ticket_logging_daterange_filter"),
    path('delete-ticket-logging-intrange-filter/<int:id>/', views.delete_ticket_logging_intrange_filter, name="delete_ticket_logging_intrange_filter"),
    path('delete-ticket-logging-floatrange-filter/<int:id>/', views.delete_ticket_logging_floatrange_filter, name="delete_ticket_logging_floatrange_filter"),
    path('delete-ticket-logging/<int:id>/', views.delete_ticket_logging, name="delete_ticket_logging"),
    path('update-ticket-logging/<int:id>/', views.update_ticket_logging, name="update_ticket_logging"),

    path('export-ticket-logging-csv/', views.ExportCSVView.as_view(), name='export_ticket_logging_csv'),
    path('export-ticket-logging-excel/', views.ExportExcelView.as_view(), name='export_ticket_logging_excel'),
    path('export-ticket-logging-pdf/', views.ExportPDFView.as_view(), name='export_ticket_logging_pdf'),
]