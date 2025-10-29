from django.urls import path
from apps.file_manager import views


urlpatterns = [
    path('file-manager/', views.file_manager, name="file_manager"),
    path('file-manager/<str:slug>/', views.sub_folders, name="sub_folders"),
    path('files/upload/', views.upload_file_to_folder, name='upload_file_to_folder'),

    path('folders/create/', views.create_folder, name='create_folder'),
    path('folders/create/<str:slug>/', views.create_folder, name='create_subfolder'),

    path('delete/folder/<int:pk>/', views.delete_folder, name='delete_folder'),
    path('edit/folder/<int:pk>/', views.edit_folder, name='edit_folder'),

    path('delete/file/<int:pk>/', views.delete_file, name='delete_file'),
    path('edit/file/<int:pk>/', views.edit_file, name='edit_file'),

    path('delete-selected-items/', views.delete_selected_items, name='delete_selected_items'),
    path('set-default-value/', views.set_default_value, name='set_default_value'),
    path('clear-default/', views.clear_default, name='clear_default'),
]
