from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Quote
from .serializers import QuoteSerializer
class QuoteViewSet(viewsets.ModelViewSet):
    queryset=Quote.objects.all()
    serializer_class=QuoteSerializer