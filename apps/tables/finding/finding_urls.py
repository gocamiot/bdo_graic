from django.urls import path, re_path
from apps.tables.finding import finding_views as views

urlpatterns = [
    re_path(r'^finding(?:/(?P<companies>[\w\s,./;\'\[\]\-=<>?:"{}|_+!@#$%^&*()`~]+))?/$', views.finding, name="finding"),
    path('my-actions/', views.my_finding, name="my_finding"),
    path('finding_version_control_dt/<uuid:id>/', views.finding_version_control_dt, name="finding_version_control_dt"),
    path('create_finding/', views.create_finding, name="create_finding"),
    path('create-finding-filter/', views.create_finding_filter, name="create_finding_filter"),
    path('create-finding-page-items/', views.create_finding_page_items, name="create_finding_page_items"),
    path('create-finding-hide-show-items/', views.create_finding_hide_show_filter, name="create_finding_hide_show_filter"),
    path('delete-finding-filter/<int:id>/', views.delete_finding_view_filter, name="delete_finding_view_filter"),
    path('delete-finding-daterange-filter/<int:id>/', views.delete_finding_daterange_filter, name="delete_finding_daterange_filter"),
    path('delete-finding-intrange-filter/<int:id>/', views.delete_finding_intrange_filter, name="delete_finding_intrange_filter"),
    path('delete-finding-floatrange-filter/<int:id>/', views.delete_finding_floatrange_filter, name="delete_finding_floatrange_filter"),
    path('delete-finding/<uuid:id>/', views.delete_finding, name="delete_finding"),
    path('update-finding/<uuid:id>/', views.update_finding, name="update_finding"),
    path('update-my-action/<uuid:id>/', views.update_my_finding, name="update_my_finding"),
    path('get-sub-items/<int:pk>/', views.get_sub_items, name='get_sub_items'),

    re_path(r'^export-finding-csv(?:/(?P<companies>[\w\s,./;\'\[\]\-=<>?:"{}|_+!@#$%^&*()`~]+))?/$', views.ExportCSVView.as_view(), name='export_finding_csv'),
    re_path(r'^export-finding-docx(?:/(?P<companies>[\w\s,./;\'\[\]\-=<>?:"{}|_+!@#$%^&*()`~]+))?/$', views.ExportDocxView.as_view(), name='export_finding_docx'),
    # my finding export
    re_path(r'^export-my-finding-csv(?:/(?P<companies>[\w\s,./;\'\[\]\-=<>?:"{}|_+!@#$%^&*()`~]+))?/$', views.ExportMyFindingCSVView.as_view(), name='export_my_finding_csv'),
    re_path(r'^export-my-finding-docx(?:/(?P<companies>[\w\s,./;\'\[\]\-=<>?:"{}|_+!@#$%^&*()`~]+))?/$', views.ExportMyFindingDocxView.as_view(), name='export_my_finding_docx'),
    path('export-finding-pdf/', views.ExportPDFView.as_view(), name='export_finding_pdf'),
]