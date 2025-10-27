from rest_framework import viewsets, permissions
from .models import Report
from .serializers import ReportSerializer
from django.views.decorators.csrf import csrf_exempt

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().order_by('-created_at')
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
