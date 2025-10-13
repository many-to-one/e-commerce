from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse

import requests
import json
import os

from vendor.models import Vendor


def get_access_token(authorization_code, vendor_name):
    print("Getting access token...----------------", authorization_code, vendor_name)
    vendor = Vendor.objects.get(name=vendor_name)
    print("Getting RETSET_CLIENT_ID...----------------", vendor.client_id)
    print("Getting access RETSET_CLIENT_SECRET...----------------", vendor.secret_id)

    try:
        # data = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': "http://localhost:5173/allegro-auth-code/retse"}
        # response = requests.post("https://allegro.pl.allegrosandbox.pl/auth/oauth/token", data=data, verify=False,
        #                                       allow_redirects=True, auth=(os.environ.get('RETSET_CLIENT_ID'), os.environ.get('RETSET_CLIENT_SECRET')))

        data = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': f"http://localhost:5173/allegro-auth-code/{vendor_name}"}
        response = requests.post("https://allegro.pl.allegrosandbox.pl/auth/oauth/token", data=data, verify=True,
                                            allow_redirects=True, auth=(vendor.client_id, vendor.secret_id))
        print("RESPONSE CONTENT *$*$*$*$*$*$*$*$*$*$*$:", response.text)
        
        print("Status --------------------------- :", response.status_code)
        print("Body --------------------------- :", response.text)

        response.raise_for_status()  # This will raise HTTPError if status is 4xx/5xx

        tokens = response.json()
        return tokens['access_token']
    except requests.exceptions.RequestException as err:
        print("Request failed:", err)
        raise

    

@api_view(['POST'])
def exchange_token_view(request, code, vendor_name):
    print("Getting exchange_token_view...----------------", code, vendor_name)
    authorization_code = code #request.data.get('code')
    if not authorization_code:
        return JsonResponse({'error': 'Missing authorization code'}, status=400)

    try:
        access_token = get_access_token(authorization_code, vendor_name)
        if access_token:
            print("Access Token:", access_token)
            vendor = Vendor.objects.get(name=vendor_name)
            vendor.access_token = access_token
            vendor.save()
        return Response({'access_token': access_token})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)