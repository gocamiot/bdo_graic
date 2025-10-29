from django.urls import path

from . import views

urlpatterns = [
    path("device_logins/", views.index, name="charts"),
    path("create-chart-filter/", views.create_chart_filter, name="create_chart_filter"),
    path('get-device-data/', views.get_device_data, name="get_device_data"),
    path('get-operating-data/', views.get_operating_data, name="get_operating_data"),
    path('get-operating-supported-data/', views.get_operating_supported_data, name="get_operating_supported_data"),
    path('get-ad-devices-data/', views.get_ad_device_data, name="get_ad_device_data"),
]