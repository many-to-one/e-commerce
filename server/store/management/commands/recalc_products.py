from decimal import Decimal, ROUND_HALF_UP
from django.core.management.base import BaseCommand
from store.models import Product

class Command(BaseCommand):
    help = "Przelicza price_brutto, zysk_pln i zysk_procent dla wszystkich produktów"

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

            # zapis do pól
            p.price_brutto = cena_brutto
            p.zysk_pln = zysk_pln
            p.zysk_procent = zysk_percent
            p.save(update_fields=["price_brutto", "zysk_pln", "zysk_procent"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Przeliczono {updated} produktów."))
