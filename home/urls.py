from django.urls import path

from . import views

urlpatterns = [
    # path("", views.index, name="index"),
    path("", views.starter, name="starter"),
    path("index/", views.index, name="index"),
    path("starter/", views.starter, name="starter"),
    #path('get-device-data/', views.get_device_data, name="get_device_data"),

    path('create-table-dropdown/', views.create_table_dropdown, name="create_table_dropdown"),
    path('update-table-dropdown/<int:id>/', views.update_table_dropdown, name="update_table_dropdown"),
    path('delete-table-dropdown/<int:id>/', views.delete_table_dropdown, name="delete_table_dropdown"),
    path('create-sub-items/<int:id>/', views.create_sub_items, name="create_sub_items"),
    path('update-sub-items/<int:id>/', views.update_sub_item, name="update_sub_item"),
    path('delete-sub-items/<int:id>/', views.delete_sub_item, name="delete_sub_item"),

    # Dependent dropdown
    path('create-dependent-dropdown/', views.create_dependent_dropdown, name="create_dependent_dropdown"),
    path('update-dependent-dropdown/<int:id>/', views.update_dependent_dropdown, name="update_dependent_dropdown"),
    path('delete-dependent-dropdown/<int:id>/', views.delete_dependent_dropdown, name="delete_dependent_dropdown"),
    path('create-dependent-subitems/<int:id>/', views.create_dependent_sub_items, name="create_dependent_sub_items"),

    # Join models
    path('join-models/', views.join_models, name='join_models'),
    path('check_model_exists/', views.check_model_exists, name='check_model_exists'),
    path('check-task-status/', views.check_task_status, name='check_task_status'),
    path('view-404/', views.join_view_404, name='join_view_404'),

    path('load-data-to-join-model/<str:model_name>/<int:pk>/', views.load_data_to_join_model, name="load_data_to_join_model"),

    # Model builder
    path('model-builder/', views.model_builder, name='model_builder'),
    path('process-file/', views.process_file, name='process_file'),
    path('sap-api-headers/<int:id>/', views.sap_api_headers, name='sap_api_headers'),
    path('sap-api-data/<int:id>/', views.sap_api_data, name='sap_api_data'),
    path('sql-query-headers/<int:id>/', views.sql_query_headers, name='sql_query_headers'),
    path('sql-query-data/<int:id>/', views.sql_query_data, name='sql_query_data'),
]
