# import time
# from django.core.files.base import ContentFile

# from .views import allegro_request

# def create_label(order, ALLEGRO_API_URL, resp, vendor, headers, errors, zip_file):

#     order.commandId = resp.json().get('commandId')
#     order.save(update_fields=['commandId'])
#     ship_url = f"https://{ALLEGRO_API_URL}/shipment-management/shipments/create-commands/{resp.json().get('commandId')}"
#     ship_resp = allegro_request("GET", ship_url, vendor.name, headers=headers)
#     ship_data = ship_resp.json()
#     print('Fetching shipment ship_resp ##################### ', ship_resp, ship_resp.text)
#     if ship_resp.status_code == 400 or ship_resp.status_code == 401:
#         errors.add(f"❌ 1688 {ship_resp.status_code} - {ship_resp.json().get('errors', [{}])[0].get('userMessage')}\n")
#     else:
#         # if ship_resp.json().get('status') == "ERROR" and ship_resp.json().get('errors', [{}])[0].get('code') == "DIMENSIONS_VALIDATION_ERROR":
#         #     order.error = f"❌ {ship_resp.json().get('errors', [{}])[0].get('userMessage')}\n"
#         #     order.save(update_fields=['error'])

#         if ship_resp.json().get('status') == "ERROR": 
#             err = ship_resp.json().get('errors', [{}])[0] 
#             if err.get('code') == "DIMENSIONS_VALIDATION_ERROR": 
#                 print('_________________________Dimension error creating shipment:___________________________ ', err)
#                 order.error = f"❌ {err.get('message')}\n"
#                 order.save(update_fields=['error']) 
#                 return None, None

#         if ship_resp.json().get('status') == "IN_PROGRESS":
#             # self.message_user(request, f"Status tworzenia przesyłki {vendor.name}: {ship_resp.status_code} - {ship_resp.text}", level='info')
#             attempt = 1
#             max_attempts = 10

#             while attempt <= max_attempts:

#                 retry_after = ship_resp.headers.get("Retry-After")
#                 wait_seconds = int(retry_after) if retry_after else 1

#                 print(f"⏳ Waiting {wait_seconds}s for Allegro shipment creation (attempt {attempt}/{max_attempts})...")
#                 # self.message_user(request, f"⏳ Waiting {wait_seconds}s for Allegro shipment creation (attempt {attempt}/{max_attempts})...", level='info')

#                 time.sleep(wait_seconds)

#                 ship_resp = allegro_request("GET", ship_url, vendor.name, headers=headers)
#                 ship_data = ship_resp.json()

#                 # Stop if error
#                 if ship_data.get('status') == "ERROR": 
#                     err = ship_data.get('errors', [{}])[0] 
#                     if err.get('code') == "DIMENSIONS_VALIDATION_ERROR": 
#                         print('_________________________Dimension error creating shipment:___________________________ ', err)
#                         order.error = f"❌ {err.get('message')}\n"
#                         order.save(update_fields=['error']) 
#                         return None, None

#                 # Stop if success
#                 if ship_data.get("status") == "SUCCESS" and ship_data.get("shipmentId"):
#                     # self.message_user(request, f"✅ Przesyłka utworzona: {ship_data.get('shipmentId')}", level='info')
#                     # order.error = ""
#                     # order.save(update_fields=['error'])

#                     break

#                 attempt += 1

#         print('Fetching shipment ship_resp ********************* ', ship_resp, ship_resp.text)
#         order.shipmentId = ship_resp.json().get('shipmentId')
#         order.save(update_fields=['shipmentId'])
#         label_url = f"https://{ALLEGRO_API_URL}/shipment-management/label"
#         label_header = {
#             "Accept": "application/octet-stream",
#             "Authorization": f"Bearer {vendor.access_token}",
#             "Content-Type": "application/vnd.allegro.public.v1+json"
#         }
#         payload_label = {
#             "shipmentIds": [order.shipmentId], # na drugiej stronie - jak wyeliminować?
#             "pageSize": "A6",
#             "cutLine": False,
#             # "summaryReport": {
#             #     "placement": "LAST",
#             #     "fields": [
#             #         "WAYBILL",                     # niepusta tablica pól drukowanych w raporcie, dostępne wartości: 
#             #         # order.order_id,                         # WAYBILL, ORDER_ID, BUYER_LOGIN, ITEMS, DIMS_AND_WEIGHT, 
#             #         # order.buyer_login,                  # ADD_LABEL_TEXT,  NOTES_FOR_ORDER, REF_NUMBER, COD, 
#             #                                     # INSURANCE
#             #     ]
#             # }
#         }
#         label_resp = allegro_request("POST", label_url, vendor.name, headers=label_header, json=payload_label)
#         if label_resp.status_code == 200:

#             pdf_bytes = label_resp.content 
#             filename = f"label_{order.order_id}.pdf" 

#             # Save PDF to model field                           
#             order.label_file.save(filename, ContentFile(pdf_bytes)) 
#             order.save(update_fields=["label_file"]) 

#             # Add PDF to ZIP 
#             # zip_file.writestr(filename, pdf_bytes)
#             print("__________________label_resp.status_code == 200______________")

