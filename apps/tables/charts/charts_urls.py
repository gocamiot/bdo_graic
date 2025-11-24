from django.urls import path, include
from apps.tables.charts import charts_views as views

urlpatterns = [
    path('charts/', include([
        path('add-chart/<str:tab_id>/', views.add_chart, name="add_chart"),
        path('<str:chart_id>/', views.chart_details, name="chart_details"),
        path('edit/<str:chart_id>/', views.edit_chart, name="edit_chart"),
        path('delete/<str:chart_id>/', views.delete_chart, name="delete_chart"),
    ])),
]