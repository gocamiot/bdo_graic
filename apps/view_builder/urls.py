from apps.view_builder import views
from django.urls import path


urlpatterns = [
    path('', views.index, name="view_builder_index"),
    path('get-model-fields/', views.get_model_fields, name='get_model_fields'),
    path('get-model-data/', views.get_model_data, name='get_model_data'),
]
