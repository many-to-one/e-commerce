from datetime import datetime
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

from store.allegro_views.views import allegro_request

ALLEGRO_API_URL = os.getenv("ALLEGRO_API_URL")

def invoice_upload_path(instance, filename):
        # Pobierz aktualną datę
        now = datetime.now()
        # Zbuduj ścieżkę: invoices/rok/miesiąc/nazwa_pliku.pdf
        return os.path.join(
            "invoices",
            str(now.year),
            str(now.month).zfill(2),  # np. "01", "02"
            filename
        )

# def generate_invoice_allegro(invoice, vendor, buyer_info, products): # tax_rate=23
#     buffer = BytesIO()
#     c = canvas.Canvas(buffer, pagesize=A4)
#     width, height = A4

#     # Dynamically resolve path
#     font_path = os.path.join(settings.BASE_DIR, 'fonts', 'DejaVuSans.ttf')
#     pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

#     styles = getSampleStyleSheet()
#     normal_style = styles['Normal']
#     normal_style.wordWrap = 'CJK'
#     normal_style.fontSize = 6
#     normal_style.fontName = 'DejaVuSans'
#     normal_style.encoding = 'utf-8'

#     allegro_order_occurred = localtime(invoice.allegro_order.occurred_at).strftime('%d-%m-%Y')
#     # year = localtime(invoice.created_at).year

#     formatted_generated = localtime(invoice.created_at).strftime('%d-%m-%Y')

#     # Title
#     c.setFont("DejaVuSans", 10)
#     c.drawString(2 * cm, height - 2 * cm, "Faktura VAT")
#     c.drawString(2 * cm, height - 2.5 * cm, f"nr: {invoice.invoice_number}")

#     # Delivery info
#     c.drawString(12 * cm, height - 2 * cm, f"Data wykonania usługi {allegro_order_occurred}")
#     c.drawString(12 * cm, height - 2.5 * cm, f"Wystawiona w dniu: {formatted_generated}")

#     # Seller info
#     c.drawString(2 * cm, height - 4 * cm, "Sprzedawca:")
#     c.drawString(2 * cm, height - 4.5 * cm, vendor.name)
#     # c.drawString(2 * cm, height - 5 * cm, f"ul. {seller['street']} {seller['streetNumber']}, {seller['postalCode']} {seller['city']}")
#     c.drawString(2 * cm, height - 5 * cm, vendor.address)
#     c.drawString(2 * cm, height - 5.5 * cm, f"NIP {vendor.nip}")
#     c.drawString(2 * cm, height - 6 * cm, f"Telefon {vendor.mobile}")
#     c.drawString(2 * cm, height - 6.5 * cm, f"E-mail: {vendor.email}")

#     # Buyer info
#     c.drawString(12 * cm, height - 4 * cm, "Nabywca:")
#     c.drawString(12 * cm, height - 4.5 * cm, buyer_info['name'])
#     c.drawString(12 * cm, height - 5 * cm, f"ul. {buyer_info['street']}, {buyer_info['zipCode']} {buyer_info['city']}")
#     c.drawString(12 * cm, height - 5.5 * cm, f"NIP {buyer_info['taxId']}")

#     # Table setup
#     data = [
#         ["Lp.", "Nazwa towaru lub usługi", "Jm", "Ilość", "Cena netto", "Wartość netto", "VAT", "Kwota VAT", "Wartość brutto"]
#     ]

#     total_netto = total_vat = total_brutto = 0

#     for i, product in enumerate(products, start=1):
#         tax_rate = float(product.get('tax_rate') or 0)
#         name = Paragraph(product.get('offer', {}).get('name') or "", normal_style)
#         quantity = int(product.get('quantity') or 0)
#         price_brutto = float(product.get('price', {}).get('amount') or 0)
#         # currency = str(product.get('price', {}).get('currency') or "PLN")
#         price_netto = price_brutto / (1 + tax_rate / 100)
#         vat_value = price_brutto - price_netto
#         value_netto = price_netto * quantity
#         value_brutto = price_brutto * quantity
#         value_vat = vat_value * quantity

#         total_netto += value_netto
#         total_vat += value_vat
#         total_brutto += value_brutto

#         data.append([
#             str(i), name, "szt.", str(quantity),
#             f"{price_netto:.2f} PLN", f"{value_netto:.2f} PLN",
#             f"{tax_rate}%", f"{value_vat:.2f} PLN", f"{value_brutto:.2f} PLN"
#         ])

