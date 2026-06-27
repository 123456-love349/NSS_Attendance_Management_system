import sqlite3
from datetime import datetime

def detect_proxies(conn):
    """
    Analyzes the database records for suspicious proxy markers:
    1. Same phone number used for different URNs.
    2. Same URN submitted with different Student Names.
    3. Same CRN repeated within the same Branch and Section for the same Event (with different URNs).
    4. Rapid multiple submissions (same URN, Phone, or Event-wide with similar timestamp within 15s).
    """
    cursor = conn.cursor()
    alerts = []

    # 1. Same phone number with different URNs
    cursor.execute('''
        SELECT a1.phone, a1.student_name, a1.urn, a2.student_name, a2.urn, a1.event
        FROM attendance a1
        JOIN attendance a2 ON a1.phone = a2.phone AND a1.urn != a2.urn
        WHERE a1.id < a2.id
    ''')
    for row in cursor.fetchall():
        phone, name1, urn1, name2, urn2, event = row
        alerts.append({
            'type': 'Same Phone Used by Different Students',
            'detail': f"Phone {phone} was used by {name1} (URN {urn1}) and {name2} (URN {urn2}) for event '{event}'.",
            'severity': 'high',
            'identifier': phone
        })

    # 2. Same URN with different student names
    cursor.execute('''
        SELECT a1.urn, a1.student_name, a2.student_name, a1.event
        FROM attendance a1
        JOIN attendance a2 ON a1.urn = a2.urn AND a1.student_name != a2.student_name
        WHERE a1.id < a2.id
    ''')
    for row in cursor.fetchall():
        urn, name1, name2, event = row
        alerts.append({
            'type': 'Same URN with Different Names',
            'detail': f"URN {urn} was registered with different names: '{name1}' and '{name2}' for event '{event}'.",
            'severity': 'high',
            'identifier': urn
        })

    # 3. Same CRN repeated in same Branch/Section for the same Event
    cursor.execute('''
        SELECT a1.crn, a1.branch, a1.section, a1.event, a1.student_name, a1.urn, a2.student_name, a2.urn
        FROM attendance a1
        JOIN attendance a2 ON a1.crn = a2.crn AND a1.branch = a2.branch AND a1.section = a2.section AND a1.event = a2.event AND a1.urn != a2.urn
        WHERE a1.id < a2.id
    ''')
    for row in cursor.fetchall():
        crn, branch, section, event, name1, urn1, name2, urn2 = row
        alerts.append({
            'type': 'CRN Collision',
            'detail': f"CRN {crn} (Branch: {branch}, Sec: {section}) was registered twice for '{event}' by different students: {name1} (URN {urn1}) and {name2} (URN {urn2}).",
            'severity': 'medium',
            'identifier': f"{branch}-{section}-{crn}"
        })

    # 4. Rapid multiple submissions (time-based)
    cursor.execute('''
        SELECT id, student_name, urn, phone, event, created_at
        FROM attendance
        ORDER BY created_at ASC, id ASC
    ''')
    records = cursor.fetchall()
    
    # Helper list to parse datetimes
    parsed_records = []
    for r in records:
        r_id, name, urn, phone, event, created_at_str = r
        try:
            dt = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00').split('.')[0])
            except Exception:
                dt = datetime.now()
        parsed_records.append({
            'id': r_id,
            'name': name,
            'urn': urn,
            'phone': phone,
            'event': event,
            'datetime': dt
        })

    # Check rapid submissions between records
    for i in range(len(parsed_records)):
        for j in range(i + 1, len(parsed_records)):
            r1 = parsed_records[i]
            r2 = parsed_records[j]
            
            # Check if same URN or same Phone or same Event
            if r1['event'] == r2['event']:
                time_diff = abs((r2['datetime'] - r1['datetime']).total_seconds())
                if time_diff < 15:
                    if r1['phone'] == r2['phone'] and r1['urn'] != r2['urn']:
                        alerts.append({
                            'type': 'Rapid Multiple Submissions (Same Phone)',
                            'detail': f"Records for {r1['name']} (URN {r1['urn']}) and {r2['name']} (URN {r2['urn']}) were submitted within {int(time_diff)} seconds of each other using the same phone number {r1['phone']}.",
                            'severity': 'high',
                            'identifier': r1['phone']
                        })
                    elif r1['urn'] == r2['urn']:
                        alerts.append({
                            'type': 'Rapid Duplicate Submission (Same URN)',
                            'detail': f"Multiple submissions for URN {r1['urn']} ({r1['name']}) occurred within {int(time_diff)} seconds.",
                            'severity': 'medium',
                            'identifier': r1['urn']
                        })

    # Deduplicate alerts
    unique_alerts = []
    seen = set()
    for a in alerts:
        key = (a['type'], a['detail'])
        if key not in seen:
            seen.add(key)
            unique_alerts.append(a)

    return unique_alerts
