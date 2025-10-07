from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse

import requests
import json
import os

def get_access_token(authorization_code):
    print("Getting access token...----------------", authorization_code)

    try:
        data = {'grant_type': 'client_credentials', 'code': authorization_code, 'redirect_uri': "http://localhost"}
        response = requests.post("https://allegro.pl.allegrosandbox.pl/auth/oauth/token", data=data, verify=False,
                                              allow_redirects=False, auth=(os.environ.get('RETSET_CLIENT_ID'), os.environ.get('RETSET_CLIENT_SECRET')))

        print("Status --------------------------- :", response.status_code)
        print("Body --------------------------- :", response.text)

        response.raise_for_status()  # This will raise HTTPError if status is 4xx/5xx

        tokens = response.json()
        return tokens['access_token']
    except requests.exceptions.RequestException as err:
        print("Request failed:", err)
        raise

    

@api_view(['POST'])
def exchange_token_view(request, code):
    print("Getting exchange_token_view...----------------", code)
    authorization_code = code #request.data.get('code')
    if not authorization_code:
        return JsonResponse({'error': 'Missing authorization code'}, status=400)

    try:
        access_token = get_access_token(authorization_code)
        return Response({'access_token': access_token})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)