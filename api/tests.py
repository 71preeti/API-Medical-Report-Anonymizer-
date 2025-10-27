from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Report

User = get_user_model()

class ReportAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_create_report(self):
        url = reverse('report-list')
        data = {'title':'T','content':'C'}
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Report.objects.count(), 1)
