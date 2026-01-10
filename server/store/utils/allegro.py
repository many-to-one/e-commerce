from decimal import Decimal
from store.allegro_views.views import allegro_request, generate_pid
from store.models import Category, Product

import os


def extract_full_description(offer_json):
    html_parts = []

    try:
        sections = offer_json.get("description", {}).get("sections", [])

        for section in sections:
            items = section.get("items", [])
            for item in items:

                # TEXT → gotowy HTML
                if item.get("type") == "TEXT":
                    html_parts.append(item.get("content", ""))

                # IMAGE → budujemy <img>
                elif item.get("type") == "IMAGE":
                    url = item.get("url")
                    if url:
                        html_parts.append(
                            f'<p><img src="{url}" style="max-width:100%;height:auto;" /></p>'
                        )

    except Exception:
        pass

    return "\n".join(html_parts).strip()


def extract_ean_and_html_description(offer_json):
    ean = None
    html_parts = []

    # --- EAN ---
    try:
        params = offer_json["productSet"][0]["product"]["parameters"]
        for p in params:
            if p.get("id") == "225693" or p.get("name") == "EAN (GTIN)":
                values = p.get("values")
                if values:
                    ean = values[0]
                break
    except Exception:
        pass

    # --- DESCRIPTION (HTML + IMAGES) ---
    try:
        sections = offer_json.get("description", {}).get("sections", [])

        for section in sections:
            items = section.get("items", [])
            for item in items:

                # TEXT → gotowy HTML
                if item.get("type") == "TEXT":
                    html_parts.append(item.get("content", ""))

                # IMAGE → budujemy <img>
                elif item.get("type") == "IMAGE":
                    url = item.get("url")
                    if url:
                        html_parts.append(
                            f'<p><img src="{url}" style="max-width:100%;height:auto;" /></p>'
                        )

    except Exception:
        pass

    html_description = "\n".join(html_parts).strip()

    return ean, html_description



def get_ean(product_id, vendor_name, headers):

    url = f"https://{os.getenv("ALLEGRO_API_URL")}/sale/product-offers/{product_id}"
    response = allegro_request("GET", url, vendor_name, headers=headers)
    print("_________EAN RESPONSE___________", response, response.json())
    return response.json()


def fetch_all_offers(vendor_name, headers):

    statuses = ["ACTIVE", "INACTIVE", "ENDED", "ACTIVATING", "NOT_LISTED"]
    all_offers = []

    for status in statuses:
        offset = 0
        while True:
            url = (
                f"https://{os.getenv("ALLEGRO_API_URL")}/sale/offers"
                f"?limit=100&offset={offset}"
                f"&publication.marketplace=allegro-pl"
                f"&publication.status={status}"
            )
            response = allegro_request("GET", url, vendor_name, headers=headers)
            data = response.json()
            # print("_________OFFER_________", data)

            offers = data.get("offers", [])
            if not offers:
                break

            all_offers.extend(offers)
            offset += 100

            total_count = data.get("totalCount")
            if total_count and offset >= total_count:
                break
            
    # for offer in all_offers:
    #     print("_________OFFER_________", offer)
        # print(f' ################### "offer id & status" ################### ', offer.get("id"), offer.get("publication", {}).get("status"))

    return all_offers



def create_product_from_allegro(offer, vendor, ean, html_description):

    sku = offer.get("external", {}).get("id")
    if not sku:
        return None

    price_brutto = Decimal(str(offer["sellingMode"]["price"]["amount"]))
    price_netto = (price_brutto / Decimal("1.23")).quantize(Decimal("0.01"))

    product = Product.objects.create(
        sku=sku,
        title=offer.get("name", "Produkt Allegro"),
        ean=ean,
        description=html_description,
        price_brutto=price_brutto,
        price=price_netto,
        stock_qty=offer.get("stock", {}).get("available", 0),
        allegro_status=offer.get("publication", {}).get("status"),
        allegro_in_stock=offer.get("publication", {}).get("status") == "ACTIVE",
        allegro_started_at=offer.get("publication", {}).get("startedAt"),
        allegro_ended_at=offer.get("publication", {}).get("endedAt"),
        allegro_watchers=offer.get("stats", {}).get("watchersCount", 0),
        allegro_visits=offer.get("stats", {}).get("visitsCount", 0),
    )

    # --- zachowaj vendorów z mojastrona.pl ---
    local_vendors = product.vendors.filter(marketplace=os.getenv("_marketplace"))

    # --- ustaw aktualnego vendora Allegro + lokalnych vendorów ---
    product.vendors.set([vendor, *local_vendors])

    # kategoria
    cat_id = offer.get("category", {}).get("id")
    if cat_id:
        try:
            category = Category.objects.get(allegro_cat_id=cat_id)
            product.category = category
        except Category.DoesNotExist:
            pass

    # zdjęcia
    img = offer.get("primaryImage", {}).get("url")
    if img:
        product.img_links = [img]

    product.save()
    return product


def clone_product_with_new_allegro_id(product, new_allegro_id, vendor, ean, html_description):
    # skopiuj bazowy produkt
    original_pk = product.pk
    original_vendors = list(product.vendors.all())

    product.pk = None  # nowy rekord
    product.allegro_id = new_allegro_id
    if product.ean is None or product.ean == "(None,)":
        product.ean=ean
    if product.description is None or product.description == "(None,)":
        product.description=html_description

    # nowy pid i unikalny slug
    product.pid = generate_pid()
    if product.slug:
        product.slug = f"{product.slug}-{new_allegro_id}"

    # wyczyść pola allegro (zaraz i tak nadpiszesz syncem)
    product.allegro_status = None
    product.allegro_in_stock = False
    product.allegro_watchers = 0
    product.allegro_visits = 0
    product.allegro_started_at = None
    product.allegro_ended_at = None

    product.save()

    # --- zachowaj vendorów z mojastrona.pl ---
    local_vendors = product.vendors.filter(marketplace=os.getenv("_marketplace"))

    # --- ustaw aktualnego vendora Allegro + lokalnych vendorów ---
    product.vendors.set([vendor, *local_vendors])

    return product