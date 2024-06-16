import streamlit as st
from util import *


def main():
    st.title('PDF File Processor')
    st.write('Upload a PDF file for processing')

    # Create a file uploader
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file:
        print(uploaded_file.name)

        extracted_texts = extract_text_from_pdf(uploaded_file)	

if __name__ == "__main__":
    main()