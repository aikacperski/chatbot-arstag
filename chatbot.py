from flask import Flask, request, jsonify, render_template
from flask_cors import CORS  # Import CORS
import openai
import csv
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os  # Import do obsługi zmiennych środowiskowych
from dotenv import load_dotenv  # Import dotenv

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

# Ustawienia OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Dane logowania do e-maila
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Funkcja do obsługi chatbota z obsługą języków
def chatbot_response(prompt, language="pl"):
    """Funkcja do generowania odpowiedzi z OpenAI API z obsługą języków."""
    try:
        system_message = (
            "Jesteś chatbotem pomagającym klientom arstag.com. "
            "Arstag.com oferuje gotowe obrazy olejne oraz możliwość zamówienia obrazów indywidualnych. "
            "Obrazy są ręcznie malowane farbami olejnymi na płótnie. "
            "Indywidualne zamówienia wymagają podania szczegółów: rozmiaru, tematyki, ramy oraz dodatkowych preferencji. "
            "Ceny obrazów zaczynają się od 500 zł. Koszt ramy to dodatkowe 100 zł. "
            "Opakowanie na prezent z kokardą kosztuje 100 zł. "
            "Ceny większych obrazów od 50x50 cm ustalane są indywidualnie. "
            "Uwaga: Arstag.com nie wykonuje karykatur."
        )
        if language == "en":
            system_message = (
                "You are a chatbot helping clients of arstag.com. "
                "Arstag.com offers ready-made oil paintings and custom-made paintings upon request. "
                "The paintings are hand-painted with oil paints on canvas. "
                "Custom orders require details such as size, theme, frame, and other preferences. "
                "Prices start from 500 PLN. The cost of a frame is an additional 100 PLN. "
                "Gift wrapping with a ribbon costs 100 PLN. "
                "Prices for larger paintings starting from 50x50 cm are determined individually. "
                "Note: Arstag.com does not create caricatures."
            )

        # Typowe odpowiedzi na pytania
        custom_answers = {
            "pl": {
                "jak masz na imię": "Nazywam się Arstag - osobisty asystent Sylwii Kacperskiej. Jak mogę Ci pomóc?",
                "cennik": (
                    "Ceny obrazów zaczynają się od 500 zł. Dodatkowa rama zamiast malowanych brzegów obrazu kosztuje 100 zł. "
                    "Opakowanie na prezent z kokardą to również 100 zł. "
                    "Ceny większych obrazów od 50x50 cm ustalane są indywidualnie. "
                    "Proszę o podanie e-maila do kontaktu przy składaniu zamówienia."
                ),
                "indywidualne zamówienia": (
                    "Tak, oferujemy indywidualne zamówienia! Proszę podać szczegóły zamówienia:\n"
                    "- Wymiary obrazu (np. 50x50 cm)\n"
                    "- Tematyka (np. kosmos, natura, portret)\n"
                    "- Kolor ramy (jeśli potrzebujesz ramy, koszt to 100 zł)\n"
                    "- Czy zapakować na prezent? (koszt 100 zł)\n"
                    "Ceny indywidualnych obrazów zaczynają się od 500 zł, a czas realizacji wynosi 28 dni.\n"
                    "Proszę o podanie e-maila do kontaktu. Uwaga: Nie wykonujemy karykatur."
                )
            },
            "en": {
                "what's your name": "My name is Arstag - the personal assistant of Sylwia Kacperska. How can I assist you?",
                "price list": (
                    "Prices for paintings start from 500 PLN. An additional frame instead of painted edges costs 100 PLN. "
                    "Gift wrapping with a ribbon is also 100 PLN. "
                    "Prices for larger paintings starting from 50x50 cm are determined individually. "
                    "Please provide an email for contact when placing an order."
                ),
                "custom orders": (
                    "Yes, we offer custom orders! Please provide the following details:\n"
                    "- Dimensions (e.g., 50x50 cm)\n"
                    "- Theme (e.g., cosmos, nature, portrait)\n"
                    "- Frame color (if needed, the cost is 100 PLN)\n"
                    "- Gift wrapping (if needed, the cost is 100 PLN)\n"
                    "Custom paintings start at 500 PLN, and the production time is 28 days.\n"
                    "Please provide an email for contact. Note: We do not create caricatures."
                )
            }
        }

        # Jeśli pytanie pasuje do typowych odpowiedzi
        for key, response in custom_answers.get(language, {}).items():
            if key in prompt.lower():
                return response

        # Generowanie odpowiedzi za pomocą OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Błąd: {e}" if language == "pl" else f"Error: {e}"

# Logowanie interakcji
def log_interaction(user_input, bot_response):
    """Funkcja zapisująca interakcję do pliku CSV"""
    try:
        with open("chat_logs.csv", mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if file.tell() == 0:
                writer.writerow(["Data i godzina", "Pytanie użytkownika", "Odpowiedź bota"])
            writer.writerow([datetime.now(), user_input, bot_response])
    except Exception as e:
        print(f"Błąd podczas zapisu do pliku: {e}")

# Funkcja do wysyłania powiadomień e-mail
def send_email_notification(user_input, bot_response):
    """Funkcja wysyłająca powiadomienie e-mail o nowym pytaniu do chatbota"""
    try:
        subject = "Nowa wiadomość od chatbota arstag.com"
        body = f"""
        Użytkownik zadał pytanie:\n{user_input}\n\n
        Odpowiedź bota:\n{bot_response}\n\n
        Data i czas: {datetime.now()}
        """

        # Tworzenie wiadomości e-mail
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = EMAIL_ADDRESS
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Wysyłanie e-maila
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Błąd podczas wysyłania e-maila: {e}")

# Tworzenie aplikacji Flask
app = Flask(__name__)
CORS(app)  # Dodanie obsługi CORS

@app.route("/")
def index():
    """Strona główna"""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Endpoint do obsługi zapytań do chatbota"""
    data = request.get_json()
    user_input = data.get("message", "")
    language = data.get("language", "pl")

    if not user_input:
        return jsonify({"error": "Brak wiadomości"}), 400

    bot_response = chatbot_response(user_input, language)
    log_interaction(user_input, bot_response)
    send_email_notification(user_input, bot_response)

    return jsonify({"response": bot_response})

if __name__ == "__main__":
    app.run(debug=True)
