import re
import time

from .views import allegro_request

def create_shipment(ALLEGRO_API_URL, vendor, order, package):

    print(' ***************************** create_shipment package ***************************** ', package)

    address = "ul. Testowa 1, 67-400 Wschowa"
    match = re.search(r"\b\d{2}-\d{3}\b", address)

    postal_code = match.group(0) if match else None
    # print(postal_code)  # 67-400

    url_1 = f"https://{ALLEGRO_API_URL}/shipment-management/shipments/create-commands"
    headers_post = {
        "Authorization": f"Bearer {vendor.access_token}",
        "Accept": "application/vnd.allegro.public.v1+json",
        "Content-Type": "application/vnd.allegro.public.v1+json"
    }
    payload = {
        # "commandId": uuid4().hex,
        "input": {
            "deliveryMethodId": order.delivery_method_id,  
                "sender":{    # wymagane, dane nadawcy
                    "name": vendor.name,    # dane osobowe nadawcy
                    "company":vendor.name,    # nazwa firmy
                    "street": vendor.address,    # ulica oraz numer budynku
                    "postalCode": postal_code,    # kod pocztowy
                    "city":"Wschowa",    # miasto
                    "countryCode":"PL",    # kod kraju zgodny ze standardem ISO 3166-1 alpha-2
                    "email": vendor.email,    # adres e-mail
                    "phone": vendor.mobile,    # numer telefonu nadawcy
                    # "point":"A1234567"    # wymagane, jeśli adresem nadawczym jest punkt odbioru
                },
                "receiver":{    # wymagane, dane odbiorcy
                    "name": f"{order.delivery_address["firstName"]} {order.delivery_address["lastName"]}",    # dane osobowe odbiorcy
                    "company": order.delivery_address["companyName"],    # nazwa firmy
                    "street": order.delivery_address["street"],    # ulica oraz numer budynku
                    "postalCode": order.delivery_address["zipCode"],    # kod pocztowy
                    "city": order.delivery_address["city"],    # miasto
                    "countryCode": order.delivery_address["countryCode"],    # kod kraju zgodny ze standardem ISO 3166-1 alpha-2
                    "email": order.buyer_email,    # wymagany, adres e-mail. Musisz  przekazać prawidłowy maskowany adres e-mail wygenerowany przez Allegro, np. hamu7udk3p+17454c1b6@allegromail.pl
                    "phone": order.delivery_address["phoneNumber"],    # numer telefonu
                    "point": order.pickup_point_id    # wymagane, jeśli adresem odbiorczym jest punkt odbioru. ID punktu odbioru, pobierzesz z danych zamówienia za pomocą GET /order/checkout-forms
                },
                "referenceNumber":"abcd1234",    # zewnętrzny ID / sygnatura, który nadaje sprzedający, dzięki któremu rozpozna przesyłkę w swoim systemie (część przewoźników nie korzysta z tego pola, w związku z czym informacja nie będzie widoczna na etykiecie)
                
                "packages": package
        }
    }

    resp = allegro_request("POST", url_1, vendor.name, headers=headers_post, json=payload)
    # print(' ***************************** create_shipment RESPONSE ***************************** ',resp, resp.text)
   
    return resp