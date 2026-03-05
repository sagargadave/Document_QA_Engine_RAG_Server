from django.urls import path
from . import views

urlpatterns = [
    # Document CRUD URLs 
    path('', views.DocumentListView.as_view(), name='document_list'), # Home/List
    path('upload/', views.DocumentCreateView.as_view(), name='document_upload'),
    path('edit/<int:pk>/', views.DocumentUpdateView.as_view(), name='document_edit'),
    path('delete/<int:pk>/', views.DocumentDeleteView.as_view(), name='document_delete'),
    
    path('ask/<int:doc_id>', views.ask_question, name='ask_question'), 
    
]
