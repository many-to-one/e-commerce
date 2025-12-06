# from decimal import Decimal, ROUND_HALF_UP
# from django.core.management.base import BaseCommand
# from store.models import Product

# class Command(BaseCommand):
#     help = "Przelicza price_brutto, zysk_pln i zysk_procent dla wszystkich produktów"

#     def handle(self, *args, **options):
#         vat_rate = Decimal("23")  # jeśli masz różne stawki, pobierz z obj.tax_rate

#         updated = 0
#         for p in Product.objects.all():
#             if p.price is None or p.hurt_price is None:
#                 continue

#             vat_multiplier = Decimal("1") + vat_rate / Decimal("100")

#             # cena brutto = cena netto * (1 + VAT)
#             cena_brutto = (p.price * vat_multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

#             # zysk PLN = cena brutto - hurt_price
#             zysk_pln = (cena_brutto - p.hurt_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

#             # zysk % = (zysk_pln / hurt_price) * 100
#             if p.hurt_price > 0:
#                 zysk_percent = (zysk_pln / p.hurt_price * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
#             else:
#                 zysk_percent = None

#             # zapis do pól
#             p.price_brutto = cena_brutto
#             p.zysk_pln = zysk_pln
#             p.zysk_procent = zysk_percent
#             p.save(update_fields=["price_brutto", "zysk_pln", "zysk_procent"])
#             updated += 1

#         self.stdout.write(self.style.SUCCESS(f"Przeliczono {updated} produktów."))



from decimal import Decimal, ROUND_HALF_UP
from django.core.management.base import BaseCommand
from store.models import Product

def calculate_delivery_cost(cena_brutto: Decimal, przesylki: int = 1) -> Decimal:
    """
    Oblicza koszt dostawy na podstawie ceny brutto i liczby przesyłek.
    """
    if cena_brutto < Decimal("30"):
        return Decimal("0.00")  # poniżej 30 zł np. brak obsługi
    elif cena_brutto <= Decimal("44.99"):
        return Decimal("1.59") * przesylki
    elif cena_brutto <= Decimal("64.99"):
        return Decimal("3.09") * przesylki
    elif cena_brutto <= Decimal("99.99"):
        return Decimal("4.99") * przesylki
    elif cena_brutto <= Decimal("149.99"):
        return Decimal("7.59") * przesylki
    else:
        # od 150 zł: pierwsza przesyłka 9.99, kolejne 7.59
        if przesylki == 1:
            return Decimal("9.99")
        else:
            return Decimal("9.99") + Decimal("7.59") * (przesylki - 1)


class Command(BaseCommand):
    help = "Przelicza price_brutto, zysk_pln, zysk_procent i zysk_after_payments dla wszystkich produktów"

    def handle(self, *args, **options):
        vat_rate = Decimal("23")  # jeśli masz różne stawki, pobierz z obj.tax_rate

        updated = 0
        for p in Product.objects.all():
            if p.price is None or p.hurt_price is None:
                continue

            vat_multiplier = Decimal("1") + vat_rate / Decimal("100")

            # cena brutto = cena netto * (1 + VAT)
            cena_brutto = (p.price * vat_multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # zysk PLN = cena brutto - hurt_price
            zysk_pln = (cena_brutto - p.hurt_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # zysk % = (zysk_pln / hurt_price) * 100
            if p.hurt_price > 0:
                zysk_percent = (zysk_pln / p.hurt_price * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                zysk_percent = None

            # --- Nowa logika: zysk po odjęciu 3% i kosztów dostawy ---
            cena_po_prowizji = (cena_brutto * Decimal("0.97")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            delivery_cost = calculate_delivery_cost(cena_po_prowizji, przesylki=1)
            zysk_after_payments = (cena_po_prowizji - p.hurt_price - delivery_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # zapis do pól
            p.price_brutto = cena_brutto
            p.zysk_pln = zysk_pln
            p.zysk_procent = zysk_percent
            p.zysk_after_payments = zysk_after_payments
            p.save(update_fields=["price_brutto", "zysk_pln", "zysk_procent", "zysk_after_payments"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Przeliczono {updated} produktów."))
