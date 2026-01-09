from django.urls import path, include
from apps.tables.charts import charts_views as views

urlpatterns = [
    path('charts/', include([
        path('add-chart/<str:tab_id>/', views.add_chart, name="add_chart"),
        path('add-filter/<str:chart_id>/', views.create_chart_filter, name="create_chart_filter"),
        path('<str:chart_id>/', views.chart_details, name="chart_details"),
        path('edit/<str:chart_id>/', views.edit_chart, name="edit_chart"),
        path('delete/<str:chart_id>/', views.delete_chart, name="delete_chart"),
        path("export/pdf/", views.export_chart_pdf, name="export_chart_pdf"),
        path("export/docx/", views.export_chart_docx, name="export_chart_docx"),
        path("export/pdf_bulk/", views.export_charts_pdf_bulk, name="export_charts_pdf_bulk"),
        path("export/docx_bulk/", views.export_charts_docx_bulk, name="export_charts_docx_bulk"),

        path("export/schedule/", views.create_chart_export_schedule, name="create_chart_export_schedule"),
    ])),
]