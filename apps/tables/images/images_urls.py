from django.urls import path

from apps.tables.images import images_views as views

urlpatterns = [
    path('images/<uuid:id>/', views.images, name="images"),
    path('create_images/', views.create_images, name="create_images"),
    path('create-images-filter/<uuid:img_loader_id>/', views.create_images_filter, name="create_images_filter"),
    path('create-images-page-items/<uuid:img_loader_id>/', views.create_images_page_items, name="create_images_page_items"),
    path('create-images-hide-show-items/<uuid:img_loader_id>/', views.create_images_hide_show_filter, name="create_images_hide_show_filter"),
    path('delete-images-filter/<int:id>/', views.delete_images_filter, name="delete_images_filter"),
    path('delete-images-daterange-filter/<int:id>/', views.delete_images_daterange_filter, name="delete_images_daterange_filter"),
    path('delete-images-intrange-filter/<int:id>/', views.delete_images_intrange_filter, name="delete_images_intrange_filter"),
    path('delete-images-floatrange-filter/<int:id>/', views.delete_images_floatrange_filter, name="delete_images_floatrange_filter"),
    path('delete-images/<int:id>/', views.delete_images, name="delete_images"),
    path('update-images/<int:id>/', views.update_images, name="update_images"),

    path('export-images-csv/<uuid:id>/', views.ExportCSVView.as_view(), name='export_images_csv'),
    path('export-images-pdf/', views.ExportPDFView.as_view(), name='export_images_pdf'),
]