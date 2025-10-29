from django.urls import path

from apps.tables.image_loader import image_loader_views as views

urlpatterns = [
    path('image_loader/', views.image_loader, name="image_loader"),
    path('create_image_loader/', views.create_image_loader, name="create_image_loader"),
    path('create-image-loader-filter/', views.create_image_loader_filter, name="create_image_loader_filter"),
    path('create-image-loader-page-items/', views.create_image_loader_page_items, name="create_image_loader_page_items"),
    path('create-image-loader-hide-show-items/', views.create_image_loader_hide_show_filter, name="create_image_loader_hide_show_filter"),
    path('delete-image-loader-filter/<int:id>/', views.delete_image_loader_filter, name="delete_image_loader_filter"),
    path('delete-image-loader-daterange-filter/<int:id>/', views.delete_image_loader_daterange_filter, name="delete_image_loader_daterange_filter"),
    path('delete-image-loader-intrange-filter/<int:id>/', views.delete_image_loader_intrange_filter, name="delete_image_loader_intrange_filter"),
    path('delete-image-loader-floatrange-filter/<int:id>/', views.delete_image_loader_floatrange_filter, name="delete_image_loader_floatrange_filter"),
    path('delete-image-loader/<uuid:id>/', views.delete_image_loader, name="delete_image_loader"),
    path('update-image-loader/<uuid:id>/', views.update_image_loader, name="update_image_loader"),

    path('export-image-loader-csv/', views.ExportCSVView.as_view(), name='export_image_loader_csv'),
    path('export-image-loader-pdf/', views.ExportPDFView.as_view(), name='export_image_loader_pdf'),

    path('image_loader_version_control_dt/<uuid:id>/', views.image_loader_version_control_dt, name="image_loader_version_control_dt"),
]