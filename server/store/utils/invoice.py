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

def generate_invoice_allegro(invoice, vendor, buyer_info, products, tax_rate=23):
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
    c.drawString(2 * cm, height - 2 * cm, "Faktura")
    c.drawString(2 * cm, height - 2.5 * cm, f"nr: {invoice.invoice_number}")

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

    # Delivery info
    c.drawString(2 * cm, height - 7.5 * cm, f"Data wykonania usługi {invoice.created_at.strftime('%Y-%m-%d')}")
    c.drawString(2 * cm, height - 8 * cm, f"Wystawiona w dniu: {formatted_date}")
    invoice.generated_at = formatted_date
    invoice.save()
    # c.drawString(2 * cm, height - 8 * cm, f"Data zakończenia dostawy/usługi: {formatted_date}")

    # Table setup
    data = [
        ["Lp.", "Nazwa towaru lub usługi", "Jm", "Ilość", "Cena netto", "Wartość netto", "VAT", "Kwota VAT", "Wartość brutto"]
    ]

    total_netto = total_vat = total_brutto = 0

    for i, product in enumerate(products, start=1):
        name = Paragraph(product['offer']['name'], normal_style)
        quantity = product['quantity']
        price_netto = float(product['price']['amount'])
        value_netto = price_netto * quantity
        vat_value = value_netto * (tax_rate / 100)
        value_brutto = value_netto + vat_value

        total_netto += value_netto
        total_vat += vat_value
        total_brutto += value_brutto

        data.append([
            str(i), name, "szt.", str(quantity),
            f"{price_netto:.2f} PLN", f"{value_netto:.2f} PLN",
            f"{tax_rate:.2f}%", f"{vat_value:.2f} PLN", f"{value_brutto:.2f} PLN"
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



def post_invoice_to_allegro(invoice, pdf_content):
    """Post the generated invoice to Allegro API."""
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
        add_invoice_to_order(invoice_id, invoice, order_id, access_token, pdf_content)
        print(f"Invoice {invoice.invoice_number} posted successfully to Allegro.")
    else:
        print(f"Failed to post invoice {invoice.invoice_number} to Allegro: {response.text}")

def add_invoice_to_order(invoice_id, invoice, order_id, access_token, pdf_content):
    url = f"https://api.allegro.pl.allegrosandbox.pl/order/checkout-forms/{order_id}/invoices/{invoice_id}/file"

    headers = {
        'Accept': 'application/vnd.allegro.public.v1+json',
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.put(url, headers=headers, data=pdf_content)
    print(f"--add_invoice_to_order--PUT---- {response, response.text}.")
    if response.status_code == 200:
        invoice.sent_to_buyer = True
        invoice.save()
        print(f"Invoice {invoice_id} added successfully to order {order_id}.")
    else:
        print(f"Failed to add invoice {invoice_id} to order {order_id}: {response.text}")