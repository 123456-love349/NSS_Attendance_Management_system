import os
import re
import qrcode
import urllib.parse
import time


def sanitize_event_filename(name):
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name)
    return sanitized.strip().replace(" ", "_")


def generate_event_qr(event_name, base_url):
    if not event_name:
        raise ValueError("Event name is required")

    safe_name = sanitize_event_filename(event_name)
    if not safe_name:
        raise ValueError("Invalid event name characters")

    qr_dir = os.path.join("static", "qr_codes")
    os.makedirs(qr_dir, exist_ok=True)

    filename = f"{safe_name}_{int(time.time())}.png"
    filepath = os.path.join(qr_dir, filename)

    encoded_event = urllib.parse.quote(event_name)
    qr_link = urllib.parse.urljoin(base_url, f"student_form?event={encoded_event}")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )

    qr.add_data(qr_link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#002147", back_color="white")
    img.save(filepath)

    return filename, qr_link
