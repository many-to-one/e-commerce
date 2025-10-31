from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.http import JsonResponse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import redirect, render
from django import forms

import requests
import json
import os
from dotenv import load_dotenv

from store.models import Invoice
from vendor.models import Vendor


# Load variables from .env into environment
load_dotenv()

# Access them like normal environment variables
ALL_GRO_API_URL = os.getenv("ALL_GRO_API_URL")
AUTH_URL = os.getenv("AUTH_URL")
TOKEN_URL = os.getenv("TOKEN_URL")
REDIRECT_URI = os.getenv("REDIRECT_URI")


def get_access_token(authorization_code, vendor_name):
    print("Getting access token...----------------", authorization_code, vendor_name)
    vendor = Vendor.objects.get(name=vendor_name)
    print("Getting RETSET_CLIENT_ID...----------------", vendor.client_id)
    print("Getting access RETSET_CLIENT_SECRET...----------------", vendor.secret_id)

    try:
        data = {'grant_type': 'authorization_code', 'code': authorization_code, 'redirect_uri': f"{REDIRECT_URI}:5173/allegro-auth-code/{vendor_name}"}
        response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=True, auth=(vendor.client_id, vendor.secret_id))

        # print("RESPONSE CONTENT *$*$*$*$*$*$*$*$*$*$*$:", response.text)
        
        # print("Status --------------------------- :", response.status_code)
        # print("Body --------------------------- :", response.text)

        response.raise_for_status()  # This will raise HTTPError if status is 4xx/5xx

        tokens = response.json()
        # return tokens['access_token']
        return tokens
    except requests.exceptions.RequestException as err:
        print("Request failed:", err)
        raise

    

@api_view(['POST'])
def exchange_token_view(request, code, vendor_name):
    # print("Getting exchange_token_view...----------------", code, vendor_name)
    authorization_code = code #request.data.get('code')
    if not authorization_code:
        return JsonResponse({'error': 'Missing authorization code'}, status=400)

    try:
        tokens = get_access_token(authorization_code, vendor_name)
        if tokens:
            # print("Response get_access_token ---------------:", tokens)
            vendor = Vendor.objects.get(name=vendor_name)
            vendor.access_token = tokens['access_token']
            vendor.refresh_token = tokens['refresh_token']
            vendor.save()
        return Response({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token']
            })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

def get_next_token(token, vendor_name):

    vendor = Vendor.objects.get(name=vendor_name)
    try:
        data = {'grant_type': 'refresh_token', 'refresh_token': token, 'redirect_uri': f"{REDIRECT_URI}:5173/allegro-auth-code/{vendor_name}"}
        get_next_token_response = requests.post(TOKEN_URL, data=data, verify=False,
                                              allow_redirects=True, auth=(vendor.client_id, vendor.secret_id))
        # print("Response get_next_token_response ---------------:", get_next_token_response)
        tokens = json.loads(get_next_token_response.text)
        vendor.access_token = tokens['access_token']
        vendor.refresh_token = tokens['refresh_token']
        vendor.save(update_fields=['access_token', 'refresh_token'])
        return tokens['access_token']
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    

# import requests
# from django.conf import settings

def allegro_request(method, url, vendor_name, **kwargs):
    """
    Wrapper for Allegro API requests that auto-refreshes token on 401.
    """

    vendor = Vendor.objects.get(name=vendor_name)

    # Ensure Authorization header
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {vendor.access_token}"
    kwargs["headers"] = headers

    response = requests.request(method, url, **kwargs)

    if response.status_code == 401:
        # Refresh token
        new_token = get_next_token(vendor.refresh_token, vendor_name)

        # Retry with new token
        headers["Authorization"] = f"Bearer {new_token}"
        kwargs["headers"] = headers
        response = requests.request(method, url, **kwargs)

    return response

    # needed functions??

@method_decorator(staff_member_required, name='dispatch')
class AllegroOrderAdminView(View):
    def get(self, request):
        from store.admin import AllegroOrderAdmin
        from store.models import AllegroOrder

        admin_instance = AllegroOrderAdmin(AllegroOrder, admin_site=None)
        admin_instance.fetch_and_store_allegro_orders(request, queryset=None)

        messages.success(request, "✅ Synchronizacja Allegro zakończona.")
        return redirect('/admin/store/allegroorder/')
    


# def correction_view(self, request, invoice_id):
#         invoice = Invoice.objects.get(pk=invoice_id)
#         products = invoice.products  # zakładam, że masz JSONField albo relację na produkty

#         # dynamiczny formularz
#         class DynamicCorrectionForm(forms.Form):
#             def __init__(self, *args, **kwargs):
#                 super().__init__(*args, **kwargs)
#                 for i, product in enumerate(products, start=1):
#                     self.fields[f"quantity_{i}"] = forms.IntegerField(
#                         label=f"{product['offer']['name']}",
#                         initial=product['quantity'],
#                         min_value=0
#                     )

#         if request.method == "POST":
#             form = DynamicCorrectionForm(request.POST)
#             if form.is_valid():
#                 corrected_products = []
#                 for i, product in enumerate(products, start=1):
#                     new_qty = form.cleaned_data[f"quantity_{i}"]
#                     corrected_products.append({
#                         **product,
#                         "quantity": new_qty
#                     })

#                 # utwórz nową fakturę korekcyjną
#                 correction = Invoice.objects.create(
#                     invoice_number=f"KOREKTA-{invoice.invoice_number}",
#                     shop_order=invoice.shop_order,
#                     allegro_order=invoice.allegro_order,
#                 )
#                 # zakładam, że masz pole JSONField na produkty
#                 correction.products = corrected_products
#                 correction.save()

#                 self.message_user(request, f"Utworzono korektę faktury nr {invoice.invoice_number}")
#                 return redirect("..")  # powrót do listy faktur
#         else:
#             form = DynamicCorrectionForm()

#         context = {
#             "form": form,
#             "invoice": invoice,
#             "title": f"Korekta faktury nr {invoice.invoice_number}",
#         }
#         return render(request, "admin/invoice_correction.html", context)