#     # Transport (if not Smart)
#     delivery_cost = float(invoice.allegro_order.delivery_cost or 0)

#     if delivery_cost > 0 and not invoice.allegro_order.is_smart:
#         transport_brutto = delivery_cost
#         transport_netto = transport_brutto / (1 + tax_rate / 100)
#         transport_vat = transport_brutto - transport_netto

#         total_netto += transport_netto
#         total_vat += transport_vat
#         total_brutto += transport_brutto

#         data.append([
#             str(len(data)), "Transport", "", "",
#             f"{transport_netto:.2f} PLN", f"{transport_netto:.2f} PLN",
#             f"{tax_rate}%", f"{transport_vat:.2f} PLN", f"{transport_brutto:.2f} PLN"
#         ])



#     data.append(["", "", "", "", "Razem:", f"{total_netto:.2f} PLN", "", f"{total_vat:.2f} PLN", f"{total_brutto:.2f} PLN"])

#     table = Table(data, colWidths=[1 * cm, 6 * cm, 1 * cm, 1 * cm, 2 * cm, 2 * cm, 1.5 * cm, 2 * cm, 2 * cm])
#     table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans'),
#         ('FONTSIZE', (0, 0), (-1, -1), 6),
#         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),
#     ]))

#     table.wrapOn(c, width, height)
#     table.drawOn(c, 2 * cm, height - 16 * cm)

#     # Total
#     c.drawString(2 * cm, height - 17 * cm, f"Razem do zapłaty: {total_brutto:.2f} PLN")
#     c.drawString(2 * cm, height - 17.5 * cm, f"Słownie złotych: ({num2words(total_brutto, lang='pl')} PLN)")

#     # Signatures
#     # c.drawString(2 * cm, height - 21 * cm, "_______________________________")
#     # c.drawString(2 * cm, height - 21.5 * cm, "podpis osoby upoważnionej do odbioru faktury")

#     # c.drawString(12 * cm, height - 21 * cm, "_______________________________")
#     # c.drawString(12 * cm, height - 21.5 * cm, "podpis osoby upoważnionej")
#     # c.drawString(12 * cm, height - 22 * cm, "do wystawienia faktury")

#     c.save()
#     pdf_content = buffer.getvalue()
#     buffer.close()
#     return pdf_content







