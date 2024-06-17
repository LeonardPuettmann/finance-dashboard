import fitz  # PyMuPDF
import easyocr
from tenacity import retry, stop_after_attempt, wait_random_exponential
import requests
import json
import os
from tqdm.auto import tqdm
import sqlite3

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

                    Es ist wichtig, dass Du für jegliche Buchungen exakt dieses Format einhälst, ansonsten kann dein Output nicht verarbeitet werden!
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

def isolate_values(text): 
    # Split the text by the booking header
    bookings = text.split('### ')

    # Iterate over the bookings
    value_dict = []
    for booking in bookings:
        if "Buchung" in booking:
            lines = text.split('\n')

            # Prepare a dictionary to store the values
            values = {}

            # Iterate over the lines
            for line in lines:
                if line.startswith("-"):
                    key, value = line.split(': ')
                    key = key.replace("- ", "")
                    values[key] = value
            value_dict.append(values)
    return value_dict

def inject_values(value_dict, database_name="finance.db"):
    """
    value_dict is a list of dictionaries, where each dictionary contains the values for a single booking. The keys of the dictionary are the column names of the database table. The values are the values for the respective column.
    databse_name is the name of the database file. 
    """
    # Create a connection to the database
    conn = sqlite3.connect(database_name)

    # Create a cursor object
    c = conn.cursor()

    for  values in value_dict:
        # Now you can insert the values into the database
        c.execute('''INSERT INTO Buchungswerte VALUES
                            (?, ?, ?, ?, ?, ?)''',
                        (values['Auftraggeber/Empfänger'],
                        values['Saldo'],
                        values['Betrag'],
                        values['Valuta'],
                        values['Buchungstext'],
                        values['Verwendungszweck']))
        
        # Commit the changes and close the connection
        conn.commit()
    conn.close()