from django.urls import path

from . import views

urlpatterns = [
    path("list_of_devices/", views.list_of_devices, name="list_of_devices"),
    path("create_device/", views.create_device, name="create_device"),
    path('create-device-filter/', views.create_device_filter, name="create_device_filter"),
    path('create-device-page-items/', views.create_device_page_items, name="create_device_page_items"),
    path('create-device-hide-show-items/', views.create_device_hide_show_filter, name="create_device_hide_show_filter"),
    path('delete-device-filter/<int:id>/', views.delete_device_filter, name="delete_device_filter"),
    path('delete-daterange-filter/<int:id>/', views.delete_daterange_filter, name="delete_daterange_filter"),
    path('delete-device/<int:id>/', views.delete_device, name="delete_device"),
    path('update-device/<int:id>/', views.update_device, name="update_device"),

    path('export-csv/', views.ExportCSVView.as_view(), name='export_csv'),
    path('export-pdf/', views.ExportPDFView.as_view(), name='export_pdf'),

    path('user-devices/', views.user_devices, name='user_devices'),
    path('save_selected_dt/', views.save_selected_dt, name="save_selected_dt"),

    path('add-to-favorite/<str:model_name>/<str:model_choice>/', views.add_to_favorite, name="add_to_favorite"),
    path('add-favorite-from-favorite/<str:favorite_id>/', views.add_favorite_from_favorite, name="add_favorite_from_favorite"),

    path('favorite/<str:id>/', views.favorite_details, name="favorite_details"),
    path('remove-favorite/<str:id>/', views.remove_favorite, name="remove_favorite"),
    path('create-favorite-filter/<str:favorite_id>/', views.create_favorite_filter, name="create_favorite_filter"),
    path('remove-favorite-filter/', views.delete_favorite_filter, name="delete_favorite_filter"),
    path('remove-favorite-date-range-filter/<int:id>/', views.delete_favorite_date_range_filter, name="delete_favorite_date_range_filter"),
    path('remove-favorite-int-range-filter/<int:id>/', views.delete_favorite_int_range_filter, name="delete_favorite_int_range_filter"),
    path('remove-favorite-float-range-filter/<int:id>/', views.delete_favorite_float_range_filter, name="delete_favorite_float_range_filter"),

    path('create-favorite-page-items/<str:favorite_id>/', views.create_favorite_page_items, name="create_favorite_page_items"),
    path('create-favorite-hide-show-items/<str:favorite_id>/', views.create_favorite_hide_show_filter, name="create_favorite_hide_show_filter"),

    path('add-favorite-description/<str:favorite_id>/', views.add_favorite_description, name="add_favorite_description"),
    path('export-favorite-csv/<str:id>/', views.export_favorite_csv_view, name='export_favorite_csv_view'),

    path('check_task_status/<str:task_id>/', views.check_task_status, name='check_task_status'),

    # File
    # path('file-upload/', views.file_upload, name="file_upload"),
    # path('download-file/<int:file_id>/', views.download_file, name="download_file"),
    # path('delete-file/<int:file_id>/', views.delete_file, name="delete_file"),

    # Global urls
    path('delete-saved-filter/', views.delete_saved_filter, name="delete_saved_filter"),
    path('upload-csv/<str:model_name>/', views.loader_csv_upload, name="loader_csv_upload"),
    path('upload-query/<str:model_name>/', views.loader_query_upload, name="loader_query_upload"),
    path('ipe-details/', views.ipe_details, name="ipe_details"),
    path('save-selected-rows/', views.save_selected_rows, name="save_selected_rows"),
    path('delete-unmatched/', views.delete_unmatched, name="delete_unmatched"),
    path('create_py_func_prompt/', views.create_py_func_prompt, name="create_py_func_prompt"),
    path('create_py_func/', views.create_py_func, name="create_py_func"),
    path('edit_py_func/', views.edit_py_func, name="edit_py_func"),

    path('fetch-stored-procedure-data/<str:name>/<str:model_name>/', views.trigger_fetch_stored_procedure_data, name="fetch_stored_procedure_data"),
    path('fetch-api-data/<str:model_name>/', views.trigger_fetch_api_data, name="trigger_fetch_api_data"),

    path('export-ipe-description/<int:ipe_id>/', views.export_ipe_description, name="export_ipe_description"),
    path('save-column-order/', views.save_column_order, name='save_column_order'),
]