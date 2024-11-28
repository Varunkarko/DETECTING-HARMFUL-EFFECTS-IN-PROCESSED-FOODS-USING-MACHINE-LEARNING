import cv2
import pytesseract
import openpyxl
import tkinter as tk
from tkinter import filedialog
import wikipedia
from tkinter import ttk
from groq import Groq
import webbrowser

from tkinter import ttk
# Initialize Groq client with API key
client = Groq(api_key="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")

# Load the Excel sheet that contains unsafe ingredients
excel_file = 'harmful_ingredients.xlsx'  # Update the path if necessary
wb = openpyxl.load_workbook(excel_file)
sheet = wb.active

# Function to fetch Wikipedia definition (optional)
def fetch_wikipedia_definition(ingredient):
    try:
        return wikipedia.summary(ingredient, sentences=2)
    except wikipedia.exceptions.DisambiguationError as e:
        return wikipedia.summary(e.options[0], sentences=2)
    except (wikipedia.exceptions.PageError, wikipedia.exceptions.WikipediaException):
        return None

# Function to call Groq API and get evaluation response
def get_grok_response(ingredient):
    prompt = f"Evaluate the ingredient '{ingredient}' for harmfulness, goodness, and any potential health issues caused by it. Provide a percentage score for harmfulness and goodness, describe the harmful effects, and include the uses and benefits of this ingredient."
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
        stream=False,
    )
    
    response = chat_completion.choices[0].message.content
    return response

# Function to check safety based on extracted text
def check_safety(product_text):
    unsafe_ingredients = []
    for row in sheet.iter_rows(min_row=2, values_only=True):  # Start from row 2 to skip headers
        ingredient, _ = row
        if ingredient.lower() in product_text.lower():
            unsafe_ingredients.append(ingredient.lower())
    return unsafe_ingredients

# Process the image, extract ingredients, and display the results
def process_image():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])

    if not file_path:
        result_label.config(text="No image selected", fg="#FF5733")
    else:
        image = cv2.imread(file_path)
        product_text = pytesseract.image_to_string(image)
        
        if not product_text.strip():
            result_label.config(text="No text detected in image", fg="#FF5733")
            return

        unsafe_ingredients = check_safety(product_text)
        definitions_text = ""
        
        if unsafe_ingredients:
            result_text = "The Product is Not Recommended due to UNSAFE Ingredients."
            result_label.config(text=result_text, fg="#FF5733", font=("Arial", 18, "bold"), justify="center")

            for idx, ingredient in enumerate(unsafe_ingredients, start=1):
                definition = fetch_wikipedia_definition(ingredient)
                if definition:
                    definitions_text += f"\n\n{idx}. {ingredient.capitalize()}:\n{definition}"
                else:
                    definitions_text += f"\n\n{idx}. {ingredient.capitalize()}:\nDefinition not found."

                try:
                    grok_response = get_grok_response(ingredient)
                    definitions_text += f"\n\nProduct Evaluation:\n{grok_response}"
                except Exception as e:
                    definitions_text += f"\n\nError fetching Groq response for {ingredient}: {str(e)}"

        else:
            result_text = "The Product is SAFE to Use. All Ingredients are Safe."
            result_label.config(text=result_text, fg="#2ECC71", font=("Arial", 18, "bold"), justify="center")

            ingredients = [ingredient.strip() for ingredient in product_text.split('\n') if ingredient.strip()]
            for idx, ingredient in enumerate(ingredients, start=1):
                definition = fetch_wikipedia_definition(ingredient)
                if definition:
                    definitions_text += f"\n\n{idx}. {ingredient.capitalize()}:\n{definition}"
                else:
                    definitions_text += f"\n\n{idx}. {ingredient.capitalize()}:\nDefinition not found."

                try:
                    grok_response = get_grok_response(ingredient)
                    definitions_text += f"\n\nProduct Evaluation (Uses and Benefits):\n{grok_response}"
                except Exception as e:
                    definitions_text += f"\n\nError fetching Groq response for {ingredient}: {str(e)}"

        definitions_text_widget.config(state=tk.NORMAL)
        definitions_text_widget.delete(1.0, tk.END)
        definitions_text_widget.insert(tk.END, definitions_text)
        definitions_text_widget.config(state=tk.DISABLED)

