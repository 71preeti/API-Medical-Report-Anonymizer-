from django.urls import path
from . import views

urlpatterns = [
    path('api/upload-image/', views.index, name='index'),
    path('download/<str:filename>/', views.download, name='download'),
]
