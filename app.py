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

    # Create a button
    if st.button('Load Database'):
        # Create a connection to the database
        conn = sqlite3.connect('finance.db')

        # Query the data from the database
        df = pd.read_sql_query("SELECT * FROM Buchungswerte", conn)

        # Close the connection
        conn.close()

        # Use Streamlit to display the data as a table
        st.table(df)

if __name__ == "__main__":
    main()