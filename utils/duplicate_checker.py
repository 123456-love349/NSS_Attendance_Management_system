def check_duplicate_attendance(conn, urn, event):
    """
    Checks if a student with the given URN has already marked attendance for this event.
    """
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, student_name FROM attendance WHERE urn = ? AND event = ?', 
        (urn, event)
    )
    existing = cursor.fetchone()
    return existing is not None
