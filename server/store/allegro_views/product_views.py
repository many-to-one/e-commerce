import json
import os
import requests
from bs4 import BeautifulSoup

from .views import allegro_request

ALLEGRO_API_URL = os.getenv("ALLEGRO_API_URL")


def action_with_offer_from_product(request, method, product, url, access_token, vendor_name, producer, action=None):

        # print('create_offer_from_product producer ----------------', producer["responsibleProducers"][0]['id'])
        # print('self.build_images(product.img_links) ----------------', self.build_images(product.img_links))
        print('create_offer_from_product action ----------------', action)

        raw_html = product.description # your original HTML content
        safe_html = ''
        if raw_html is not None:
            safe_html = sanitize_allegro_description(raw_html)
        else:
            safe_html = product.text_description

        try:

            if method == "PATCH":
                if action == "stock_qty":
                    payload = json.dumps({
                        "stock": {
                            "available": product.stock_qty
                        }
                    })
                elif action == "price_brutto":
                    payload = json.dumps({
                        "sellingMode": {
                            "price": {
                            "amount": str(product.price_brutto),
                            "currency": "PLN"
                            }
                        }
                    })
                elif action == "title":
                     payload = json.dumps({
                        "name": f"{product.title}",
                    })
                elif action == "activate":
                    payload = json.dumps({
                        "publication": {
                            "status": "ACTIVE", 
                        },
                    })
                elif action == "deactivate":
                    payload = json.dumps({
                        "publication": {
                            "status": "INACTIVE", 
                        },
                    })
                elif action == "delivery":
                    payload = json.dumps({
                        'delivery': {
                            'shippingRates': {
                                'name': "Paczkomat 1szt" #'Paczkomat 1szt'
                            }
                        }
                    })
                else:
                    payload = json.dumps({
                        "name": f"{product.title}",
                        "external": {
                            "id": f"{product.sku}" 
                        },
                        "productSet": [
                            {
                            "product": {
                                "id": f"{product.ean}", #product.ean,
                                "idType": "GTIN"
                            },
                            # "responsibleProducer": {
                            #     "type": "ID",
                            #     "id": producer["responsibleProducers"][0]['id']
                            # },
                            },
                        ],
                        "sellingMode": {
                            "price": {
                            "amount": str(product.price_brutto),
                            "currency": "PLN"
                            }
                        },
                        "stock": {
                            "available": product.stock_qty
                        },
                        # "publication": {
                        #     "status": "ACTIVE", 
                        # },
                        # 'delivery': {
                        #     'shippingRates': {
                        #         'name': 'Paczkomat 1szt'
                        #     }
                        # },
                        "description": {
                                "sections": [
                                    {
                                        "items": [
                                            {
                                                "type": "TEXT", 
                                                    "content": f"<p>{product.text_description}</p>" if safe_html == "" or safe_html is None else safe_html
                                            }
                                        ]
                                    }
                                ]
                            },  
                                   
                        "images": build_images(product.img_links, vendor_name) if product.img_links is not None else None
                    })

            else:   
                payload = json.dumps({
                    "name": f"{product.title}",
                    "external": {
                        "id": f"{product.sku}" 
                    },
                    "productSet": [
                        {
                        "product": {
                            "id": f"{product.ean}", #product.ean,
                            "idType": "GTIN"
                        },
                        "responsibleProducer": {
                            "type": "ID",
                            "id": producer["responsibleProducers"][0]['id']
                        },
                        },
                    ],
                    "sellingMode": {
                        "price": {
                        "amount": str(product.price_brutto),
                        "currency": "PLN"
                        }
                    },
                    "stock": {
                        "available": product.stock_qty
                    },
                    'delivery': {
                        'shippingRates': {
                            'name': "Paczkomat 1szt" #'Paczkomat 1szt'
                        }
                    },
                    "description": {
                        "sections": [
                            {
                                "items": [
                                    {
                                        "type": "TEXT",
                                        "content": safe_html if safe_html != "" or safe_html is not None else product.text_description
                                    }
                                ]
                            }
                        ]
                    },
                    "images": build_images(product.img_links, vendor_name)
                })

            headers = {
                'Accept': 'application/vnd.allegro.public.v1+json',
                'Content-Type': 'application/vnd.allegro.public.v1+json',
                'Accept-Language': 'pl-PL',
                'Authorization': f'Bearer {access_token}'
            }

            # response = requests.request("POST", url, headers=headers, data=payload)
            response = allegro_request(method, url, vendor_name, headers=headers, data=payload)
            print(f'create_offer_from_product {method} response ----------------', response)
            print(f'create_offer_from_product {method} response text ----------------', response.text)
            actions = {
                'price_brutto': 'cenę',
                'stock_qty': 'stan magazynowy',
                'title': 'tytuł',
                'description': 'opis',
                'activate': 'aktywowanie',
                'deactivate': 'dezaktywowanie',
                'delivery': 'metodę dostawy',
                'other': 'ofertę',
            }
            if response.status_code == 200:
                product.updates = False
                product.save(update_fields=['updates'])
                # self.message_user(request, f"✅ Zmieniłęs {actions[action]} w {product.sku} allegro dla {vendor_name}", level='success')
            if response.status_code == 202:
                product.allegro_in_stock = True
                # self.message_user(request, f"✅ Wystawiłeś ofertę {product.sku} allegro dla {vendor_name}", level='success')
            # elif response.status_code == 401:
                # self.message_user(request, f"⚠️ Nie jesteś załogowany {vendor_name}", level='error')
            # elif response.status_code == 422:
                # self.message_user(request, f"EAN:{product.ean}; SKU: {product.sku} - {response.status_code} - {response.text} dla {vendor_name}", level='error')
            return response
        except requests.exceptions.HTTPError as err:
            # self.message_user(request, f"⚠️ EAN:{product.ean}; SKU: {product.sku} - {err} dla {vendor_name}", level='error')
            raise SystemExit(err)
        

