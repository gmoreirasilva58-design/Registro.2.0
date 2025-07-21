from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import openai
from dotenv import load_dotenv

# Carregar chave da OpenAI do .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
DB_NAME = "database.db"

# Inicializar banco de dados
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            tags TEXT,
            summary TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Função IA: gerar resumo e tags
def analyze_note(content):
    prompt = (
        f"Texto da anotação:\n{content}\n"
        "\nResuma esse texto em 1-2 frases e sugira 3 a 5 tags relevantes."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Você é um assistente que ajuda a organizar anotações."},
                {"role": "user", "content": prompt}
            ]
        )
        result = response.choices[0].message.content.strip()
        summary, *tags_part = result.split("Tags:")
        tags = tags_part[0] if tags_part else ""
        return summary.strip(), tags.strip()
    except Exception as e:
        return "", ""

@app.route("/")
def index():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, summary FROM notes ORDER BY id DESC")
    notes = cursor.fetchall()
    conn.close()
    return render_template("index.html", notes=notes)

@app.route("/add", methods=["GET", "POST"])
def add_note():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        summary, tags = analyze_note(content)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notes (title, content, tags, summary) VALUES (?, ?, ?, ?)",
                       (title, content, tags, summary))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))
    return render_template("add_note.html")

@app.route("/note/<int:note_id>")
def view_note(note_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE id=?", (note_id,))
    note = cursor.fetchone()
    conn.close()
    return render_template("view_note.html", note=note)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
