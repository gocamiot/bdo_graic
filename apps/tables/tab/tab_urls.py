from django.urls import path

from apps.tables.tab import tab_view as views

urlpatterns = [
    path('add-to-tab/<str:model_name>/<str:model_choice>/', views.add_to_tab, name="add_to_tab"),
    path('add-tab-from-tab/<str:tab_id>/', views.add_tab_from_tab, name="add_tab_from_tab"),
    path('tab/<str:id>/', views.tab_details, name="tab_details"),
    path('remove-tab/<str:id>/', views.remove_tab, name="remove_tab"),
    path("get-axis-fields/<str:tab_id>", views.get_axis_fields, name="get_axis_fields"),
    path('create-tab-filter/<str:tab_id>/', views.create_tab_filter, name="create_tab_filter"),
    path('remove-tab-filter/', views.delete_tab_filter, name="delete_tab_filter"),

    path('create-tab-page-items/<str:tab_id>/', views.create_tab_page_items, name="create_tab_page_items"),
    path('create-tab-hide-show-items/<str:tab_id>/', views.create_tab_hide_show_filter, name="create_tab_hide_show_filter"),
    path('add-tab-notes/<str:tab_id>/', views.add_tab_notes, name="add_tab_notes"),
    path('rename-tab/<str:tab_id>/', views.rename_tab, name="rename_tab"),

    path('add-tab-description/<str:tab_id>/', views.add_tab_description, name="add_tab_description"),
    path('export-tab-csv/<str:id>/', views.export_tab_csv_view, name='export_tab_csv_view'),
    path('export-tab-excel/<str:id>/', views.ExportTabExcelView.as_view(), name='export_tab_excel_view'),
]