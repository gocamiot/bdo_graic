from django.urls import path
from apps.graic import views

urlpatterns = [
    path('chat/', views.graic_chat_index, name="graic_chat_index"),
    path('chat/<uuid:chat_id>/', views.graic_chat, name="graic_chat"),
    path('ask/<uuid:chat_id>/', views.ask_graic, name="ask_graic"),
    path('chat/<uuid:chat_id>/delete/', views.graic_chat_delete, name="graic_chat_delete"),
    path('save_preprompt/', views.save_preprompt, name="save_preprompt"),
    path('get-prompt/', views.get_prompt_by_workflow, name="get_prompt_by_workflow"),

    path('export/word/<int:pk>/', views.export_graic_word, name='export_graic_word'),
    path('export/excel/<int:pk>/', views.export_graic_excel, name='export_graic_excel'),
    path("export/generated-file/<int:pk>/", views.export_generated_file, name="export_generated_file"),
    path('export/pdf/<int:pk>/', views.export_graic_pdf, name='export_graic_pdf'),
    path('export/markdown/<int:pk>/', views.export_graic_markdown, name='export_graic_markdown'),
]
