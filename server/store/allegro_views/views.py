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

from store.models import Invoice
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
    

@method_decorator(staff_member_required, name='dispatch')
class AllegroOrderAdminView(View):
    def get(self, request):
        from store.admin import AllegroOrderAdmin
        from store.models import AllegroOrder

        admin_instance = AllegroOrderAdmin(AllegroOrder, admin_site=None)
        admin_instance.fetch_and_store_allegro_orders(request, queryset=None)

        messages.success(request, "✅ Synchronizacja Allegro zakończona.")
        return redirect('/admin/store/allegroorder/')
    


def correction_view(self, request, invoice_id):
        invoice = Invoice.objects.get(pk=invoice_id)
        products = invoice.products  # zakładam, że masz JSONField albo relację na produkty

        # dynamiczny formularz
        class DynamicCorrectionForm(forms.Form):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                for i, product in enumerate(products, start=1):
                    self.fields[f"quantity_{i}"] = forms.IntegerField(
                        label=f"{product['offer']['name']}",
                        initial=product['quantity'],
                        min_value=0
                    )

        if request.method == "POST":
            form = DynamicCorrectionForm(request.POST)
            if form.is_valid():
                corrected_products = []
                for i, product in enumerate(products, start=1):
                    new_qty = form.cleaned_data[f"quantity_{i}"]
                    corrected_products.append({
                        **product,
                        "quantity": new_qty
                    })

                # utwórz nową fakturę korekcyjną
                correction = Invoice.objects.create(
                    invoice_number=f"KOREKTA-{invoice.invoice_number}",
                    shop_order=invoice.shop_order,
                    allegro_order=invoice.allegro_order,
                )
                # zakładam, że masz pole JSONField na produkty
                correction.products = corrected_products
                correction.save()

                self.message_user(request, f"Utworzono korektę faktury nr {invoice.invoice_number}")
                return redirect("..")  # powrót do listy faktur
        else:
            form = DynamicCorrectionForm()

        context = {
            "form": form,
            "invoice": invoice,
            "title": f"Korekta faktury nr {invoice.invoice_number}",
        }
        return render(request, "admin/invoice_correction.html", context)