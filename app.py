import streamlit as st
from util import clean_text, isolate_values, inject_values
import fitz 
import easyocr
import sqlite3
import pandas as pd
import numpy as np


def main():
    st.title('Finance dashboard')
    st.write('Upload a PDF file for processing')

    # Create a file uploader
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file:   # Open the PDF
        doc = fitz.open(uploaded_file.name)

        # Initialize EasyOCR reader
        reader = easyocr.Reader(['de'])  # Change 'en' to the language you want to extract

        # Create a progress bar
        progress_bar = st.progress(0)

        # Iterate over each page
        for page_index, page in enumerate(doc):
            # Update the progress bar
            progress_bar.progress((page_index + 1) / len(doc))
            
            # Process the page
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

            page_text = "\n".join(page_content)
            print(page_text)
            print("----")
            cleaned_text = clean_text(page_text)
            print(cleaned_text)
            print("----")
            isolted_values = isolate_values(cleaned_text) # returns a list of dicts with the values isolated
            print(isolted_values)
            print("----")
            inject_values(isolted_values) # injects the values into the database
            
        # Finish the progress bar
        progress_bar.empty()
        
    # Create a connection to the database
    conn = sqlite3.connect('finance.db')

    # Query the data from the database
    df = pd.read_sql_query("SELECT * FROM Buchungswerte", conn)

    # Fill missing values in the 'Saldo' column with the previous values
    df['Saldo'] = df['Saldo'].fillna(method='ffill')
    df['Valuta'] = df['Valuta'].replace('NA', np.nan).fillna(method='ffill')

    # Convert the 'Valuta' column to datetime
    df['Valuta'] = pd.to_datetime(df['Valuta'], format='%d.%m.%Y')

    # Create a new column 'Saldo_numeric' with the integer part of 'Saldo' and without commas and dots
    df['Saldo_numeric'] = pd.to_numeric(df['Saldo'].str.split(',', expand=True)[0].str.replace('.', '').str.replace(',', ''), errors='coerce')

    # Fill missing values in the 'Saldo_numeric' column with the previous values
    df['Saldo_numeric'] = df['Saldo_numeric'].fillna(method='ffill')

    # Group the DataFrame by 'Valuta' and take the sum of 'Saldo_numeric' for each group
    df_grouped = df.groupby('Valuta')['Saldo_numeric'].sum().reset_index()

    # Sort the DataFrame by 'Saldo_numeric' in descending order
    df_sorted = df_grouped.sort_values(by='Saldo_numeric', ascending=False)

    # Create a bar chart with 'Valuta' as the x-axis and 'Saldo_numeric' as the y-axis
    st.bar_chart(df_sorted.set_index('Valuta')['Saldo_numeric'])

    # Close the connection
    conn.close()
    
    # Create a button
    if st.button('Show Database'):
        # Use Streamlit to display the data as a table
        st.table(df)

if __name__ == "__main__":
    main()