import customtkinter as ctk
from tkinter import filedialog
from rag_engine import ask_medical_question
import threading
import speech_recognition as sr
import pyttsx3

# ================= THEME =================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")  # more medical theme

# ================= PATIENT MEMORY =================

patient_symptoms = []
listening = False

# ================= SPEECH FIX =================

def speak(text):
    def run():
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 170)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except:
            pass

    threading.Thread(target=run, daemon=True).start()

# ================= VOICE SYSTEM =================

def toggle_voice():
    global listening

    if not listening:
        listening = True
        voice_btn.configure(text="🛑 Stop Voice", fg_color="#ff4d4d")
        threading.Thread(target=continuous_voice, daemon=True).start()
    else:
        listening = False
        voice_btn.configure(text="🎤 Voice", fg_color="#1f6aa5")

def continuous_voice():
    global listening
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)

            while listening:
                try:
                    status_label.configure(text="🎤 Listening...", text_color="orange")

                    audio = recognizer.listen(source, phrase_time_limit=6)
                    text = recognizer.recognize_google(audio, language="en-IN")

                    entry.delete(0, "end")
                    entry.insert(0, text)

                except:
                    continue

    except:
        status_label.configure(text="⚠ Microphone Error", text_color="red")

# ================= SEND MESSAGE =================

def send_message():
    user_message = entry.get()
    if not user_message.strip():
        return

    chat_box.insert("end", f"\n🧑 You:\n{user_message}\n")
    chat_box.see("end")

    entry.delete(0, "end")
    status_label.configure(text="Analyzing Symptoms...", text_color="yellow")

    threading.Thread(target=process_ai, args=(user_message,), daemon=True).start()

def process_ai(user_message):
    patient_symptoms.append(user_message)

    response, risk = ask_medical_question(
        user_message,
        previous_symptoms=patient_symptoms
    )

    chat_box.insert("end", f"\n🤖 AI Diagnosis:\n{response}\n")

    # Risk badge coloring
    if risk == "LOW":
        risk_color = "green"
    elif risk == "MODERATE":
        risk_color = "orange"
    elif risk == "HIGH":
        risk_color = "red"
    else:
        risk_color = "#ff0000"

    chat_box.insert("end", f"\n⚠ Risk Level: {risk}\n", risk_color)
    chat_box.see("end")

    status_label.configure(text="Ready", text_color="lightgreen")

    speak(response)

# ================= IMAGE =================

def upload_image():
    file_path = filedialog.askopenfilename()
    if file_path:
        chat_box.insert("end", f"\n📷 Image Uploaded:\n{file_path}\n")
        chat_box.insert("end", "Vision analysis integration coming soon.\n")
        chat_box.see("end")

# ================= UI =================

app = ctk.CTk()
app.title("🏥 Advanced Medical Decision Support System")
app.geometry("1100x800")

# Header
header = ctk.CTkLabel(
    app,
    text="🏥 AI Medical Assistant",
    font=("Arial", 28, "bold"),
    text_color="#00cc99"
)
header.pack(pady=20)

# Chat box
chat_box = ctk.CTkTextbox(app, width=1000, height=500)
chat_box.pack(pady=15)

# Input entry
entry = ctk.CTkEntry(
    app,
    width=900,
    height=40,
    font=("Arial", 16),
    placeholder_text="Describe your symptoms..."
)
entry.pack(pady=10)

# Button Frame
button_frame = ctk.CTkFrame(app)
button_frame.pack(pady=10)

send_btn = ctk.CTkButton(
    button_frame,
    text="Send",
    width=140,
    command=send_message,
    fg_color="#0099ff"
)
send_btn.grid(row=0, column=0, padx=15)

voice_btn = ctk.CTkButton(
    button_frame,
    text="🎤 Voice",
    width=140,
    command=toggle_voice
)
voice_btn.grid(row=0, column=1, padx=15)

image_btn = ctk.CTkButton(
    button_frame,
    text="📷 Upload Image",
    width=160,
    command=upload_image,
    fg_color="#33cc33"
)
image_btn.grid(row=0, column=2, padx=15)

# Status Label
status_label = ctk.CTkLabel(
    app,
    text="Ready",
    font=("Arial", 14),
    text_color="lightgreen"
)
status_label.pack(pady=10)

app.mainloop()