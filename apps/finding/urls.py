from django.urls import path
from apps.finding import views


urlpatterns = [
    path('add-to-finding/<str:model_name>/<str:model_choice>/', views.add_to_finding, name="add_to_finding"),
    path('add-finding-from-finding/<str:finding_id>/', views.add_finding_from_finding, name="add_finding_from_finding"),

    path('finding/<str:id>/', views.finding_details, name="finding_details"),
    path('remove-finding/<str:id>/', views.remove_finding, name="remove_finding"),
    path('create-finding-filter/<str:finding_id>/', views.create_finding_filter, name="create_finding_filter"),
    path('remove-finding-filter/', views.delete_finding_filter, name="delete_finding_filter"),
    path('remove-finding-date-range-filter/<int:id>/', views.delete_finding_date_range_filter, name="delete_finding_date_range_filter"),
    path('remove-finding-int-range-filter/<int:id>/', views.delete_finding_int_range_filter, name="delete_finding_int_range_filter"),
    path('remove-finding-float-range-filter/<int:id>/', views.delete_finding_float_range_filter, name="delete_finding_float_range_filter"),

    path('create-finding-page-items/<str:finding_id>/', views.create_finding_page_items, name="create_finding_page_items"),
    path('create-finding-hide-show-items/<str:finding_id>/', views.create_finding_hide_show_filter, name="create_finding_hide_show_filter"),

    path('add-finding-description/<str:finding_id>/', views.add_finding_description, name="add_finding_description"),
    path('export-finding-csv/<str:id>/', views.export_finding_csv_view, name='export_finding_csv_view'),
    path('export-finding-excel/<str:id>/', views.ExportFindingExcelView.as_view(), name='export_finding_excel_view'),
]
