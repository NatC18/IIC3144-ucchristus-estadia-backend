"""
URLs for data_loader app
"""
from django.urls import path
from . import views

app_name = 'data_loader'

urlpatterns = [
    path('info/', views.data_loader_info, name='data_loader_info'),
    # Add your data loader endpoints here
    # path('upload/', views.upload_excel, name='upload_excel'),
    # path('process/', views.process_data, name='process_data'),
]