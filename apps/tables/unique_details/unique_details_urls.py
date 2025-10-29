from django.urls import path, re_path

from apps.tables.unique_details import unique_details_views as views

urlpatterns = [
    # re_path(r'^unique_details/(?P<unique_model_name>[^/]+)/(?P<unique_field_name>[^/]+)/(?P<unique_value>.*)/$', views.unique_details, name="unique_details"),
    # re_path(
    #     r'^unique_details/(?P<unique_model_name>[^/]+)/(?P<unique_field_name>[^/]+)(?:/(?P<unique_value>[^/]+))?(?:/(?P<finding_id>[0-9a-fA-F-]+))?/?$', 
    #     views.unique_details, 
    #     name="unique_details"
    # ),
    re_path(
        r'^unique_details/(?P<unique_model_name>[^/]+)/(?P<unique_field_name>[^/]+)'
        r'(?:/(?P<unique_value>[^/]*))?'
        r'(?:/(?P<finding_id>[0-9a-fA-F-]*))?'
        r'(?:/(?P<s_model_choice>[^/]*))?/?$',
        views.unique_details,
        name="unique_details"
    ),
    path('create-unique-details-filter/<str:unique_model_name>/<str:unique_field_name>/', views.create_unique_details_filter, name="create_unique_details_filter"),
    path('create-unique-details-page-items/<str:unique_id>/', views.create_unique_details_page_items, name="create_unique_details_page_items"),
    path('create-unique-details-hide-show-items/<str:unique_id>/', views.create_unique_details_hide_show_filter, name="create_unique_details_hide_show_filter"),
    path('delete-unique-details-filter/<int:id>/', views.delete_unique_details_filter, name="delete_unique_details_filter"),
    path('delete-unique-details-daterange-filter/<int:id>/', views.delete_unique_details_daterange_filter, name="delete_unique_details_daterange_filter"),
    path('delete-unique-details-intrange-filter/<int:id>/', views.delete_unique_details_intrange_filter, name="delete_unique_details_intrange_filter"),
    path('delete-unique-details-floatrange-filter/<int:id>/', views.delete_unique_details_floatrange_filter, name="delete_unique_details_floatrange_filter"),
    # re_path(r'^delete-unique-details/(?P<id>[0-9a-fA-F-]+)/$', views.delete_unique_details, name="delete_unique_details"),
    # re_path(r'^update-unique-details/(?P<id>[0-9a-fA-F-]+)/$', views.update_unique_details, name="update_unique_details"),

    re_path(r'^export-unique-details-csv/(?P<unique_model_name>[^/]+)/(?P<unique_field_name>[^/]+)/(?P<unique_value>.*)/$', views.ExportCSVView.as_view(), name="export_unique_details_csv"),
    re_path(r'^export-unique-details-excel/(?P<unique_model_name>[^/]+)/(?P<unique_field_name>[^/]+)/(?P<unique_value>.*)/$', views.ExportExcelView.as_view(), name="export_unique_details_excel"),
    # path('export-unique-details-pdf/', views.ExportPDFView.as_view(), name='export_unique_details_pdf'),
]