#             # return zip_file
#             return filename, pdf_bytes

#         else:
#             print('_________________________Error creating label:___________________________ ', label_resp, label_resp.text)
#             errors.add(f"❌ 1768 {label_resp.status_code} - {label_resp.json().get('errors', [{}])[0].get('userMessage')}\n")
#             return None, None
#             # return errors







import time
from django.core.files.base import ContentFile
from .views import allegro_request


def create_label(order, ALLEGRO_API_URL, resp, vendor, headers, errors, zip_file):

    label_error = None

    # 1) Zapisz commandId
    command_id = resp.json().get("commandId")
    order.commandId = command_id
    order.save(update_fields=["commandId"])

    # 2) Pobierz status tworzenia przesyłki
    ship_url = f"https://{ALLEGRO_API_URL}/shipment-management/shipments/create-commands/{command_id}"
    ship_resp = allegro_request("GET", ship_url, vendor.name, headers=headers)
    print("Fetching shipment ship_resp ##################### ", ship_resp, ship_resp.text)

    # 3) Błędy HTTP
    if ship_resp.status_code in (400, 401):
        # errors.add(f"❌ 1688 {ship_resp.status_code} - "
        #            f"{ship_resp.json().get('errors', [{}])[0].get('userMessage')}\n")
        order.error = f"❌ {ship_resp.status_code} - {ship_resp.json().get('errors', [{}])[0].get('userMessage')}\n"
        order.save(update_fields=["error"])
        return None, None

    ship_data = ship_resp.json()

    # 4) Błąd DIMENSIONS od razu
    if ship_data.get("status") == "ERROR":
        err = ship_data.get("errors", [{}])[0]
        if err.get("code") == "DIMENSIONS_VALIDATION_ERROR":
            label_error = f"{err.get('userMessage')}\n"
            print("_________________________Dimension error creating shipment:___________________________ ", label_error)
            order.error = f"❌ Allegro nie utworzyło przesyłki. Status: : {label_error}\n"
            order.save(update_fields=["error"])
            return None, None

    # 5) Jeśli IN_PROGRESS → retry
    if ship_data.get("status") == "IN_PROGRESS":
        attempt = 1
        max_attempts = 10

        while attempt <= max_attempts:

            retry_after = ship_resp.headers.get("Retry-After")
            wait_seconds = int(retry_after) if retry_after else 1

            print(f"⏳ Waiting {wait_seconds}s for Allegro shipment creation (attempt {attempt}/{max_attempts})...")
            time.sleep(wait_seconds)

            ship_resp = allegro_request("GET", ship_url, vendor.name, headers=headers)
            ship_data = ship_resp.json()

            # Jeśli ERROR podczas retry
            if ship_data.get("status") == "ERROR":
                err = ship_data.get("errors", [{}])[0]
                print("_________________________Error during retry:___________________________ ", err)

                if err.get("code") == "DIMENSIONS_VALIDATION_ERROR":
                    order.error = f"❌ {err.get('userMessage')}\n"
                    order.save(update_fields=["error"])
                    return None, None

                errors.add(f"❌ Błąd tworzenia przesyłki: {err.get('userMessage')}")
                return None, None

            # Jeśli SUCCESS → przerywamy retry
            if ship_data.get("status") == "SUCCESS" and ship_data.get("shipmentId"):
                break

            attempt += 1

    # 6) Po retry — sprawdź finalny status
    final_status = ship_data.get("status")
    shipment_id = ship_data.get("shipmentId")

    if final_status != "SUCCESS" or not shipment_id:
        # order.error = f"❌ Allegro nie utworzyło przesyłki. Status: {final_status}, shipmentId: {shipment_id}: {label_error}\n"
        # order.save(update_fields=["error"])
        return None, None

    # 7) Zapisz shipmentId
    order.shipmentId = shipment_id
    order.save(update_fields=["shipmentId"])

    # 8) Pobierz etykietę
    label_url = f"https://{ALLEGRO_API_URL}/shipment-management/label"
    label_header = {
        "Accept": "application/octet-stream",
        "Authorization": f"Bearer {vendor.access_token}",
        "Content-Type": "application/vnd.allegro.public.v1+json"
    }
    payload_label = {
        "shipmentIds": [shipment_id],
        "pageSize": "A6",
        "cutLine": False
    }

    label_resp = allegro_request("POST", label_url, vendor.name, headers=label_header, json=payload_label)

    # 9) Obsługa błędu etykiety
    if label_resp.status_code != 200:
        print("_________________________Error creating label:___________________________ ", label_resp, label_resp.text)
        order.error = f"❌ {label_resp.status_code} - {label_resp.json().get('errors', [{}])[0].get('userMessage')}\n "
        order.save(update_fields=["error"])
        return None, None

    # 10) Zapis PDF
    pdf_bytes = label_resp.content
    filename = f"label_{order.order_id}.pdf"

    order.label_file.save(filename, ContentFile(pdf_bytes))
    order.save(update_fields=["label_file"])

    print("__________________label_resp.status_code == 200______________")

    return filename, pdf_bytes
