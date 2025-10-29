from django.urls import path

from apps.tables.finding_attachment import finding_attachment_views as views

urlpatterns = [
    path('finding-attachment/<uuid:id>/', views.finding_attachment, name="finding_attachment"),
    path('finding_attachments_version_control_dt/<int:id>/', views.finding_attachments_version_control_dt, name="finding_attachments_version_control_dt"),
    path('create-finding-attachment/<uuid:id>/', views.create_finding_attachment, name="create_finding_attachment"),
    path('create-finding-attachment-filter/', views.create_finding_attachment_filter, name="create_finding_attachment_filter"),
    path('create-finding-attachment-page-items/', views.create_finding_attachment_page_items, name="create_finding_attachment_page_items"),
    path('create-finding-attachment-hide-show-items/', views.create_finding_attachment_hide_show_filter, name="create_finding_attachment_hide_show_filter"),
    path('delete-finding-attachment-filter/<int:id>/', views.delete_finding_attachment_filter, name="delete_finding_attachment_filter"),
    path('delete-finding-attachment/<int:id>/', views.delete_finding_attachment, name="delete_finding_attachment"),
    path('update-finding-attachment/<int:id>/', views.update_finding_attachment, name="update_finding_attachment"),
    path('finding_attachment_duplicate_row/<int:id>/', views.finding_attachment_duplicate_row, name="finding_attachment_duplicate_row"),

    path('export-finding-attachment-csv/', views.ExportCSVView.as_view(), name='export_finding_attachment_csv'),
    path('download_attachment/<int:id>/', views.download_attachment, name='download_attachment'),
]