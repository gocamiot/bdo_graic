from django.urls import path

from apps.tables.change_requests import change_requests_views as views

urlpatterns = [
    path('change_requests/', views.change_requests, name="change_requests"),
    path('create_change_requests/', views.create_change_requests, name="create_change_requests"),
    path('create-change-requests-filter/', views.create_change_requests_filter, name="create_change_requests_filter"),
    path('create-change-requests-page-items/', views.create_change_requests_page_items, name="create_change_requests_page_items"),
    path('create-change-requests-hide-show-items/', views.create_change_requests_hide_show_filter, name="create_change_requests_hide_show_filter"),
    path('delete-change-requests-filter/<int:id>/', views.delete_change_requests_filter, name="delete_change_requests_filter"),
    path('delete-change-requests-daterange-filter/<int:id>/', views.delete_change_requests_daterange_filter, name="delete_change_requests_daterange_filter"),
    path('delete-change-requests-intrange-filter/<int:id>/', views.delete_change_requests_intrange_filter, name="delete_change_requests_intrange_filter"),
    path('delete-change-requests-floatrange-filter/<int:id>/', views.delete_change_requests_floatrange_filter, name="delete_change_requests_floatrange_filter"),
    path('delete-change-requests/<int:id>/', views.delete_change_requests, name="delete_change_requests"),
    path('update-change-requests/<int:id>/', views.update_change_requests, name="update_change_requests"),

    path('export-change-requests-csv/', views.ExportCSVView.as_view(), name='export_change_requests_csv'),
    path('export-change-requests-excel/', views.ExportExcelView.as_view(), name='export_change_requests_excel'),
    path('export-change-requests-pdf/', views.ExportPDFView.as_view(), name='export_change_requests_pdf'),
]