from django.urls import path, include
from apps.tables.risk_card import risk_card_views as views

urlpatterns = [
    path('risk-card/', include([
        path('create/<str:tab_id>/', views.add_risk_card, name="add_risk_card"),
        path('add-filter/<str:chart_id>/', views.create_risk_chart_filter, name="create_risk_chart_filter"),
        path('delete/<str:score_card_id>/', views.delete_score_card, name="delete_score_card"),

        path('export-risk-docx/', views.export_risk_docx, name='export_risk_docx'),
        path('export-risk-pdf/', views.export_risk_pdf, name='export_risk_pdf'),

        path("export/schedule/", views.create_risk_export_schedule, name="create_risk_export_schedule"),
        path('<str:chart_id>/', views.risk_chart_details, name="risk_chart_details"),
    ])),
]