from openai import OpenAI
import os

OPENAI_API_KEY = os.environ.get("SUPER_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_allegro_seo_title(base_title: str) -> str:
    prompt = f"""
Jesteś ekspertem Allegro. Na podstawie poniższego tytułu produktu stwórz zoptymalizowany SEO tytuł dla allegro.pl.

Wymagania:
- maksymalnie 75 znaków,
- po polsku,
- naturalny, atrakcyjny,
- bez emotikonów i cudzysłowów.

Oryginalny tytuł:
"{base_title}"

Zwróć tylko nowy tytuł.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Jesteś asystentem e-commerce dla allegro.pl."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=64,
        )

        # POPRAWKA: message.content zamiast message["content"]
        new_title = response.choices[0].message.content.strip()

        # usuń cudzysłowy
        new_title = new_title.strip('"').strip("'")

        return new_title[:75]

    except Exception as e:
        return f"ERROR: {str(e)}"
