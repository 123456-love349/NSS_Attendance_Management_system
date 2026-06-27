from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
import sqlite3
import os
import random
from functools import wraps

# Utilities
from utils.qr_generator import generate_event_qr
from utils.excel_export import export_attendance_to_excel
from utils.proxy_detector import detect_proxies

app = Flask(__name__)
app.secret_key = "nss_secret_key"

DB_PATH = "database.db"


# ---------------- DB CONNECTION ----------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- ADMIN DECORATOR ----------------
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


# ---------------- HOME ----------------
@app.route("/")
def index():
    return render_template("index.html")




# ---------------- OTP VERIFY ----------------
@app.route("/send_otp", methods=["POST"])
def send_otp():
    phone = request.form.get("phone", "").strip()

    if not phone:
        return jsonify({"status": "error", "message": "Phone number required"}), 400

    if not phone.isdigit() or len(phone) != 10:
        return jsonify({"status": "error", "message": "Enter a valid 10-digit phone number"}), 400

    otp = random.randint(1000, 9999)

    session["otp"] = str(otp)
    session["phone"] = phone
    session["verified"] = False

    print("OTP SENT:", otp)

    return jsonify({
        "status": "success",
        "message": "OTP generated successfully",
        "otp": str(otp)      # Demo OTP
    })
# ---------------- OTP VERIFY ----------------
@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    user_otp = request.form.get("otp", "").strip()

    if not session.get("otp"):
        return jsonify({"message": "Please request OTP first"}), 400

    if user_otp == session.get("otp"):
        session["verified"] = True
        return jsonify({"message": "OTP verified"})
    else:
        session["verified"] = False
        return jsonify({"message": "Invalid OTP"}), 400


# ---------------- STUDENT FORM ----------------
@app.route("/student_form", methods=["GET", "POST"])
def student_form():
    conn = get_db_connection()

    if request.method == "POST":
        if not session.get("verified"):
            flash("Please verify OTP first", "error")
            conn.close()
            return redirect(request.url)

        student_name = request.form.get("student_name", "").strip()
        branch = request.form.get("branch", "").strip()
        section = request.form.get("section", "").strip()
        crn = request.form.get("crn", "").strip()
        urn = request.form.get("urn", "").strip()
        phone = request.form.get("phone", "").strip()
        is_nss_volunteer = request.form.get("is_nss_volunteer", "").strip()
        event = request.form.get("event", "").strip()

        if not all([student_name, branch, section, crn, urn, phone, is_nss_volunteer, event]):
            flash("All fields are required", "error")
            conn.close()
            return redirect(url_for("student_form", event=event))

        try:
            existing = conn.execute("""
                SELECT * FROM attendance
                WHERE (urn = ? OR phone = ?) AND event = ?
            """, (urn, phone, event)).fetchone()

            if existing:
                flash("Attendance already marked", "error")
                return redirect(url_for("student_form", event=event))

            conn.execute("""
                INSERT INTO attendance
                (student_name, branch, section, crn, urn, phone, is_nss_volunteer, event, attendance_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                student_name, branch, section, crn,
                urn, phone, is_nss_volunteer, event, "QR Scan"
            ))

            conn.commit()

            session.pop("otp", None)
            session.pop("verified", None)

            flash("Attendance marked successfully!", "success")

        finally:
            conn.close()

        return redirect(url_for("student_form", event=event))

    # GET request
    event_name = request.args.get("event", "").strip()

    events = conn.execute("""
        SELECT DISTINCT event FROM attendance
        WHERE event IS NOT NULL AND event != ''
        ORDER BY event ASC
    """).fetchall()
    conn.close()

    events_list = [row["event"] for row in events]

    return render_template(
        "student_form.html",
        event_name=event_name,
        events_list=events_list
    )


# ---------------- ADMIN LOGIN ----------------
ADMIN_USERNAME = "nss_admin_2026"
ADMIN_PASSWORD = "Arsh123"

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin"))

        flash("Invalid credentials", "error")

    return render_template("admin_login.html")


# ---------------- ADMIN LOGOUT ----------------
@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
@admin_required
def admin():
    conn = get_db_connection()

    total_records = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    suspicious_records = detect_proxies(conn)

    branch_stats = conn.execute("""
        SELECT branch, COUNT(*) as count
        FROM attendance
        GROUP BY branch
        ORDER BY count DESC
    """).fetchall()

    event_stats = conn.execute("""
        SELECT event, COUNT(*) as count
        FROM attendance
        GROUP BY event
        ORDER BY count DESC
    """).fetchall()

    conn.close()

    stats = {
        "total_records": total_records,
        "active_events": len(os.listdir("static/qr_codes")) if os.path.exists("static/qr_codes") else 0,
        "suspicious_alerts": len(suspicious_records)
    }

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        suspicious_records=suspicious_records,
        branch_stats=branch_stats,
        event_stats=event_stats,
        qr_generated=False
    )


# ---------------- MANUAL ENTRY ----------------
@app.route("/admin/manual_entry", methods=["POST"])
@admin_required
def manual_entry():
    student_name = request.form.get("student_name", "").strip()
    branch = request.form.get("branch", "").strip()
    section = request.form.get("section", "").strip()
    crn = request.form.get("crn", "").strip()
    urn = request.form.get("urn", "").strip()
    phone = request.form.get("phone", "").strip()
    is_nss_volunteer = request.form.get("is_nss_volunteer", "").strip()
    event = request.form.get("event", "").strip()

    conn = get_db_connection()

    try:
        existing = conn.execute("""
            SELECT * FROM attendance
            WHERE (urn = ? OR phone = ?) AND event = ?
        """, (urn, phone, event)).fetchone()

        if existing:
            flash("Already marked", "error")
            return redirect(url_for("admin"))

        conn.execute("""
            INSERT INTO attendance
            (student_name, branch, section, crn, urn, phone, is_nss_volunteer, event, attendance_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_name, branch, section, crn,
            urn, phone, is_nss_volunteer, event, "Manual"
        ))

        conn.commit()
        flash("Saved successfully", "success")

    finally:
        conn.close()

    return redirect(url_for("admin"))


