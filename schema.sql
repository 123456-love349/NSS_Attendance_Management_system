DROP TABLE IF EXISTS attendance;
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    branch TEXT,
    section TEXT,
    crn TEXT,
    urn TEXT,
    phone TEXT,
    is_nss_volunteer TEXT,
    event TEXT,
    attendance_mode TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
