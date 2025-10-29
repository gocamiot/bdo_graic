from django.urls import path

from apps.tables.control_ad_user import control_ad_user_views as views

urlpatterns = [
    path('control_ad_user/', views.control_ad_user, name="control_ad_user"),
    path('create_control_ad_user/', views.create_control_ad_user, name="create_control_ad_user"),
    path('create-control-ad-user-filter/', views.create_control_ad_user_filter, name="create_control_ad_user_filter"),
    path('create-control-ad-user-page-items/', views.create_control_ad_user_page_items, name="create_control_ad_user_page_items"),
    path('create-control-ad-user-hide-show-items/', views.create_control_ad_user_hide_show_filter, name="create_control_ad_user_hide_show_filter"),
    path('delete-control-ad-user-filter/<int:id>/', views.delete_control_ad_user_filter, name="delete_control_ad_user_filter"),
    path('delete-control-ad-user-daterange-filter/<int:id>/', views.delete_control_ad_user_daterange_filter, name="delete_control_ad_user_daterange_filter"),
    path('delete-control-ad-user-intrange-filter/<int:id>/', views.delete_control_ad_user_intrange_filter, name="delete_control_ad_user_intrange_filter"),
    path('delete-control-ad-user-floatrange-filter/<int:id>/', views.delete_control_ad_user_floatrange_filter, name="delete_control_ad_user_floatrange_filter"),
    path('delete-control-ad-user/<int:id>/', views.delete_control_ad_user, name="delete_control_ad_user"),
    path('update-control-ad-user/<int:id>/', views.update_control_ad_user, name="update_control_ad_user"),

    path('export-control-ad-user-csv/', views.ExportCSVView.as_view(), name='export_control_ad_user_csv'),
    path('export-control-ad-user-excel/', views.ExportExcelView.as_view(), name='export_control_ad_user_excel'),
    path('export-control-ad-user-pdf/', views.ExportPDFView.as_view(), name='export_control_ad_user_pdf'),
]