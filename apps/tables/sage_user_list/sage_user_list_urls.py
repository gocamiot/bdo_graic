from django.urls import path

from apps.tables.sage_user_list import sage_user_list_views as views

urlpatterns = [
    path('sage_user_list/', views.sage_user_list, name="sage_user_list"),
    path('create_sage_user_list/', views.create_sage_user_list, name="create_sage_user_list"),
    path('create-sage-user-list-filter/', views.create_sage_user_list_filter, name="create_sage_user_list_filter"),
    path('create-sage-user-list-page-items/', views.create_sage_user_list_page_items, name="create_sage_user_list_page_items"),
    path('create-sage-user-list-hide-show-items/', views.create_sage_user_list_hide_show_filter, name="create_sage_user_list_hide_show_filter"),
    path('delete-sage-user-list-filter/<int:id>/', views.delete_sage_user_list_filter, name="delete_sage_user_list_filter"),
    path('delete-sage-user-list-daterange-filter/<int:id>/', views.delete_sage_user_list_daterange_filter, name="delete_sage_user_list_daterange_filter"),
    path('delete-sage-user-list-intrange-filter/<int:id>/', views.delete_sage_user_list_intrange_filter, name="delete_sage_user_list_intrange_filter"),
    path('delete-sage-user-list-floatrange-filter/<int:id>/', views.delete_sage_user_list_floatrange_filter, name="delete_sage_user_list_floatrange_filter"),
    path('delete-sage-user-list/<int:id>/', views.delete_sage_user_list, name="delete_sage_user_list"),
    path('update-sage-user-list/<int:id>/', views.update_sage_user_list, name="update_sage_user_list"),

    path('export-sage-user-list-csv/', views.ExportCSVView.as_view(), name='export_sage_user_list_csv'),
    path('export-sage-user-list-excel/', views.ExportExcelView.as_view(), name='export_sage_user_list_excel'),
    path('export-sage-user-list-pdf/', views.ExportPDFView.as_view(), name='export_sage_user_list_pdf'),
]