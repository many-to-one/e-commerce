import os
import requests
from decimal import Decimal


PAYU_OAUTH_URL = os.getenv('PAYU_OAUTH_URL')
PAYU_API_URL = os.getenv('PAYU_API_URL')
PAYU_CLIENT_ID = os.getenv('PAYU_CLIENT_ID')
PAYU_CLIENT_SECRET = os.getenv('PAYU_CLIENT_SECRET')


def payu_authenticate():
    auth_url = PAYU_OAUTH_URL
    auth_data = {
        "grant_type": "client_credentials",
        "client_id": PAYU_CLIENT_ID,  # Replace with your actual client_id
        "client_secret": PAYU_CLIENT_SECRET  # Replace with your actual client_secret
    }

    try:
        auth_response = requests.post(auth_url, data=auth_data)
        # auth_response.raise_for_status()
        token_data = auth_response.json()
        print('*****payu_authenticate Token Data**********', token_data)
        access_token = token_data.get("access_token")
        if not access_token:
            return None
        return access_token
    except requests.RequestException as e:
        return None


def to_grosze(value):
    if isinstance(value, Decimal):
        return int(value * 100)
    return int(float(value) * 100)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # First IP in list
        print('*****get_client_ip X-Forwarded-For**********', ip)
    else:
        ip = request.META.get('REMOTE_ADDR')
        print('*****get_client_ip REMOTE_ADDR**********', ip)
    return ip