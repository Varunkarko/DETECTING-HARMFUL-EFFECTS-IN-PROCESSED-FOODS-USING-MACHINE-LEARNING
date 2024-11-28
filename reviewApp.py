import streamlit as st
import cv2
import pytesseract
import openpyxl
import wikipedia
from groq import Groq
import numpy as np

client = Groq(api_key="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")
excel_file = 'harmful_ingredients.xlsx'
wb = openpyxl.load_workbook(excel_file)
sheet = wb.active


def fetch_wikipedia_definition(ingredient):
    try:
        return wikipedia.summary(ingredient, sentences=2)
    except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError, wikipedia.exceptions.WikipediaException):
        return None

def get_grok_response(ingredient):
    prompt = f"Evaluate the ingredient '{ingredient}' for harmfulness and benefits."
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
        stream=False,
    )
    return chat_completion.choices[0].message.content

def check_safety(product_text):
    unsafe_ingredients = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        ingredient, _ = row
        if ingredient.lower() in product_text.lower():
            unsafe_ingredients.append(ingredient.lower())
    return unsafe_ingredients

def process_image(image_file):
    image = cv2.imdecode(np.frombuffer(image_file.read(), np.uint8), 1)
    product_text = pytesseract.image_to_string(image)
    unsafe_ingredients = check_safety(product_text)
    
    response_text = ""
    if unsafe_ingredients:
        response_text += "Not Recommended due to UNSAFE ingredients:\n"
        for ingredient in unsafe_ingredients:
            definition = fetch_wikipedia_definition(ingredient)
            response_text += f"\n- {ingredient.capitalize()}: {definition or 'Definition not found'}"
            response_text += f"\n  Groq Analysis: {get_grok_response(ingredient)}"
    else:
        response_text = "All ingredients are safe."
    return response_text, product_text

# Streamlit App for Product Review
st.title("Ingredient Inspector and Review")

uploaded_image = st.file_uploader("Upload an Image", type=["jpg", "jpeg", "png", "bmp"])
if uploaded_image:
    response_text, product_text = process_image(uploaded_image)
    st.write("Product Analysis:", response_text)

    # Review Section
    st.subheader("Review this Product")
    product_name = st.text_input("Product Name")
    rating = st.slider("Star Rating", 1, 5)
    description = st.text_area("Description of Product")

    if st.button("Submit Review"):
        if product_name and description:
            st.success("Thank you for your review!")
            # Here you can save the review data to a file or database if needed.
        else:
            st.error("Please fill out all fields.")