# ---------------- QR GENERATE ----------------
@app.route("/admin/generate_qr", methods=["POST"])
@admin_required
def generate_qr():
    event_name = request.form.get("event_name", "").strip()

    if not event_name:
        flash("Event name required", "error")
        return redirect(url_for("admin"))

    try:
        filename, qr_link = generate_event_qr(event_name, request.host_url)

        conn = get_db_connection()

        total_records = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        suspicious_records = detect_proxies(conn)

        branch_stats = conn.execute("""
            SELECT branch, COUNT(*) as count
            FROM attendance
            GROUP BY branch
            ORDER BY count DESC
        """).fetchall()

        event_stats = conn.execute("""
            SELECT event, COUNT(*) as count
            FROM attendance
            GROUP BY event
            ORDER BY count DESC
        """).fetchall()

        conn.close()

        stats = {
            "total_records": total_records,
            "active_events": len(os.listdir("static/qr_codes")) if os.path.exists("static/qr_codes") else 0,
            "suspicious_alerts": len(suspicious_records)
        }

        flash("QR generated successfully!", "success")

        return render_template(
            "admin_dashboard.html",
            stats=stats,
            suspicious_records=suspicious_records,
            branch_stats=branch_stats,
            event_stats=event_stats,
            qr_generated=True,
            qr_filename=filename,
            qr_link=qr_link
        )

    except Exception as e:
        print("QR ERROR:", e)
        flash(f"QR generation failed: {str(e)}", "error")
        return redirect(url_for("admin"))


# ---------------- ANALYTICS ----------------
@app.route("/analytics")
@admin_required
def analytics():
    conn = get_db_connection()

    branch_rows = conn.execute("""
        SELECT branch, COUNT(*) as count
        FROM attendance
        GROUP BY branch
        ORDER BY count DESC
    """).fetchall()

    volunteer_rows = conn.execute("""
        SELECT is_nss_volunteer, COUNT(*) as count
        FROM attendance
        GROUP BY is_nss_volunteer
        ORDER BY count DESC
    """).fetchall()

    mode_rows = conn.execute("""
        SELECT attendance_mode, COUNT(*) as count
        FROM attendance
        GROUP BY attendance_mode
        ORDER BY count DESC
    """).fetchall()

    event_rows = conn.execute("""
        SELECT event, COUNT(*) as count
        FROM attendance
        GROUP BY event
        ORDER BY count DESC
    """).fetchall()

    conn.close()

    branch_data = {
        "labels": [row["branch"] for row in branch_rows if row["branch"]],
        "counts": [row["count"] for row in branch_rows if row["branch"]]
    }

    volunteer_data = {
        "labels": [row["is_nss_volunteer"] for row in volunteer_rows if row["is_nss_volunteer"]],
        "counts": [row["count"] for row in volunteer_rows if row["is_nss_volunteer"]]
    }

    mode_data = {
        "labels": [row["attendance_mode"] for row in mode_rows if row["attendance_mode"]],
        "counts": [row["count"] for row in mode_rows if row["attendance_mode"]]
    }

    event_data = {
        "labels": [row["event"] for row in event_rows if row["event"]],
        "counts": [row["count"] for row in event_rows if row["event"]]
    }

    return render_template(
        "analytics.html",
        branch_data=branch_data,
        volunteer_data=volunteer_data,
        mode_data=mode_data,
        event_data=event_data
    )


# ---------------- RESULTS ----------------
@app.route("/results")
@admin_required
def results():
    conn = get_db_connection()
    records = conn.execute("SELECT * FROM attendance ORDER BY id DESC").fetchall()
    conn.close()

    return render_template("results.html", records=records)


# ---------------- DOWNLOAD EXCEL ----------------
@app.route("/download")
@admin_required
def download():
    conn = get_db_connection()
    file_path = export_attendance_to_excel(conn, "attendance_report.xlsx")
    conn.close()

    return send_file(file_path, as_attachment=True)


# ---------------- API ----------------
@app.route("/api/attendance")
@admin_required
def api_attendance():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM attendance").fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


# ---------------- RUN ----------------
if __name__ == "__main__":
    os.makedirs("static/qr_codes", exist_ok=True)
    os.makedirs("excel_reports", exist_ok=True)
    app.run(debug=True)
