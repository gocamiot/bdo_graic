from django.urls import path

from apps.tables.hr_user_list import hr_user_list_views as views

urlpatterns = [
    path('hr_user_list/', views.hr_user_list, name="hr_user_list"),
    path('create_hr_user_list/', views.create_hr_user_list, name="create_hr_user_list"),
    path('create-hr-user-list-filter/', views.create_hr_user_list_filter, name="create_hr_user_list_filter"),
    path('create-hr-user-list-page-items/', views.create_hr_user_list_page_items, name="create_hr_user_list_page_items"),
    path('create-hr-user-list-hide-show-items/', views.create_hr_user_list_hide_show_filter, name="create_hr_user_list_hide_show_filter"),
    path('delete-hr-user-list-filter/<int:id>/', views.delete_hr_user_list_filter, name="delete_hr_user_list_filter"),
    path('delete-hr-user-list-daterange-filter/<int:id>/', views.delete_hr_user_list_daterange_filter, name="delete_hr_user_list_daterange_filter"),
    path('delete-hr-user-list-intrange-filter/<int:id>/', views.delete_hr_user_list_intrange_filter, name="delete_hr_user_list_intrange_filter"),
    path('delete-hr-user-list-floatrange-filter/<int:id>/', views.delete_hr_user_list_floatrange_filter, name="delete_hr_user_list_floatrange_filter"),
    path('delete-hr-user-list/<int:id>/', views.delete_hr_user_list, name="delete_hr_user_list"),
    path('update-hr-user-list/<int:id>/', views.update_hr_user_list, name="update_hr_user_list"),

    path('export-hr-user-list-csv/', views.ExportCSVView.as_view(), name='export_hr_user_list_csv'),
    path('export-hr-user-list-excel/', views.ExportExcelView.as_view(), name='export_hr_user_list_excel'),
    path('export-hr-user-list-pdf/', views.ExportPDFView.as_view(), name='export_hr_user_list_pdf'),
]