# Main ingredient inspector app setup
def open_review():
    webbrowser.open("http://localhost:8501")

# Main ingredient inspector app setup
def main_app():
    global result_label, definitions_text_widget

    window = tk.Tk()
    window.title("Ingredient Inspector")
    window.geometry("800x600")
    window.configure(bg="#ECF0F1")

    header_frame = tk.Frame(window, bg="#3498DB")
    header_frame.grid(row=0, column=0, sticky="ew")

    content_frame = tk.Frame(window, bg="#ECF0F1")
    content_frame.grid(row=1, column=0, sticky="nsew", padx=50, pady=30)

    title_label = tk.Label(header_frame, text="Ingredient Inspector", font=("Helvetica", 28, "bold"), bg="#3498DB", fg="white")
    title_label.grid(row=0, column=0, padx=20, pady=20, sticky="nw")

    upload_label = tk.Label(content_frame, text="Please upload your image here:", font=("Helvetica", 14), bg="#ECF0F1", fg="#34495E")
    upload_label.grid(row=0, column=0, padx=20, pady=10)

    upload_button = ttk.Button(content_frame, text="Upload Image", command=process_image, style="TButton")
    upload_button.grid(row=1, column=0, pady=20)

    result_label = tk.Label(content_frame, text="", bg="#ECF0F1", justify="center")
    result_label.grid(row=2, column=0, pady=20)

    definitions_text_widget = tk.Text(content_frame, bg="#ECF0F1", fg="black", font=("Arial", 16, "bold"), wrap="word", height=10, width=80)
    definitions_text_widget.grid(row=3, column=0, pady=20)
    definitions_text_widget.config(state=tk.DISABLED)

    scrollbar = tk.Scrollbar(content_frame, command=definitions_text_widget.yview)
    scrollbar.grid(row=3, column=1, sticky="ns")
    definitions_text_widget.config(yscrollcommand=scrollbar.set)

    # Add the "Review" button with proper padding and styling
    review_button = ttk.Button(content_frame, text="Review", command=open_review, style="TButton")
    review_button.grid(row=4, column=0, pady=30)  # Added padding for spacing

    style = ttk.Style()
    style.configure("TButton", padding=10, relief="flat", background="#2E86C1", foreground="black", font=("Helvetica", 16))

    # Ensure the window grid expands properly
    window.grid_rowconfigure(1, weight=1)
    window.grid_columnconfigure(0, weight=1)

    window.mainloop()

# Function to handle the login page
def login():
    username = username_entry.get()
    password = password_entry.get()
    if username == "admin" and password == "123":  # Customize your credentials here
        login_window.destroy()  # Close the login window
        main_app()  # Open the main ingredient inspection window
    else:
        login_result.config(text="Invalid username or password", fg="red")

# Create a login window
login_window = tk.Tk()
login_window.title("Login")
login_window.geometry("300x200")

# Login form setup
tk.Label(login_window, text="Username:", font=("Helvetica", 14)).pack(pady=5)
username_entry = tk.Entry(login_window, font=("Helvetica", 12))
username_entry.pack(pady=5)

tk.Label(login_window, text="Password:", font=("Helvetica", 14)).pack(pady=5)
password_entry = tk.Entry(login_window, font=("Helvetica", 12), show="*")
password_entry.pack(pady=5)

login_result = tk.Label(login_window, text="", font=("Helvetica", 12))
login_result.pack(pady=5)

login_button = tk.Button(login_window, text="Login", font=("Helvetica", 12), command=login)
login_button.pack(pady=10)

login_window.mainloop()
