from decimal import Decimal
from store.allegro_views.views import allegro_request, generate_pid
from store.models import Category, Product

import os


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

            offers = data.get("offers", [])
            if not offers:
                break

            all_offers.extend(offers)
            offset += 100

            total_count = data.get("totalCount")
            if total_count and offset >= total_count:
                break
            
    for offer in all_offers:
        print(f' ################### "offer id & status" ################### ', offer.get("id"), offer.get("publication", {}).get("status"))

    return all_offers



def create_product_from_allegro(offer, vendor):

    sku = offer.get("external", {}).get("id")
    if not sku:
        return None

    price_brutto = Decimal(str(offer["sellingMode"]["price"]["amount"]))
    price_netto = (price_brutto / Decimal("1.23")).quantize(Decimal("0.01"))

    product = Product.objects.create(
        sku=sku,
        title=offer.get("name", "Produkt Allegro"),
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
    local_vendors = product.vendors.filter(marketplace="mojastrona.pl")

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


def clone_product_with_new_allegro_id(product, new_allegro_id, vendor):
    # skopiuj bazowy produkt
    original_pk = product.pk
    original_vendors = list(product.vendors.all())

    product.pk = None  # nowy rekord
    product.allegro_id = new_allegro_id

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
    local_vendors = product.vendors.filter(marketplace=os.get("_marketplace"))

    # --- ustaw aktualnego vendora Allegro + lokalnych vendorów ---
    product.vendors.set([vendor, *local_vendors])

    return product