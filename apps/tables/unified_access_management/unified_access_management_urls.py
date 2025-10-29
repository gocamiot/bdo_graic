from django.urls import path

from apps.tables.unified_access_management import unified_access_management_views as views

urlpatterns = [
    path('unified_access_management/', views.unified_access_management, name="unified_access_management"),
    path('create_unified_access_management/', views.create_unified_access_management, name="create_unified_access_management"),
    path('create-unified-access-management-filter/', views.create_unified_access_management_filter, name="create_unified_access_management_filter"),
    path('create-unified-access-management-page-items/', views.create_unified_access_management_page_items, name="create_unified_access_management_page_items"),
    path('create-unified-access-management-hide-show-items/', views.create_unified_access_management_hide_show_filter, name="create_unified_access_management_hide_show_filter"),
    path('delete-unified-access-management-filter/<int:id>/', views.delete_unified_access_management_filter, name="delete_unified_access_management_filter"),
    path('delete-unified-access-management-daterange-filter/<int:id>/', views.delete_unified_access_management_daterange_filter, name="delete_unified_access_management_daterange_filter"),
    path('delete-unified-access-management-intrange-filter/<int:id>/', views.delete_unified_access_management_intrange_filter, name="delete_unified_access_management_intrange_filter"),
    path('delete-unified-access-management-floatrange-filter/<int:id>/', views.delete_unified_access_management_floatrange_filter, name="delete_unified_access_management_floatrange_filter"),
    path('delete-unified-access-management/<int:id>/', views.delete_unified_access_management, name="delete_unified_access_management"),
    path('update-unified-access-management/<int:id>/', views.update_unified_access_management, name="update_unified_access_management"),

    path('export-unified-access-management-csv/', views.ExportCSVView.as_view(), name='export_unified_access_management_csv'),
    path('export-unified-access-management-excel/', views.ExportExcelView.as_view(), name='export_unified_access_management_excel'),
    path('export-unified-access-management-pdf/', views.ExportPDFView.as_view(), name='export_unified_access_management_pdf'),
]