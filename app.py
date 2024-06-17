import streamlit as st
from util import clean_text, isolate_values, inject_values
import fitz 
import easyocr
import sqlite3
import pandas as pd


def main():
    st.title('PDF File Processor')
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
        cleaned_content = []
        for page_index in range(len(doc)):
            # Update the progress bar
            progress_bar.progress((page_index + 1) / len(doc))

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

            page_text = "\n".join(page_content)
            cleaned_text = clean_text(page_text)
            cleaned_content.append(cleaned_text)

        for content in cleaned_content:
            isolted_values = isolate_values(content) # returns a list of dicts with the values isolated
            inject_values(isolted_values) # injects the values into the database

        # Create a connection to the database
        conn = sqlite3.connect('my_database.db')

        # Query the data from the database
        df = pd.read_sql_query("SELECT * FROM Buchungswerte", conn)

        # Close the connection
        conn.close()

        # Use Streamlit to display the data as a table
        st.table(df)

        # Finish the progress bar
        progress_bar.empty()

if __name__ == "__main__":
    main()