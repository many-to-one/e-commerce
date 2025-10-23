from io import BytesIO
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from django.utils.timezone import localtime
import requests
from num2words import num2words

import os

# from staticfiles.backend import settings
from django.conf import settings

def generate_invoice_allegro(invoice, vendor, buyer_info, products): # tax_rate=23
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Dynamically resolve path
    font_path = os.path.join(settings.BASE_DIR, 'fonts', 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.wordWrap = 'CJK'
    normal_style.fontSize = 6
    normal_style.fontName = 'DejaVuSans'
    normal_style.encoding = 'utf-8'

    formatted_date = localtime(invoice.created_at).strftime('%Y-%m-%d')
    # year = localtime(invoice.created_at).year

    # Title
    c.setFont("DejaVuSans", 10)
    c.drawString(2 * cm, height - 2 * cm, "Faktura VAT")
    c.drawString(2 * cm, height - 2.5 * cm, f"nr: {invoice.invoice_number}")

    # Delivery info
    c.drawString(12 * cm, height - 2 * cm, f"Data wykonania usługi {invoice.created_at.strftime('%Y-%m-%d')}")
    c.drawString(12 * cm, height - 2.5 * cm, f"Wystawiona w dniu: {formatted_date}")

    # Seller info
    c.drawString(2 * cm, height - 4 * cm, "Sprzedawca:")
    c.drawString(2 * cm, height - 4.5 * cm, vendor.name)
    # c.drawString(2 * cm, height - 5 * cm, f"ul. {seller['street']} {seller['streetNumber']}, {seller['postalCode']} {seller['city']}")
    c.drawString(2 * cm, height - 5 * cm, vendor.address)
    c.drawString(2 * cm, height - 5.5 * cm, f"NIP {vendor.nip}")
    c.drawString(2 * cm, height - 6 * cm, f"Telefon {vendor.mobile}")
    c.drawString(2 * cm, height - 6.5 * cm, f"E-mail: {vendor.email}")

    # Buyer info
    c.drawString(12 * cm, height - 4 * cm, "Nabywca:")
    c.drawString(12 * cm, height - 4.5 * cm, buyer_info['name'])
    c.drawString(12 * cm, height - 5 * cm, f"ul. {buyer_info['street']}, {buyer_info['zipCode']} {buyer_info['city']}")
    c.drawString(12 * cm, height - 5.5 * cm, f"NIP {buyer_info['taxId']}")

    invoice.generated_at = formatted_date
    invoice.save()
    # c.drawString(2 * cm, height - 8 * cm, f"Data zakończenia dostawy/usługi: {formatted_date}")

    # Table setup
    data = [
        ["Lp.", "Nazwa towaru lub usługi", "Jm", "Ilość", "Cena netto", "Wartość netto", "VAT", "Kwota VAT", "Wartość brutto"]
    ]

    total_netto = total_vat = total_brutto = 0

    for i, product in enumerate(products, start=1):
        tax_rate = float(product.get('tax_rate'))
        name = Paragraph(product['offer']['name'], normal_style)
        quantity = product['quantity']
        price_brutto = float(product['price']['amount'])
        price_netto = price_brutto / (1 + tax_rate / 100)
        vat_value = price_brutto - price_netto
        value_netto = price_netto * quantity
        value_brutto = price_brutto * quantity
        value_vat = vat_value * quantity

        total_netto += value_netto
        total_vat += value_vat
        total_brutto += value_brutto

        data.append([
            str(i), name, "szt.", str(quantity),
            f"{price_netto:.2f} PLN", f"{value_netto:.2f} PLN",
            f"{tax_rate}%", f"{value_vat:.2f} PLN", f"{value_brutto:.2f} PLN"
        ])

    # Transport (if not Smart)
    delivery_cost = float(invoice.allegro_order.delivery_cost or 0)

    if delivery_cost > 0 and not invoice.allegro_order.is_smart:
        transport_brutto = delivery_cost
        transport_netto = transport_brutto / (1 + tax_rate / 100)
        transport_vat = transport_brutto - transport_netto

        total_netto += transport_netto
        total_vat += transport_vat
        total_brutto += transport_brutto

        data.append([
            str(len(data)), "Transport", "", "",
            f"{transport_netto:.2f} PLN", f"{transport_netto:.2f} PLN",
            f"{tax_rate}%", f"{transport_vat:.2f} PLN", f"{transport_brutto:.2f} PLN"
        ])



    data.append(["", "", "", "", "Razem:", f"{total_netto:.2f} PLN", "", f"{total_vat:.2f} PLN", f"{total_brutto:.2f} PLN"])

    table = Table(data, colWidths=[1 * cm, 6 * cm, 1 * cm, 1 * cm, 2 * cm, 2 * cm, 1.5 * cm, 2 * cm, 2 * cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    table.wrapOn(c, width, height)
    table.drawOn(c, 2 * cm, height - 16 * cm)

    # Total
    c.drawString(2 * cm, height - 17 * cm, f"Razem do zapłaty: {total_brutto:.2f} PLN")
    c.drawString(2 * cm, height - 17.5 * cm, f"Słownie złotych: ({num2words(total_brutto, lang='pl')} PLN)")

    # Signatures
    # c.drawString(2 * cm, height - 21 * cm, "_______________________________")
    # c.drawString(2 * cm, height - 21.5 * cm, "podpis osoby upoważnionej do odbioru faktury")

    # c.drawString(12 * cm, height - 21 * cm, "_______________________________")
    # c.drawString(12 * cm, height - 21.5 * cm, "podpis osoby upoważnionej")
    # c.drawString(12 * cm, height - 22 * cm, "do wystawienia faktury")

    c.save()
    pdf_content = buffer.getvalue()
    buffer.close()
    return pdf_content



def post_invoice_to_allegro(invoice, pdf_content, correction):
    """Post the generated invoice to Allegro API."""

    print('post_invoice_to_allegro invoice vendor ---------', correction)

    if correction:
        invoice = invoice.main_invoice
    access_token = invoice.vendor.access_token
    order_id = invoice.allegro_order.order_id
    url = f"https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms/{order_id}/invoices"

    payload = {
        "file": {
            "name": f"invoice_{invoice.invoice_number}.pdf"
        },
        "invoiceNumber": invoice.invoice_number
    }

    headers = {
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json',
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 201:
        invoice_id = response.json().get("id")
        add_invoice_to_order(invoice_id, invoice, order_id, access_token, pdf_content, correction)
        print(f"Invoice {invoice.invoice_number} posted successfully to Allegro.")
    else:
        print(f"Failed to post invoice {invoice.invoice_number} to Allegro: {response.text}")

def add_invoice_to_order(invoice_id, invoice, order_id, access_token, pdf_content, correction):
    url = f"https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms/{order_id}/invoices/{invoice_id}/file"

    headers = {
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.put(url, headers=headers, data=pdf_content)
    print(f"--add_invoice_to_order--PUT---- {response, response.text}.")
    if response.status_code == 200:
        if correction:
            invoice = invoice.main_invoice.sent_to_buyer = True
        else:
            invoice.sent_to_buyer = True
            invoice.save()
            print(f"Invoice {invoice_id} added successfully to order {order_id}.")
    else:
        print(f"Failed to add invoice {invoice_id} to order {order_id}: {response.text}")




def generate_correction_invoice_allegro(invoice, buyer_info, products, _main_invoice_products):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Czcionka
    font_path = os.path.join(settings.BASE_DIR, 'fonts', 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.wordWrap = 'CJK'
    normal_style.fontSize = 6
    normal_style.fontName = 'DejaVuSans'

    formatted_date = localtime(invoice.created_at).strftime('%Y-%m-%d')

    # --- Nagłówek ---
    c.setFont("DejaVuSans", 10)
    c.drawString(2 * cm, height - 2 * cm, f"Faktura VAT – korygująca nr: {invoice.invoice_number}")
    c.drawString(2 * cm, height - 2.7 * cm, f"Data wystawienia: {formatted_date}")
    c.drawString(2 * cm, height - 4 * cm, f"Dotyczy faktury nr: {invoice.main_invoice.invoice_number}")
    c.drawString(2 * cm, height - 4.7 * cm, f"Wystawionej w dniu: {invoice.main_invoice.generated_at}")

    # --- Dane sprzedawcy i nabywcy ---
    c.setFont("DejaVuSans", 9)
    c.drawString(2 * cm, height - 6 * cm, "Sprzedawca:")
    c.drawString(2 * cm, height - 6.5 * cm, invoice.main_invoice.vendor.name)
    c.drawString(2 * cm, height - 7 * cm, invoice.main_invoice.vendor.address)
    c.drawString(2 * cm, height - 7.5 * cm, f"NIP {invoice.main_invoice.vendor.nip}")

    c.drawString(12 * cm, height - 6 * cm, "Nabywca:")
    c.drawString(12 * cm, height - 6.5 * cm, buyer_info['name'])
    c.drawString(12 * cm, height - 7 * cm, f"ul. {buyer_info['street']}, {buyer_info['zipCode']} {buyer_info['city']}")
    c.drawString(12 * cm, height - 7.5 * cm, f"NIP {buyer_info['taxId']}")

    # --- Tabela: Dane przed korektą ---
    c.drawString(2 * cm, height - 11 * cm, "Dane przed korektą:")
    table_before = build_products_table(_main_invoice_products, normal_style, invoice.main_invoice.allegro_order)
    table_before.wrapOn(c, width, height)
    table_before.drawOn(c, 2 * cm, height - 16 * cm)

    # --- Tabela: Dane po korekcie ---
    c.drawString(2 * cm, height - 20 * cm, "Dane po korekcie:")
    table_after = build_products_table(products, normal_style, invoice.main_invoice.allegro_order)
    table_after.wrapOn(c, width, height)
    table_after.drawOn(c, 2 * cm, height - 26 * cm)

    c.save()
    pdf_content = buffer.getvalue()
    buffer.close()
    return pdf_content

def build_products_table(products, normal_style, allegro_order, tax_rate_default=23):
    data = [["Lp.", "Nazwa", "Jm", "Ilość", "Cena netto", "Wartość netto", "VAT", "Kwota VAT", "Wartość brutto"]]
    total_netto = total_vat = total_brutto = 0

    # Flaga: czy transport już jest w products
    has_transport = any(
        (p.get("offer_name") or p.get("offer", {}).get("name")) == "Transport"
        for p in products
    )

    for i, product in enumerate(products, start=1):
        tax_rate = float(product.get('tax_rate', tax_rate_default))
        name = Paragraph(product.get('offer', {}).get('name', product.get('offer_name')), normal_style)
        quantity = int(product['quantity'])
        price_brutto = float(product.get('price', {}).get('amount', product.get('price_amount')))
        price_netto = price_brutto / (1 + tax_rate / 100)
        vat_value = price_brutto - price_netto
        value_netto = price_netto * quantity
        value_brutto = price_brutto * quantity
        value_vat = vat_value * quantity

        total_netto += value_netto
        total_vat += value_vat
        total_brutto += value_brutto

        data.append([
            str(i), name, "szt.", str(quantity),
            f"{price_netto:.2f} PLN", f"{value_netto:.2f} PLN",
            f"{tax_rate}%", f"{value_vat:.2f} PLN", f"{value_brutto:.2f} PLN"
        ])

    # Transport dodajemy tylko jeśli nie ma go w products
    if not has_transport:
        delivery_cost = float(allegro_order.delivery_cost or 0)
        if delivery_cost > 0 and not allegro_order.is_smart:
            transport_brutto = delivery_cost
            transport_netto = transport_brutto / (1 + tax_rate / 100)
            transport_vat = transport_brutto - transport_netto
            total_netto += transport_netto
            total_vat += transport_vat
            total_brutto += transport_brutto
            data.append([
                str(len(data)), "Transport", "", "1",
                f"{transport_netto:.2f} PLN", f"{transport_netto:.2f} PLN",
                f"{tax_rate}%", f"{transport_vat:.2f} PLN", f"{transport_brutto:.2f} PLN"
            ])

    # Podsumowanie
    data.append(["", "", "", "", "Razem:", f"{total_netto:.2f} PLN", "", f"{total_vat:.2f} PLN", f"{total_brutto:.2f} PLN"])

    table = Table(data, colWidths=[1*cm, 6*cm, 1*cm, 1*cm, 2*cm, 2*cm, 1.5*cm, 2*cm, 2*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    return table

