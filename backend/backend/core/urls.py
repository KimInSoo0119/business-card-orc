from django.urls import path
from .views import BusinessCardUploadView, CustomerListView, CustomerDeleteView

urlpatterns = [
    path('api/business-card/', BusinessCardUploadView.as_view()),
    path('api/business-card/list/', CustomerListView.as_view()),
    path('api/business-card/<str:customer_id>/', CustomerDeleteView.as_view()),
]