def upload_image(url, vendor_name):
    """
    Wysyła pojedynczy URL do Allegro i zwraca link z domeny a.allegroimg.pl
    """
    _url = f"https://{ALLEGRO_API_URL}/sale/images"

    headers = {
        "Accept": "application/vnd.allegro.public.v1+json",
        "Content-Type": "application/vnd.allegro.public.v1+json",
    }

    payload = {"url": url}

    # ważne: używaj json=payload zamiast data=payload
    response = allegro_request("POST", _url, vendor_name, headers=headers, json=payload)
    data = response.json()
    print('data ----------------', data)

    # Allegro zwraca {"location": "..."}
    # return {"url": data["location"]}
    return data["location"]


def build_images(img_links, vendor_name):
    """
    Wysyła wszystkie linki z img_links do Allegro i zwraca listę obiektów { "url": ... }
    """
    uploaded = []
    for link in img_links:
        uploaded.append(upload_image(link, vendor_name))
    print('uploaded ----------------', uploaded)
    return uploaded


def sanitize_allegro_description(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # usuń wszystkie style, klasy, atrybuty
    for tag in soup.find_all(True):
        tag.attrs = {}

    # usuń <div> (rozpakuj zawartość)
    for div in soup.find_all("div"):
        div.unwrap()

    # zamień <h1>/<h2> na <h2> (bez styli)
    for h in soup.find_all(["h1", "h2"]):
        new_h = soup.new_tag("h2")
        new_h.string = "⭐ " + h.get_text(strip=True)
        h.replace_with(new_h)

    # zamień <table> na <ul><li>
    for table in soup.find_all("table"):
        ul = soup.new_tag("ul")
        for td in table.find_all("td"):
            text = td.get_text(strip=True)
            if text:
                li = soup.new_tag("li")
                li.string = f"➡️ {text}"
                ul.append(li)
        table.replace_with(ul)

    # usuń wszystkie <img>
    for img in soup.find_all("img"):
        img.decompose()


    # usuń wszystkie <br>
    for br in soup.find_all("br"):
        br.decompose()

    # zamień <b> na <h2> (bo <b> nie jest dozwolone)
    for b in soup.find_all("b"):
        new_h = soup.new_tag("h2")
        new_h.string = b.get_text(strip=True)
        b.replace_with(new_h)

    # zamień <span> na <p>
    for span in soup.find_all("span"):
        new_p = soup.new_tag("p")
        new_p.string = span.get_text(strip=True)
        span.replace_with(new_p)

    return str(soup)