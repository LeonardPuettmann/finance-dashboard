import fitz  # PyMuPDF
import easyocr
from tenacity import retry, stop_after_attempt, wait_random_exponential
import requests
import json
import os
from tqdm.auto import tqdm

api_key = os.getenv("MISTRAL_API_KEY")

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def clean_text(extraction):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {
                "role": "user",
                "content": """
                    Du bist ein Experte für Textsäuberung von Bankauszügen. Bitte gebe die folgenden Inhalte als Markdown wieder, sodass ich dieses markdown direkt kopieren und verwenden kann. Bitte benutze keine Tabelle, sonders Liste alle zusammengehörenden Elemente als Block auf. Ein Block sollte so aussehen: 
                    ### Buchung X:
                    - Auftraggeber/Empfänger:
                    - Saldo: 
                    - Betrag:
                    - Valuta: 
                    - Buchungstext:
                    - Verwendungszweck: 

                    Alle weiteren Informationen, welche nicht Buchungen sind, sollen auch als Block dargestellt werden. 
                """.strip()
            },
            {
                "role": "user",
                "content": f"<<< Säubere diesen Text: {extraction} >>>"
            }
        ],
        "max_tokens": 4096,	
        "temperature": 0.0
    }

    response = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, data=json.dumps(payload))
    response.raise_for_status()  # Raise an exception for HTTP errors
    response_object = response.json()
    print(response_object)
    answer = response_object["choices"][0]["message"]["content"]
    return answer

def extract_text_from_pdf(pdf_path, verbose=False):
    # Open the PDF
    doc = fitz.open(pdf_path)

    # Initialize EasyOCR reader
    reader = easyocr.Reader(['de'])  # Change 'en' to the language you want to extract

    # Iterate over each page
    cleaned_content = []
    for page_index in tqdm(range(len(doc))):
        # Get the page
        page = doc[page_index]
        

        # Convert the page to an image
        pix = page.get_pixmap(dpi=300)
        pix.save("temp_page.png")  # Save as a temporary image

        # Extract text from the image
        result = reader.readtext("temp_page.png")

        # Print the extracted text
        page_content = []
        for text_block in result:
            page_content.append(text_block[1])
        if verbose:
            page_text = "\n".join(page_content)
            print(f"Page {page_index + 1}:\n{page_text}")
            print("\n -------- \n")
            cleaned_text = clean_text(page_text)
            print(f"Cleaned Page {page_index + 1}:\n{cleaned_text}")
            print("\n -------- \n")
        else:
            page_text = "\n".join(page_content)
            cleaned_text = clean_text(page_text)
            cleaned_content.append(cleaned_text)
    
    return cleaned_content