from django import forms
import datetime


class InvoiceReportForm(forms.Form):
    # Automatyczne generowanie listy lat od 2020 do bieżącego + 5
    current_year = datetime.date.today().year
    YEAR_CHOICES = [(y, y) for y in range(2020, current_year + 6)]

    MONTH_CHOICES = [
        (1, "Styczeń"),
        (2, "Luty"),
        (3, "Marzec"),
        (4, "Kwiecień"),
        (5, "Maj"),
        (6, "Czerwiec"),
        (7, "Lipiec"),
        (8, "Sierpień"),
        (9, "Wrzesień"),
        (10, "Październik"),
        (11, "Listopad"),
        (12, "Grudzień"),
    ]

    year = forms.ChoiceField(
        label="Rok",
        choices=YEAR_CHOICES,
        initial=current_year
    )

    month = forms.ChoiceField(
        label="Miesiąc",
        choices=MONTH_CHOICES,
        initial=datetime.date.today().month
    )



class InvoiceCorrectionsReportForm(forms.Form):
    current_year = datetime.date.today().year
    YEAR_CHOICES = [(y, y) for y in range(2020, current_year + 6)]

    MONTH_CHOICES = [
        (1, "Styczeń"), (2, "Luty"), (3, "Marzec"), (4, "Kwiecień"),
        (5, "Maj"), (6, "Czerwiec"), (7, "Lipiec"), (8, "Sierpień"),
        (9, "Wrzesień"), (10, "Październik"), (11, "Listopad"), (12, "Grudzień"),
    ]

    year = forms.ChoiceField(label="Rok", choices=YEAR_CHOICES, initial=current_year)
    month = forms.ChoiceField(label="Miesiąc", choices=MONTH_CHOICES, initial=datetime.date.today().month)