def generate_invoice_allegro(invoice, vendor, user, buyer_info, products):  # tax_rate optional

    # print(' VENDOR ----------------------- ', vendor)
    # print(' USER ----------------------- ', user)
    # print(' VENDOR NIP ----------------------- ', vendor.nip)
    # print(' USERNAME ----------------------- ', user.full_name)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Register font
    font_path = os.path.join(settings.BASE_DIR, 'fonts', 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.wordWrap = 'CJK'
    normal_style.fontSize = 6
    normal_style.fontName = 'DejaVuSans'
    normal_style.encoding = 'utf-8'

    # Dates
    allegro_order_occurred = localtime(invoice.allegro_order.occurred_at).strftime('%d-%m-%Y') if getattr(invoice.allegro_order, 'occurred_at', None) else ''
    formatted_generated = localtime(invoice.created_at).strftime('%d-%m-%Y') if getattr(invoice, 'created_at', None) else ''

    # Title
    c.setFont("DejaVuSans", 10)
    c.drawString(2 * cm, height - 2 * cm, "Faktura VAT")
    c.drawString(2 * cm, height - 2.5 * cm, f"nr: {getattr(invoice, 'invoice_number', '')}")

    # Delivery info
    c.drawString(12 * cm, height - 2 * cm, f"Data wykonania usługi {allegro_order_occurred}")
    c.drawString(12 * cm, height - 2.5 * cm, f"Wystawiona w dniu: {formatted_generated}")

    from reportlab.lib.utils import simpleSplit

    # Seller info
    c.drawString(2 * cm, height - 4 * cm, "Sprzedawca:")
    c.drawString(2 * cm, height - 4.5 * cm, str(user.full_name or ""))
    c.drawString(2 * cm, height - 5 * cm, f"{str(vendor.address or "")}" ) # Adres:
    c.drawString(2 * cm, height - 5.5 * cm, f"NIP: {str(vendor.nip or "")}" )
    c.drawString(2 * cm, height - 6 * cm, f"Telefon: {str(user.phone or "")}" )
    c.drawString(2 * cm, height - 6.5 * cm, f"E-mail: {str(getattr(vendor, 'email', '') or '')}")

    # Buyer 
    buyer_name = str(buyer_info.get('name') or "")
    wrapped = simpleSplit(buyer_name, c._fontname, c._fontsize, 7*cm) # szerokość pola


    y = height - 4.5 * cm
    for line in wrapped:
        c.drawString(12 * cm, y, line)
        y -= 0.5 * cm  # odstęp między liniami
    c.drawString(12 * cm, height - 4 * cm, "Nabywca:")
    # c.drawString(12 * cm, height - 4.5 * cm, str(buyer_info.get('name') or ""))
    c.drawString(12 * cm, height - 4.5 * cm, buyer_name)
    c.drawString(12 * cm, height - 5 * cm, f"ul. {buyer_info.get('street','')} {buyer_info.get('zipCode','')} {buyer_info.get('city','')}")
    c.drawString(12 * cm, height - 5.5 * cm, f"NIP {buyer_info.get('taxId','')}")

    # Table setup
    data = [["Lp.", "Nazwa towaru lub usługi", "Jm", "Ilość", "Cena netto", "Wartość netto", "VAT", "Kwota VAT", "Wartość brutto"]]
    total_netto = total_vat = total_brutto = 0

    for i, product in enumerate(products, start=1):
        tax_rate = float(product.get('tax_rate') or 0)
        name_str = str(product.get('offer', {}).get('name') or "")
        name = Paragraph(name_str, normal_style)
        quantity = int(product.get('quantity') or 0)
        price_brutto = float(product.get('price', {}).get('amount') or 0)

        price_netto = price_brutto / (1 + tax_rate / 100) if tax_rate else price_brutto
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
    delivery_cost = float(getattr(invoice.allegro_order, 'delivery_cost', 0) or 0)
    transport_tax_rate = float(getattr(invoice.allegro_order, 'tax_rate', 0) or 0)  # fallback

    # print(' ################################## delivery_cost ################################## ', delivery_cost)

    # if delivery_cost > 0 and not getattr(invoice.allegro_order, 'is_smart', False):
    if delivery_cost > 0:
        # print(' ################################## delivery_cost > 0 ################################## ', delivery_cost)
        transport_brutto = delivery_cost
        transport_netto = transport_brutto / (1 + transport_tax_rate / 100) if transport_tax_rate else transport_brutto
        transport_vat = transport_brutto - transport_netto

        total_netto += transport_netto
        total_vat += transport_vat
        total_brutto += transport_brutto

        data.append([
            str(len(data)), "Transport", "", "",
            f"{transport_netto:.2f} PLN", f"{transport_netto:.2f} PLN",
            f"{transport_tax_rate}%", f"{transport_vat:.2f} PLN", f"{transport_brutto:.2f} PLN"
        ])


    # Totals row
    data.append(["", "", "", "", "Razem:", f"{total_netto:.2f} PLN", "", f"{total_vat:.2f} PLN", f"{total_brutto:.2f} PLN"])

    table = Table(data, colWidths=[1*cm,6*cm,1*cm,1*cm,2*cm,2*cm,1.5*cm,2*cm,2*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'DejaVuSans'),
        ('FONTSIZE', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))

    table.wrapOn(c, width, height)
    table.drawOn(c, 2*cm, height - 16*cm)

    # Total text
    c.drawString(2*cm, height - 17*cm, f"Razem do zapłaty: {total_brutto:.2f} PLN")
    # c.drawString(2*cm, height - 17.5*cm, f"Słownie złotych: ({num2words(total_brutto, lang='pl')} PLN)")

    c.save()
    pdf_content = buffer.getvalue()
    buffer.close()

    return pdf_content






def post_invoice_to_allegro(vendor, invoice, pdf_content, correction):
    """Post the generated invoice to Allegro API."""

    _invoice = None
    _order_id = None

    message = ''

    if correction:
        # print('post_invoice_to_allegro invoice correction TRUE ---------', correction)
        _invoice = invoice
        _order_id = invoice.main_invoice.allegro_order.order_id
    else:
        # print('post_invoice_to_allegro invoice correction FALSE ---------', correction)
        _invoice = invoice
        _order_id = invoice.allegro_order.order_id
    # print('post_invoice_to_allegro invoice_number ---------', _invoice.invoice_number)
    access_token = invoice.vendor.access_token
    url = f"https://{ALLEGRO_API_URL}/order/checkout-forms/{_order_id}/invoices" 

    payload = {
        "file": {
            "name": f"invoice_{_invoice.invoice_number}.pdf"
        },
        "invoiceNumber": _invoice.invoice_number
    }

    headers = {
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/vnd.allegro.public.v1+json',
        'Authorization': f'Bearer {access_token}'
    }

    response = allegro_request("POST", url, vendor.name, headers=headers, data=json.dumps(payload))
    # response = requests.post(url, headers=headers, data=json.dumps(payload))
    print(f"--post_invoice_to_allegro--POST---- {response, response.text}.")
    if response.status_code == 201:
        invoice_id = response.json().get("id")
        res = add_invoice_to_order(invoice_id, invoice, _order_id, access_token, pdf_content, correction)
        message = res
        # print(f"Invoice {invoice.invoice_number} posted successfully to Allegro.")
    elif response.status_code == 422:
        message = f"Faktura {invoice_id} przekroczyła dozwolony limit 10 faktur na zamówienie."
        # print(f"Invoice {invoice_id} has reached limit of maximum number of invoices, which is 10 per order.")
    else:
        message = f"Nie udało się wysłać fakturę {invoice.invoice_number} do Allegro: {response.text}"
        # print(f"Failed to post invoice {invoice.invoice_number} to Allegro: {response.text}")

    return message

def add_invoice_to_order(invoice_id, invoice, order_id, access_token, pdf_content, correction):
    url = f"https://{ALLEGRO_API_URL}/order/checkout-forms/{order_id}/invoices/{invoice_id}/file"

    headers = {
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Content-Type': 'application/pdf',
        'Authorization': f'Bearer {access_token}'
    }

    response = allegro_request("PUT", url, invoice.vendor.name, headers=headers, data=pdf_content)
    # response = requests.put(url, headers=headers, data=pdf_content)
    print(f"--add_invoice_to_order--PUT---- {response, response.text}.")
    if response.status_code == 200:
        invoice.sent_to_buyer = True
        invoice.save()
        return f"Fakturę {invoice.invoice_number} wysłąno do Allegro."
        # print(f"Fakturę {invoice_id} załącząno do zamuwienia {order_id}.")
    else:
        return f"Nie udało się załączyć faktury {invoice_id} do zamówienia {order_id}: {response.text}"
        # print(f"Nie udało się załączyć faktury {invoice_id} do zamówienia {order_id}: {response.text}")




def generate_correction_invoice_allegro(invoice, buyer_info, user, products, _main_invoice_products):
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

    correct_invoice_created_at = localtime(invoice.created_at).strftime('%d-%m-%Y')

    main_invoice_created_at = localtime(invoice.main_invoice.created_at).strftime('%d-%m-%Y')

    # --- Nagłówek ---
    c.setFont("DejaVuSans", 10)
    c.drawString(2 * cm, height - 2 * cm, f"Faktura VAT – korygująca nr: {invoice.invoice_number}")
    c.drawString(2 * cm, height - 2.7 * cm, f"Data wystawienia: {correct_invoice_created_at}")
    c.drawString(2 * cm, height - 4 * cm, f"Dotyczy faktury nr: {invoice.main_invoice.invoice_number}")
    c.drawString(2 * cm, height - 4.7 * cm, f"Wystawionej w dniu: {main_invoice_created_at}")

    # --- Dane sprzedawcy i nabywcy ---
    # c.setFont("DejaVuSans", 9)
    c.drawString(2 * cm, height - 6 * cm, "Sprzedawca:")
    # c.drawString(2 * cm, height - 6.5 * cm, invoice.main_invoice.vendor.name)
    # c.drawString(2 * cm, height - 7 * cm, invoice.main_invoice.vendor.address)
    # c.drawString(2 * cm, height - 7.5 * cm, f"NIP {invoice.main_invoice.vendor.nip}")
    c.drawString(2 * cm, height - 6.5 * cm, str(user.full_name or ""))
    c.drawString(2 * cm, height - 7 * cm, f"{str(invoice.main_invoice.vendor.address or '')}") # Adres:
    c.drawString(2 * cm, height - 7.5 * cm, f"NIP: {str(invoice.main_invoice.vendor.nip or '')}")
    c.drawString(2 * cm, height - 8 * cm, f"Telefon: {str(user.phone or '')}")
    c.drawString(2 * cm, height - 8.5 * cm, f"Email: {str(invoice.main_invoice.vendor.email or '')}")

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
                # str(len(data)), "Transport", "", "1",
                str(len(data)), "Transport", "", "",
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




# WEBSTORE LOGIC 

def generate_invoice_webstore(invoice, vendor, user, buyer_info, products): # tax_rate=23
    # print(' ----------- generate_invoice_webstore products -------------', products)
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

    web_order_occurred = localtime(invoice.shop_order.date).strftime('%d-%m-%Y')
    # year = localtime(invoice.created_at).year

    formatted_generated = localtime(invoice.created_at).strftime('%d-%m-%Y')

    # Title
    # print(' ----------- generate_invoice_webstore invoice -------------', invoice.invoice_number)
    c.setFont("DejaVuSans", 10)
    c.drawString(2 * cm, height - 2 * cm, "Faktura VAT")
    c.drawString(2 * cm, height - 2.5 * cm, f"nr: {invoice.invoice_number}")

    # Delivery info
    c.drawString(12 * cm, height - 2 * cm, f"Data wykonania usługi {web_order_occurred}")
    c.drawString(12 * cm, height - 2.5 * cm, f"Wystawiona w dniu: {formatted_generated}")

    # Seller info
    # print(' ----------- generate_invoice_webstore vendor -------------', vendor.name)
    # print(' ----------- generate_invoice_webstore vendor address -------------', vendor.address)
    # print(' ----------- generate_invoice_webstore vendor nip -------------', vendor.nip)
    # print(' ----------- generate_invoice_webstore vendor mobile -------------', vendor.mobile)
    # print(' ----------- generate_invoice_webstore vendor email -------------', vendor.email)
    c.drawString(2 * cm, height - 4 * cm, "Sprzedawca:")
    c.drawString(2 * cm, height - 4.5 * cm, str(user.full_name or ""))
    c.drawString(2 * cm, height - 5 * cm, f"{str(vendor.address or "")}" ) # Adres:
    c.drawString(2 * cm, height - 5.5 * cm, f"NIP: {str(vendor.nip or "")}" )
    c.drawString(2 * cm, height - 6 * cm, f"Telefon: {str(user.phone or "")}" )
    c.drawString(2 * cm, height - 6.5 * cm, f"E-mail: {str(getattr(vendor, 'email', '') or '')}")

    # Buyer info
    # print(' ----------- generate_invoice_webstore buyer_info name -------------', buyer_info['name'])
    # print(' ----------- generate_invoice_webstore buyer_info street -------------', buyer_info['street'])
    # print(' ----------- generate_invoice_webstore buyer_info zipCode -------------', buyer_info['zipCode'])
    # print(' ----------- generate_invoice_webstore buyer_info city -------------', buyer_info['city'])
    # print(' ----------- generate_invoice_webstore buyer_info taxId -------------', buyer_info['taxId'])

    c.drawString(12 * cm, height - 4 * cm, "Nabywca:")
    c.drawString(12 * cm, height - 4.5 * cm, buyer_info['name'])
    c.drawString(12 * cm, height - 5 * cm, f"ul. {buyer_info['street']}, {buyer_info['zipCode']} {buyer_info['city']}")
    c.drawString(12 * cm, height - 5.5 * cm, f"NIP {buyer_info['taxId']}")

    # Table setup
    data = [
        ["Lp.", "Nazwa towaru lub usługi", "Jm", "Ilość", "Cena netto", "Wartość netto", "VAT", "Kwota VAT", "Wartość brutto"]
    ]

    total_netto = total_vat = total_brutto = 0

    for i, product in enumerate(products, start=1):
        # print(' ----------- generate_invoice_webstore product -------------', product['offer']['name'])
        tax_rate = float(product.get('tax_rate') or 0)
        name = Paragraph(product.get('offer', {}).get('name') or "", normal_style)
        quantity = int(product.get('quantity') or 0)
        price_brutto = float(product.get('price', {}).get('amount') or 0)
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
    delivery_cost = float(invoice.shop_order.shipping_amount or 0)

    if delivery_cost > 0:
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
    # c.drawString(2 * cm, height - 17.5 * cm, f"Słownie złotych: ({num2words(total_brutto, lang='pl')} PLN)")

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




from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.utils.timezone import localtime
import os
from django.conf import settings

def generate_correction_invoice_webstore(invoice, buyer_info, user, products, _main_invoice_products):
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

    correct_invoice_created_at = localtime(invoice.created_at).strftime('%d-%m-%Y')
    main_invoice_created_at = localtime(invoice.main_invoice.created_at).strftime('%d-%m-%Y')

    # --- Nagłówek ---
    c.setFont("DejaVuSans", 10)
    c.drawString(2 * cm, height - 2 * cm, f"Faktura VAT – korygująca nr: {invoice.invoice_number}")
    c.drawString(2 * cm, height - 2.7 * cm, f"Data wystawienia: {correct_invoice_created_at}")
    c.drawString(2 * cm, height - 4 * cm, f"Dotyczy faktury nr: {invoice.main_invoice.invoice_number}")
    c.drawString(2 * cm, height - 4.7 * cm, f"Wystawionej w dniu: {main_invoice_created_at}")

    # --- Dane sprzedawcy i nabywcy ---

    c.setFont("DejaVuSans", 9)
    c.drawString(2 * cm, height - 6 * cm, "Sprzedawca:")
    # c.drawString(2 * cm, height - 6.5 * cm, str(user.full_name or ""))
    # c.drawString(2 * cm, height - 7 * cm, str(invoice.main_invoice.vendor.address or ""))
    # c.drawString(2 * cm, height - 7.5 * cm, str(invoice.main_invoice.vendor.email or ""))
    # c.drawString(2 * cm, height - 8 * cm, str(user.phone or ""))
    # c.drawString(2 * cm, height - 8.5 * cm, f"NIP {str(invoice.main_invoice.vendor.nip or '')}")
    c.drawString(2 * cm, height - 6.5 * cm, str(user.full_name or ""))
    c.drawString(2 * cm, height - 7 * cm, f"{str(invoice.main_invoice.vendor.address or '')}") # Adres: 
    c.drawString(2 * cm, height - 7.5 * cm, f"NIP: {str(invoice.main_invoice.vendor.nip or '')}")
    c.drawString(2 * cm, height - 8 * cm, f"Telefon: {str(user.phone or '')}")
    c.drawString(2 * cm, height - 8.5 * cm, f"Email: {str(invoice.main_invoice.vendor.email or '')}")

    c.drawString(12 * cm, height - 6 * cm, "Nabywca:")
    c.drawString(12 * cm, height - 6.5 * cm, buyer_info['name'])
    c.drawString(12 * cm, height - 7 * cm, f"ul. {buyer_info['street']}, {buyer_info['zipCode']} {buyer_info['city']}")
    c.drawString(12 * cm, height - 7.5 * cm, f"NIP {buyer_info['taxId']}")

    # --- Tabela: Dane przed korektą ---
    c.drawString(2 * cm, height - 11 * cm, "Dane przed korektą:")
    table_before = build_products_table_webstore(_main_invoice_products, normal_style, invoice.main_invoice.shop_order)
    table_before.wrapOn(c, width, height)
    table_before.drawOn(c, 2 * cm, height - 16 * cm)

    # --- Tabela: Dane po korekcie ---
    c.drawString(2 * cm, height - 20 * cm, "Dane po korekcie:")
    table_after = build_products_table_webstore(products, normal_style, invoice.main_invoice.shop_order)
    table_after.wrapOn(c, width, height)
    table_after.drawOn(c, 2 * cm, height - 26 * cm)

    c.save()
    pdf_content = buffer.getvalue()
    buffer.close()
    return pdf_content


def build_products_table_webstore(products, normal_style, shop_order, tax_rate_default=23):
    data = [["Lp.", "Nazwa", "Jm", "Ilość", "Cena netto", "Wartość netto", "VAT", "Kwota VAT", "Wartość brutto"]]
    total_netto = total_vat = total_brutto = 0

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

    # Transport jeśli nie ma w products

    if not has_transport:
        delivery_cost = float(shop_order.shipping_amount or 0)
        if delivery_cost > 0:
            transport_brutto = delivery_cost
            transport_netto = transport_brutto / (1 + tax_rate_default / 100)
            transport_vat = transport_brutto - transport_netto
            total_netto += transport_netto
            total_vat += transport_vat
            total_brutto += transport_brutto
            data.append([
                # str(len(data)), "Transport", "", "",
                f"{transport_netto:.2f} PLN", f"{transport_netto:.2f} PLN",
                f"{tax_rate_default}%", f"{transport_vat:.2f} PLN", f"{transport_brutto:.2f} PLN"
            ])

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
