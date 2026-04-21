from flask import Flask, request, render_template, session, redirect
import sqlite3
from datetime import date, timedelta

app = Flask(__name__)
app.secret_key = "multifit_secret"

ACTIVIDADES = ["Musculación", "Taekwondo", "Kick Boxing", "Boxeo", "Yoga"]

# ---------------- DB ----------------
def db():
    conn = sqlite3.connect("gym.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- INIT ----------------
def init_db():
    conn = db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS socios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dni TEXT UNIQUE,
        nombre TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS membresias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        socio_id INTEGER,
        actividad TEXT,
        vencimiento TEXT
    )
    """)

    conn.commit()
    conn.close()

# ---------------- CHECK DNI ----------------
def check_dni(dni):
    conn = db()

    rows = conn.execute("""
        SELECT m.* FROM membresias m
        JOIN socios s ON s.id = m.socio_id
        WHERE s.dni=?
    """, (dni,)).fetchall()

    conn.close()

    if not rows:
        return {"status": "no_existe"}

    hoy = date.today()
    detalle = []

    for r in rows:
        venc = date.fromisoformat(r["vencimiento"])
        dias = (venc - hoy).days

        detalle.append({
            "actividad": r["actividad"],
            "estado": "ok" if dias >= 0 else "vencido",
            "dias": dias
        })

    return {"status": "ok", "detalle": detalle}

# ---------------- HOME ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        result = check_dni(request.form.get("dni"))

    return render_template("index.html", result=result)

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("user") == "admin" and request.form.get("pass") == "1234":
            session["admin"] = True
            return redirect("/admin")

    return render_template("login.html")

# ---------------- EDIT ----------------
@app.route("/edit/<int:id>", methods=["POST"])
def edit(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = db()
    nombre = request.form["nombre"]

    conn.execute("UPDATE socios SET nombre=? WHERE id=?", (nombre, id))
    conn.commit()
    conn.close()

    return redirect("/admin")

# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = db()
    conn.execute("DELETE FROM socios WHERE id=?", (id,))
    conn.execute("DELETE FROM membresias WHERE socio_id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")

# ---------------- ADMIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect("/login")

    conn = db()

    if request.method == "POST":
        dni = request.form["dni"]
        nombre = request.form["nombre"]
        actividad = request.form["actividad"]
        dias = int(request.form["dias"])

        vencimiento = (date.today() + timedelta(days=dias)).isoformat()

        # crear o buscar socio
        socio = conn.execute("SELECT * FROM socios WHERE dni=?", (dni,)).fetchone()

        if not socio:
            conn.execute("INSERT INTO socios (dni, nombre) VALUES (?, ?)", (dni, nombre))
            socio_id = conn.execute("SELECT id FROM socios WHERE dni=?", (dni,)).fetchone()["id"]
        else:
            socio_id = socio["id"]

        # evitar duplicar misma actividad
        existe = conn.execute("""
            SELECT * FROM membresias 
            WHERE socio_id=? AND actividad=?
        """, (socio_id, actividad)).fetchone()

        if not existe:
            conn.execute("""
                INSERT INTO membresias (socio_id, actividad, vencimiento)
                VALUES (?, ?, ?)
            """, (socio_id, actividad, vencimiento))

        conn.commit()

    # socios
    socios_raw = conn.execute("SELECT * FROM socios ORDER BY id ASC").fetchall()

    # membresias
    membresias_raw = conn.execute("""
        SELECT m.*, s.dni, s.nombre
        FROM membresias m
        JOIN socios s ON s.id = m.socio_id
    """).fetchall()

    conn.close()

    # estructurar
    socios = {}
    for s in socios_raw:
        socios[s["id"]] = {
            "id": s["id"],
            "dni": s["dni"],
            "nombre": s["nombre"],
            "membresias": []
        }

    for m in membresias_raw:
        socios[m["socio_id"]]["membresias"].append(m)

    actividades = {a: [] for a in ACTIVIDADES}

    for m in membresias_raw:
        actividades[m["actividad"]].append(socios[m["socio_id"]])

    return render_template("admin.html",
                           socios=socios,
                           actividades=actividades,
                           actividades_list=ACTIVIDADES)

# ---------------- START ----------------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)