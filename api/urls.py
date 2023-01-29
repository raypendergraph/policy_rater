from .views import QuoteViewSet
from django.urls import path, include
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'quotes', QuoteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
