from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse

import requests
import json
import os

from users.models import User


@api_view(['GET'])
def user_vendors(request, email):
    try:
        user = User.objects.get(email=email)
        vendors = user.vendor.all()  # assuming ForeignKey with related_name='vendors'
        vendor_data = [{'id': v.id, 'name': v.name, 'client_id': v.client_id, 'marketplace': v.marketplace,} for v in vendors]
        return Response({'vendors': vendor_data})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
