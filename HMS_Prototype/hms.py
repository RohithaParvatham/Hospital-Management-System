import sqlite3
import tkinter as tk
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import messagebox, ttk


APP_NAME = "HMS | Hospital Management System"
SPECIALTIES = (
    "Cardiology",
    "Dermatology",
    "Emergency Medicine",
    "Gastroenterology",
    "General Medicine",
    "Nephrology",
    "Neurology",
    "Obstetrics & Gynecology",
    "Oncology",
    "Ophthalmology",
    "Orthopedics",
    "Pediatrics",
    "Pulmonology",
    "Urology",
)
PATIENT_TYPES = ("Outpatient", "Inpatient")
PRIORITIES = ("Urgent", "High", "Routine")
APPOINTMENT_STATUSES = (
    "Scheduled",
    "Checked in",
    "In consultation",
    "Completed",
    "Cancelled",
    "No-show",
)
APPOINTMENT_TRANSITIONS = {
    "Scheduled": ("Checked in", "Cancelled", "No-show"),
    "Checked in": ("In consultation", "Cancelled", "No-show"),
    "In consultation": ("Completed",),
    "Completed": (),
    "Cancelled": (),
    "No-show": (),
}
STATUSES = {
    "Outpatient": ("Waiting", "In consultation", "Visit complete"),
    "Inpatient": ("Admitted", "Discharged"),
}
PRIORITY_ORDER = {"Urgent": 0, "High": 1, "Routine": 2}

COLORS = {
    "navy": "#14283F",
    "navy_light": "#203A55",
    "teal": "#148A83",
    "teal_light": "#E6F4F2",
    "background": "#F3F6F9",
    "white": "#FFFFFF",
    "text": "#1E2D3D",
    "muted": "#718096",
    "border": "#E1E8EF",
    "red": "#B8323C",
    "red_light": "#FCEAEC",
    "amber": "#9A6500",
    "amber_light": "#FFF4D6",
    "green": "#26734D",
    "green_light": "#E8F5ED",
}


class HospitalStore:
    """Local prototype data store; it is independent of the original MySQL app."""

    def __init__(self, database_path=None):
        self.database_path = Path(database_path or Path(__file__).with_name("hms_prototype.sqlite3"))
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        self._seed_doctors()

    def _create_tables(self):
        with self.connection:
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS doctors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    specialty TEXT NOT NULL,
                    credentials TEXT NOT NULL DEFAULT '',
                    clinic TEXT NOT NULL DEFAULT '',
                    extension TEXT NOT NULL DEFAULT '',
                    active INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS patients (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    sex TEXT NOT NULL,
                    contact TEXT NOT NULL DEFAULT '',
                    patient_type TEXT NOT NULL CHECK(patient_type IN ('Outpatient', 'Inpatient')),
                    specialty TEXT NOT NULL,
                    doctor_id INTEGER NOT NULL REFERENCES doctors(id),
                    priority TEXT NOT NULL CHECK(priority IN ('Urgent', 'High', 'Routine')),
                    status TEXT NOT NULL,
                    bed TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT NOT NULL REFERENCES patients(id),
                    doctor_id INTEGER NOT NULL REFERENCES doctors(id),
                    appointment_at TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL CHECK(duration_minutes IN (15, 30, 45, 60)),
                    reason TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL CHECK(status IN (
                        'Scheduled', 'Checked in', 'In consultation',
                        'Completed', 'Cancelled', 'No-show'
                    )),
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_appointments_date_doctor
                    ON appointments(appointment_at, doctor_id);
                CREATE TABLE IF NOT EXISTS app_settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL
                );
                INSERT OR IGNORE INTO app_settings (setting_key, setting_value)
                VALUES ('inpatient_bed_capacity', '0');
                """
            )

    def _seed_doctors(self):
        if self.connection.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]:
            return
        demo_doctors = (
            ("Dr. A. Mehta", "Cardiology", "MD, DM", "Heart Centre", "201"),
            ("Dr. N. Rao", "Neurology", "MD, DM", "Neurosciences", "214"),
            ("Dr. S. Iyer", "Orthopedics", "MS, DNB", "Bone & Joint Centre", "226"),
            ("Dr. P. Kapoor", "Pediatrics", "MD, DCH", "Children's Clinic", "232"),
            ("Dr. R. Shah", "General Medicine", "MD", "OPD - Block A", "108"),
            ("Dr. K. Nair", "Oncology", "MD, DM", "Cancer Centre", "305"),
            ("Dr. M. Das", "Emergency Medicine", "MD", "Emergency Department", "100"),
            ("Dr. I. Joseph", "Gastroenterology", "MD, DM", "Digestive Health Unit", "241"),
            ("Dr. V. Menon", "Nephrology", "MD, DM", "Renal Centre", "252"),
            ("Dr. T. Bose", "Obstetrics & Gynecology", "MS, DNB", "Women's Health", "263"),
            ("Dr. F. Ali", "Pulmonology", "MD, DNB", "Respiratory Unit", "274"),
        )
        with self.connection:
            self.connection.executemany(
                """
                INSERT INTO doctors (name, specialty, credentials, clinic, extension)
                VALUES (?, ?, ?, ?, ?)
                """,
                demo_doctors,
            )

    def list_doctors(self, specialty=None):
        query = """
            SELECT d.*, COUNT(p.id) AS active_patients
            FROM doctors AS d
            LEFT JOIN patients AS p
                ON p.doctor_id = d.id AND p.status NOT IN ('Discharged', 'Visit complete')
            WHERE d.active = 1
        """
        params = ()
        if specialty and specialty != "All specialties":
            query += " AND d.specialty = ?"
            params = (specialty,)
        query += " GROUP BY d.id ORDER BY d.specialty, d.name"
        return self.connection.execute(query, params).fetchall()

    def add_doctor(self, name, specialty, credentials, clinic, extension):
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO doctors (name, specialty, credentials, clinic, extension)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name.strip(), specialty, credentials.strip(), clinic.strip(), extension.strip()),
            )
        return cursor.lastrowid

    def list_patients(self, patient_type=None, priority=None, search=""):
        query = """
            SELECT p.*, d.name AS doctor_name
            FROM patients AS p
            JOIN doctors AS d ON d.id = p.doctor_id
            WHERE 1 = 1
        """
        params = []
        if patient_type and patient_type != "All patient types":
            query += " AND p.patient_type = ?"
            params.append(patient_type)
        if priority and priority != "All priorities":
            query += " AND p.priority = ?"
            params.append(priority)
        search = search.strip()
        if search:
            query += " AND (p.id LIKE ? OR p.name LIKE ? OR p.specialty LIKE ? OR d.name LIKE ?)"
            match = f"%{search}%"
            params.extend((match, match, match, match))
        query += """
            ORDER BY
                CASE p.priority WHEN 'Urgent' THEN 0 WHEN 'High' THEN 1 ELSE 2 END,
                p.created_at DESC
        """
        return self.connection.execute(query, params).fetchall()

    def list_active_inpatients(self):
        return self.connection.execute(
            """
            SELECT p.*, d.name AS doctor_name
            FROM patients AS p
            JOIN doctors AS d ON d.id = p.doctor_id
            WHERE p.patient_type = 'Inpatient' AND p.status != 'Discharged'
            ORDER BY
                CASE p.priority WHEN 'Urgent' THEN 0 WHEN 'High' THEN 1 ELSE 2 END,
                p.created_at ASC
            """
        ).fetchall()

    def list_outpatient_queue(self):
        return self.connection.execute(
            """
            SELECT p.*, d.name AS doctor_name
            FROM patients AS p
            JOIN doctors AS d ON d.id = p.doctor_id
            WHERE p.patient_type = 'Outpatient'
              AND p.status IN ('Waiting', 'In consultation')
            ORDER BY
                CASE p.priority WHEN 'Urgent' THEN 0 WHEN 'High' THEN 1 ELSE 2 END,
                CASE p.status WHEN 'In consultation' THEN 0 ELSE 1 END,
                p.created_at ASC
            """
        ).fetchall()

    def specialty_workload(self):
        return self.connection.execute(
            """
            SELECT p.specialty, COUNT(*) AS active_cases,
                   COUNT(DISTINCT p.doctor_id) AS assigned_doctors
            FROM patients AS p
            WHERE p.status NOT IN ('Discharged', 'Visit complete')
            GROUP BY p.specialty
            ORDER BY active_cases DESC, p.specialty
            """
        ).fetchall()

    def get_bed_capacity(self):
        row = self.connection.execute(
            """
            SELECT setting_value FROM app_settings
            WHERE setting_key = 'inpatient_bed_capacity'
            """
        ).fetchone()
        return int(row["setting_value"]) if row else 0

    def set_bed_capacity(self, capacity):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 0:
            raise ValueError("Bed capacity must be a non-negative whole number.")
        occupied = len(self.list_active_inpatients())
        if capacity < occupied:
            raise ValueError(
                f"Capacity cannot be below the current inpatient census ({occupied})."
            )
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO app_settings (setting_key, setting_value)
                VALUES ('inpatient_bed_capacity', ?)
                ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
                """,
                (str(capacity),),
            )

    def load_demo_data(self):
        if self.sample_case_count():
            raise ValueError("Fictional sample patients have already been loaded.")

        demo_names = (
            ("SAMPLE - Patient A", 42, "Female", "Outpatient", "Cardiology", "Urgent", "Waiting", "", 18),
            ("SAMPLE - Patient B", 57, "Male", "Inpatient", "Neurology", "High", "Admitted", "NEURO-12", 75),
            ("SAMPLE - Patient C", 34, "Female", "Outpatient", "Orthopedics", "Routine", "Waiting", "", 35),
            ("SAMPLE - Patient D", 68, "Male", "Inpatient", "Cardiology", "Routine", "Admitted", "", 180),
            ("SAMPLE - Patient E", 9, "Not specified", "Outpatient", "Pediatrics", "High", "In consultation", "", 52),
        )
        doctor_by_specialty = {
            row["specialty"]: row["id"]
            for row in self.connection.execute(
                "SELECT id, specialty FROM doctors WHERE active = 1"
            ).fetchall()
        }
        now = datetime.now()
        with self.connection:
            next_number = self.connection.execute(
                """
                SELECT COALESCE(MAX(CAST(SUBSTR(id, 5) AS INTEGER)), 0) + 1
                FROM patients
                """
            ).fetchone()[0]
            for index, case in enumerate(demo_names):
                name, age, sex, patient_type, specialty, priority, status, bed, minutes_ago = case
                doctor_id = doctor_by_specialty.get(specialty)
                if doctor_id is None:
                    raise ValueError(f"No active demo doctor is configured for {specialty}.")
                created_at = (
                    now - timedelta(minutes=minutes_ago)
                ).replace(second=0, microsecond=0).isoformat(timespec="minutes")
                patient_id = f"HMS-{next_number + index:04d}"
                self.connection.execute(
                    """
                    INSERT INTO patients (
                        id, name, age, sex, contact, patient_type, specialty,
                        doctor_id, priority, status, bed, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        patient_id, name, age, sex, "", patient_type, specialty,
                        doctor_id, priority, status, bed, created_at,
                    ),
                )
        self.load_demo_appointments()

    def load_demo_appointments(self):
        samples = self.connection.execute(
            """
            SELECT p.id, p.doctor_id, p.specialty
            FROM patients AS p
            WHERE p.patient_type = 'Outpatient' AND p.name LIKE 'SAMPLE - %'
            ORDER BY p.id
            """
        ).fetchall()
        if len(samples) < 3:
            raise ValueError("Load the fictional sample patients before adding sample appointments.")
        sample_ids = tuple(patient["id"] for patient in samples)
        placeholders = ",".join("?" for _ in sample_ids)
        existing = self.connection.execute(
            f"SELECT COUNT(*) FROM appointments WHERE patient_id IN ({placeholders})",
            sample_ids,
        ).fetchone()[0]
        if existing:
            raise ValueError("Sample appointments have already been loaded.")

        now = datetime.now().replace(second=0, microsecond=0)
        first_start = now + timedelta(minutes=15)
        remainder = first_start.minute % 15
        if remainder:
            first_start += timedelta(minutes=15 - remainder)
        if first_start.hour >= 15:
            first_start = (first_start + timedelta(days=1)).replace(hour=9, minute=0)
        elif first_start.hour < 8:
            first_start = first_start.replace(hour=9, minute=0)

        reasons = (
            "Initial specialty consultation",
            "Orthopedic follow-up",
            "Pediatric clinic review",
        )
        sample_slots = []
        for index, patient in enumerate(samples[:3]):
            candidate = first_start + timedelta(minutes=30 * index)
            for _attempt in range(24):
                end = candidate + timedelta(minutes=30)
                conflict = self.connection.execute(
                    """
                    SELECT 1 FROM appointments
                    WHERE doctor_id = ?
                      AND status NOT IN ('Cancelled', 'No-show', 'Completed')
                      AND datetime(appointment_at) < datetime(?)
                      AND datetime(appointment_at, '+' || duration_minutes || ' minutes')
                          > datetime(?)
                    LIMIT 1
                    """,
                    (
                        patient["doctor_id"],
                        end.isoformat(timespec="minutes"),
                        candidate.isoformat(timespec="minutes"),
                    ),
                ).fetchone()
                if not conflict:
                    sample_slots.append((patient, candidate))
                    break
                candidate += timedelta(minutes=30)
            else:
                raise ValueError(
                    f"No example appointment slot is available for {patient['specialty']}."
                )

        with self.connection:
            for index, (patient, appointment_start) in enumerate(sample_slots):
                appointment_at = appointment_start.isoformat(timespec="minutes")
                self.connection.execute(
                    """
                    INSERT INTO appointments (
                        patient_id, doctor_id, appointment_at, duration_minutes,
                        reason, status, created_at
                    )
                    VALUES (?, ?, ?, 30, ?, 'Scheduled', ?)
                    """,
                    (
                        patient["id"], patient["doctor_id"], appointment_at,
                        reasons[index], now.isoformat(timespec="minutes"),
                    ),
                )

    def list_appointments(self, appointment_date=None):
        query = """
            SELECT a.*, p.name AS patient_name, p.specialty,
                   d.name AS doctor_name, d.clinic,
                   printf('APT-%04d', a.id) AS appointment_number
            FROM appointments AS a
            JOIN patients AS p ON p.id = a.patient_id
            JOIN doctors AS d ON d.id = a.doctor_id
            WHERE 1 = 1
        """
        params = []
        if appointment_date:
            try:
                date.fromisoformat(appointment_date)
            except ValueError as error:
                raise ValueError("Enter the date in YYYY-MM-DD format.") from error
            query += " AND SUBSTR(a.appointment_at, 1, 10) = ?"
            params.append(appointment_date)
        query += " ORDER BY a.appointment_at, d.name"
        return self.connection.execute(query, params).fetchall()

    def add_appointment(self, patient_id, doctor_id, appointment_at, duration_minutes, reason):
        try:
            start = datetime.fromisoformat(appointment_at)
        except ValueError as error:
            raise ValueError("Enter a valid appointment date and time.") from error
        if start.tzinfo is not None:
            raise ValueError("Use the hospital's local date and time without a timezone suffix.")
        if start <= datetime.now():
            raise ValueError("New appointments must be scheduled for a future date and time.")
        if isinstance(duration_minutes, bool) or duration_minutes not in (15, 30, 45, 60):
            raise ValueError("Choose an appointment duration of 15, 30, 45, or 60 minutes.")

        patient = self.connection.execute(
            "SELECT patient_type, specialty FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
        if patient is None:
            raise ValueError("Choose a patient from the patient register.")
        if patient["patient_type"] != "Outpatient":
            raise ValueError("Appointments can only be booked for outpatient records.")
        doctor = self.connection.execute(
            "SELECT specialty FROM doctors WHERE id = ? AND active = 1", (doctor_id,)
        ).fetchone()
        if doctor is None:
            raise ValueError("Choose an active doctor from the directory.")
        if doctor["specialty"] != patient["specialty"]:
            raise ValueError("The selected doctor does not match the patient's specialty.")

        end = start + timedelta(minutes=duration_minutes)
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            conflict = self.connection.execute(
                """
                SELECT a.appointment_at, a.doctor_id, a.patient_id
                FROM appointments AS a
                WHERE a.status NOT IN ('Cancelled', 'No-show', 'Completed')
                  AND (a.doctor_id = ? OR a.patient_id = ?)
                  AND datetime(a.appointment_at) < datetime(?)
                  AND datetime(a.appointment_at, '+' || a.duration_minutes || ' minutes') > datetime(?)
                ORDER BY a.appointment_at
                LIMIT 1
                """,
                (
                    doctor_id,
                    patient_id,
                    end.isoformat(timespec="minutes"),
                    start.isoformat(timespec="minutes"),
                ),
            ).fetchone()
            if conflict:
                conflict_time = datetime.fromisoformat(conflict["appointment_at"]).strftime("%H:%M")
                if conflict["patient_id"] == patient_id:
                    raise ValueError(
                        f"This patient already has an active appointment overlapping {conflict_time}."
                    )
                raise ValueError(
                    f"This doctor already has an active appointment overlapping {conflict_time}."
                )
            cursor = self.connection.execute(
                """
                INSERT INTO appointments (
                    patient_id, doctor_id, appointment_at, duration_minutes,
                    reason, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, 'Scheduled', ?)
                """,
                (
                    patient_id,
                    doctor_id,
                    start.isoformat(timespec="minutes"),
                    duration_minutes,
                    reason.strip(),
                    datetime.now().isoformat(timespec="minutes"),
                ),
            )
        return cursor.lastrowid

    def update_appointment_status(self, appointment_id, status):
        appointment = self.connection.execute(
            "SELECT status FROM appointments WHERE id = ?", (appointment_id,)
        ).fetchone()
        if appointment is None:
            raise ValueError("The selected appointment was not found.")
        if status not in APPOINTMENT_TRANSITIONS[appointment["status"]]:
            raise ValueError(
                f"Cannot move an appointment from {appointment['status']} to {status}."
            )
        with self.connection:
            self.connection.execute(
                "UPDATE appointments SET status = ? WHERE id = ?",
                (status, appointment_id),
            )

    def sample_appointment_count(self):
        return self.connection.execute(
            """
            SELECT COUNT(*) FROM appointments AS a
            JOIN patients AS p ON p.id = a.patient_id
            WHERE p.name LIKE 'SAMPLE - %'
            """
        ).fetchone()[0]

    def sample_appointment_date(self):
        row = self.connection.execute(
            """
            SELECT MIN(a.appointment_at) AS first_appointment
            FROM appointments AS a
            JOIN patients AS p ON p.id = a.patient_id
            WHERE p.name LIKE 'SAMPLE - %'
            """
        ).fetchone()
        return row["first_appointment"][:10] if row and row["first_appointment"] else None

    def add_patient(
        self,
        name,
        age,
        sex,
        contact,
        patient_type,
        specialty,
        doctor_id,
        priority,
        bed,
    ):
        if patient_type not in PATIENT_TYPES:
            raise ValueError("Choose Inpatient or Outpatient.")
        if priority not in PRIORITIES:
            raise ValueError("Choose a workflow priority.")
        if specialty not in SPECIALTIES:
            raise ValueError("Choose a listed specialty.")
        allowed_statuses = STATUSES[patient_type]
        status = "Admitted" if patient_type == "Inpatient" else "Waiting"
        if status not in allowed_statuses:
            raise ValueError("The initial status is not valid for this patient type.")

        with self.connection:
            next_number = self.connection.execute(
                """
                SELECT COALESCE(MAX(CAST(SUBSTR(id, 5) AS INTEGER)), 0) + 1
                FROM patients
                """
            ).fetchone()[0]
            patient_id = f"HMS-{next_number:04d}"
            self.connection.execute(
                """
                INSERT INTO patients (
                    id, name, age, sex, contact, patient_type, specialty,
                    doctor_id, priority, status, bed, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patient_id,
                    name.strip(),
                    age,
                    sex,
                    contact.strip(),
                    patient_type,
                    specialty,
                    doctor_id,
                    priority,
                    status,
                    bed.strip(),
                    datetime.now().isoformat(timespec="minutes"),
                ),
            )
        return patient_id

    def update_status(self, patient_id, status):
        patient = self.connection.execute(
            "SELECT patient_type FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
        if patient is None:
            raise ValueError("The selected patient record was not found.")
        if status not in STATUSES[patient["patient_type"]]:
            raise ValueError("That status is not available for this patient type.")
        with self.connection:
            self.connection.execute(
                "UPDATE patients SET status = ? WHERE id = ?", (status, patient_id)
            )

    def update_patient_bed(self, patient_id, bed):
        patient = self.connection.execute(
            "SELECT patient_type, status FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
        if patient is None:
            raise ValueError("The selected patient record was not found.")
        if patient["patient_type"] != "Inpatient" or patient["status"] == "Discharged":
            raise ValueError("A bed can only be assigned to an active inpatient.")
        bed = bed.strip()
        if bed:
            occupied = self.connection.execute(
                """
                SELECT id FROM patients
                WHERE patient_type = 'Inpatient' AND status != 'Discharged'
                  AND id != ? AND UPPER(TRIM(bed)) = UPPER(?)
                """,
                (patient_id, bed),
            ).fetchone()
            if occupied:
                raise ValueError(f"Bed / room {bed} is already assigned to an active inpatient.")
        with self.connection:
            self.connection.execute(
                "UPDATE patients SET bed = ? WHERE id = ?", (bed, patient_id)
            )

    def dashboard_counts(self):
        counts = self.connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN patient_type = 'Inpatient' AND status != 'Discharged' THEN 1 ELSE 0 END) AS inpatients,
                SUM(CASE WHEN patient_type = 'Outpatient' AND status != 'Visit complete' THEN 1 ELSE 0 END) AS outpatients,
                SUM(CASE WHEN patient_type = 'Outpatient' AND status = 'Waiting' THEN 1 ELSE 0 END) AS waiting,
                SUM(CASE WHEN patient_type = 'Outpatient' AND status = 'In consultation' THEN 1 ELSE 0 END) AS in_consultation,
                SUM(CASE WHEN priority = 'Urgent' AND status NOT IN ('Discharged', 'Visit complete') THEN 1 ELSE 0 END) AS urgent,
                SUM(CASE WHEN priority IN ('Urgent', 'High') AND status NOT IN ('Discharged', 'Visit complete') THEN 1 ELSE 0 END) AS high_priority,
                SUM(CASE WHEN patient_type = 'Inpatient' AND status != 'Discharged'
                          AND (bed IS NULL OR TRIM(bed) = '') THEN 1 ELSE 0 END) AS patients_without_bed
            FROM patients
            """
        ).fetchone()
        active_doctors = self.connection.execute(
            "SELECT COUNT(*) FROM doctors WHERE active = 1"
        ).fetchone()[0]
        today = datetime.now().date().isoformat()
        activity = self.connection.execute(
            """
            SELECT
                SUM(CASE WHEN patient_type = 'Inpatient' THEN 1 ELSE 0 END) AS admissions,
                SUM(CASE WHEN patient_type = 'Outpatient' THEN 1 ELSE 0 END) AS registrations
            FROM patients
            WHERE SUBSTR(created_at, 1, 10) = ?
            """,
            (today,),
        ).fetchone()
        active_specialties = self.connection.execute(
            """
            SELECT COUNT(DISTINCT specialty) FROM patients
            WHERE status NOT IN ('Discharged', 'Visit complete')
            """
        ).fetchone()[0]
        return {
            "total": counts["total"] or 0,
            "inpatients": counts["inpatients"] or 0,
            "outpatients": counts["outpatients"] or 0,
            "waiting": counts["waiting"] or 0,
            "in_consultation": counts["in_consultation"] or 0,
            "urgent": counts["urgent"] or 0,
            "high_priority": counts["high_priority"] or 0,
            "patients_without_bed": counts["patients_without_bed"] or 0,
            "today_admissions": activity["admissions"] or 0,
            "today_outpatients": activity["registrations"] or 0,
            "today_appointments": self.connection.execute(
                """
                SELECT COUNT(*) FROM appointments
                WHERE SUBSTR(appointment_at, 1, 10) = ?
                  AND status NOT IN ('Cancelled', 'No-show')
                """,
                (today,),
            ).fetchone()[0],
            "active_specialties": active_specialties,
            "doctors": active_doctors,
        }

    def sample_case_count(self):
        return self.connection.execute(
            "SELECT COUNT(*) FROM patients WHERE name LIKE 'SAMPLE - %'"
        ).fetchone()[0]

    def close(self):
        self.connection.close()


class HMSApp:
    def __init__(self, root, store=None):
        self.root = root
        self.store = store or HospitalStore()
        self.root.title(APP_NAME)
        self.root.geometry("1360x820")
        self.root.minsize(1040, 680)
        self.root.configure(bg=COLORS["background"])
        self.current_page = "Dashboard"
        self._configure_styles()
        self._build_shell()
        self.show_page("Dashboard")
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=COLORS["white"],
            fieldbackground=COLORS["white"],
            foreground=COLORS["text"],
            rowheight=36,
            borderwidth=0,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background="#F6F8FA",
            foreground=COLORS["muted"],
            relief="flat",
            font=("Segoe UI Semibold", 9),
            padding=(8, 10),
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["teal_light"])],
            foreground=[("selected", COLORS["text"])],
        )
        style.configure(
            "HMS.TCombobox",
            padding=7,
            fieldbackground=COLORS["white"],
            background=COLORS["white"],
        )
        style.configure(
            "HMS.TEntry",
            padding=8,
            fieldbackground=COLORS["white"],
        )
        style.configure(
            "HMS.Horizontal.TProgressbar",
            troughcolor=COLORS["border"],
            background=COLORS["teal"],
            thickness=10,
        )

    def _build_shell(self):
        self.shell = tk.Frame(self.root, bg=COLORS["background"])
        self.shell.pack(fill="both", expand=True)
        self.shell.grid_columnconfigure(1, weight=1)
        self.shell.grid_rowconfigure(0, weight=1)

        self.sidebar = tk.Frame(self.shell, bg=COLORS["navy"], width=230)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)
        tk.Label(
            self.sidebar,
            text="HMS",
            bg=COLORS["navy"],
            fg=COLORS["white"],
            font=("Segoe UI", 23, "bold"),
        ).pack(anchor="w", padx=25, pady=(27, 0))
        tk.Label(
            self.sidebar,
            text="HOSPITAL MANAGEMENT",
            bg=COLORS["navy"],
            fg="#AFC0D0",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=27, pady=(0, 30))

        self.nav_buttons = {}
        for label in ("Dashboard", "Operations", "Appointments", "Patients", "Doctors"):
            button = tk.Button(
                self.sidebar,
                text=f"   {label}",
                anchor="w",
                relief="flat",
                bd=0,
                padx=14,
                pady=12,
                bg=COLORS["navy"],
                fg="#D4DFE9",
                activebackground=COLORS["navy_light"],
                activeforeground=COLORS["white"],
                font=("Segoe UI Semibold", 10),
                command=lambda page=label: self.show_page(page),
            )
            button.pack(fill="x", padx=12, pady=3)
            self.nav_buttons[label] = button

        tk.Frame(self.sidebar, bg="#385169", height=1).pack(fill="x", padx=20, pady=22)
        tk.Label(
            self.sidebar,
            text="PROTOTYPE",
            bg=COLORS["navy"],
            fg="#AFC0D0",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=27)
        tk.Label(
            self.sidebar,
            text="Use fictional data only.\nNot for clinical decisions.",
            justify="left",
            bg=COLORS["navy"],
            fg="#AFC0D0",
            font=("Segoe UI", 8),
        ).pack(anchor="w", padx=27, pady=(7, 0))

        self.main = tk.Frame(self.shell, bg=COLORS["background"])
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self.topbar = tk.Frame(self.main, bg=COLORS["white"], height=76)
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.grid_propagate(False)
        self.page_title = tk.Label(
            self.topbar,
            text="",
            bg=COLORS["white"],
            fg=COLORS["text"],
            font=("Segoe UI Semibold", 17),
        )
        self.page_title.pack(side="left", padx=28, pady=22)
        tk.Label(
            self.topbar,
            text=datetime.now().strftime("%A, %d %B %Y"),
            bg=COLORS["white"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(side="right", padx=28)
        self.content = tk.Frame(self.main, bg=COLORS["background"])
        self.content.grid(row=1, column=0, sticky="nsew")

    def show_page(self, page):
        self.current_page = page
        for child in self.content.winfo_children():
            child.destroy()
        self.page_title.configure(text=page)
        for label, button in self.nav_buttons.items():
            selected = label == page
            button.configure(
                bg=COLORS["navy_light"] if selected else COLORS["navy"],
                fg=COLORS["white"] if selected else "#D4DFE9",
            )
        if page == "Dashboard":
            self._show_dashboard()
        elif page == "Operations":
            self._show_operations()
        elif page == "Appointments":
            self._show_appointments()
        elif page == "Patients":
            self._show_patients()
        else:
            self._show_doctors()

    def _page_intro(self, parent, title, description, button_text=None, command=None):
        row = tk.Frame(parent, bg=COLORS["background"])
        row.pack(fill="x", padx=28, pady=(22, 16))
        copy = tk.Frame(row, bg=COLORS["background"])
        copy.pack(side="left", fill="x", expand=True)
        tk.Label(
            copy, text=title, bg=COLORS["background"], fg=COLORS["text"],
            font=("Segoe UI Semibold", 15),
        ).pack(anchor="w")
        tk.Label(
            copy, text=description, bg=COLORS["background"], fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(4, 0))
        if button_text:
            self._button(row, button_text, command, primary=True).pack(side="right", padx=2)
        return row

    def _button(self, parent, text, command, primary=False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=COLORS["teal"] if primary else COLORS["white"],
            fg=COLORS["white"] if primary else COLORS["text"],
            activebackground=COLORS["navy_light"] if primary else "#F1F4F7",
            activeforeground=COLORS["white"] if primary else COLORS["text"],
            relief="flat",
            bd=0,
            padx=15,
            pady=9,
            cursor="hand2",
            font=("Segoe UI Semibold", 9),
        )

    def _card(self, parent, title, value, note, accent):
        card = tk.Frame(parent, bg=COLORS["white"], highlightbackground=COLORS["border"], highlightthickness=1)
        card.pack(side="left", fill="both", expand=True, padx=(0, 12))
        tk.Frame(card, bg=accent, width=4).pack(side="left", fill="y")
        body = tk.Frame(card, bg=COLORS["white"])
        body.pack(side="left", fill="both", expand=True, padx=15, pady=13)
        tk.Label(body, text=title.upper(), bg=COLORS["white"], fg=COLORS["muted"],
                 font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(body, text=str(value), bg=COLORS["white"], fg=COLORS["text"],
                 font=("Segoe UI Semibold", 23)).pack(anchor="w", pady=(2, 0))
        tk.Label(body, text=note, bg=COLORS["white"], fg=COLORS["muted"],
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(1, 0))
        return card

    def _section(self, parent, title, subtitle=None):
        frame = tk.Frame(parent, bg=COLORS["white"], highlightbackground=COLORS["border"], highlightthickness=1)
        heading = tk.Frame(frame, bg=COLORS["white"])
        heading.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(heading, text=title, bg=COLORS["white"], fg=COLORS["text"],
                 font=("Segoe UI Semibold", 11)).pack(anchor="w")
        if subtitle:
            tk.Label(heading, text=subtitle, bg=COLORS["white"], fg=COLORS["muted"],
                     font=("Segoe UI", 8)).pack(anchor="w", pady=(3, 0))
        return frame

    def _make_tree(self, parent, columns, headings, widths, height=10):
        table_frame = tk.Frame(parent, bg=COLORS["white"])
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=height)
        for column, heading, width in zip(columns, headings, widths):
            tree.heading(column, text=heading)
            tree.column(column, width=width, minwidth=65, anchor="w", stretch=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        tree.tag_configure("urgent", foreground=COLORS["red"])
        tree.tag_configure("high", foreground=COLORS["amber"])
        tree.tag_configure("complete", foreground=COLORS["muted"])
        return tree

    def _show_dashboard(self):
        page = self.content
        counts = self.store.dashboard_counts()
        intro = self._page_intro(
            page,
            "Daily operations overview",
            "A live snapshot of inpatient capacity, outpatient flow and specialty workload.",
            "Register patient",
            self._add_patient_dialog,
        )
        if self.store.sample_case_count() == 0:
            self._button(
                intro, "Add fictional examples", self._load_sample_data
            ).pack(side="right", padx=2)
        if self.store.sample_case_count():
            tk.Label(
                page,
                text="DEMO DATA  |  SAMPLE-prefixed patients are fictional examples. Remove them before entering real records.",
                bg=COLORS["amber_light"],
                fg=COLORS["amber"],
                font=("Segoe UI Semibold", 8),
                anchor="w",
                padx=12,
                pady=7,
            ).pack(fill="x", padx=28, pady=(0, 10))

        capacity = self.store.get_bed_capacity()
        bed_note = f"Configured capacity: {capacity} beds" if capacity else "Configure staffed bed capacity"
        cards = tk.Frame(page, bg=COLORS["background"])
        cards.pack(fill="x", padx=28)
        today_note = (
            f"{counts['today_admissions']} admissions / "
            f"{counts['today_outpatients']} registrations / "
            f"{counts['today_appointments']} appointments"
        )
        self._card(cards, "Inpatient census", counts["inpatients"], bed_note, COLORS["teal"])
        self._card(
            cards, "OPD waiting", counts["waiting"],
            f"{counts['in_consultation']} currently in consultation", "#416D9C",
        )
        self._card(
            cards, "Urgent / high priority", counts["high_priority"],
            "Open workflow flags - staff assigned", COLORS["red"],
        )
        self._card(cards, "Today's activity", today_note, f"{counts['doctors']} active doctors", "#8067A9")

        main_row = tk.Frame(page, bg=COLORS["background"])
        main_row.pack(fill="both", expand=True, padx=28, pady=(14, 8))
        bed_panel = self._section(
            main_row,
            "Inpatient bed census",
            "Active admissions and recorded bed / room assignments.",
        )
        bed_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
        opd_panel = self._section(
            main_row,
            "Outpatient flow",
            "Open queue ordered by staff-entered priority, then registration time.",
        )
        opd_panel.pack(side="left", fill="both", expand=True, padx=(8, 0))

        capacity_row = tk.Frame(bed_panel, bg=COLORS["white"])
        capacity_row.pack(fill="x", padx=14, pady=(0, 8))
        occupancy_text = (
            f"{counts['inpatients']} of {capacity} beds occupied"
            if capacity else f"{counts['inpatients']} inpatients - capacity not configured"
        )
        tk.Label(
            capacity_row, text=occupancy_text, bg=COLORS["white"], fg=COLORS["text"],
            font=("Segoe UI Semibold", 9),
        ).pack(side="left")
        self._button(capacity_row, "Set capacity", self._configure_bed_capacity).pack(side="right")
        if capacity:
            progress = ttk.Progressbar(
                bed_panel, maximum=capacity, value=min(counts["inpatients"], capacity),
                mode="determinate", style="HMS.Horizontal.TProgressbar",
            )
            progress.pack(fill="x", padx=14, pady=(0, 6))
            percent = round(counts["inpatients"] * 100 / capacity)
            tk.Label(
                bed_panel, text=f"{percent}% of configured capacity", bg=COLORS["white"],
                fg=COLORS["muted"], font=("Segoe UI", 8),
            ).pack(anchor="w", padx=14, pady=(0, 5))
        if counts["patients_without_bed"]:
            tk.Label(
                bed_panel,
                text=f"Action: {counts['patients_without_bed']} inpatient record(s) have no bed / room entered.",
                bg=COLORS["amber_light"], fg=COLORS["amber"],
                font=("Segoe UI Semibold", 8), anchor="w", padx=8, pady=5,
            ).pack(fill="x", padx=12, pady=(0, 6))

        inpatient_tree = self._make_tree(
            bed_panel, ("id", "patient", "bed", "specialty", "priority"),
            ("ID", "PATIENT", "BED / ROOM", "SPECIALTY", "PRIORITY"),
            (85, 145, 105, 140, 80), height=4,
        )
        for patient in self.store.list_active_inpatients()[:5]:
            inpatient_tree.insert(
                "", "end", iid=f"bed-{patient['id']}",
                values=(
                    patient["id"], patient["name"], patient["bed"] or "Not assigned",
                    patient["specialty"], patient["priority"],
                ),
                tags=(patient["priority"].lower(),),
            )

        opd_tree = self._make_tree(
            opd_panel, ("id", "patient", "specialty", "priority", "status", "age"),
            ("ID", "PATIENT", "SPECIALTY", "PRIORITY", "STATUS", "REGISTERED"),
            (75, 135, 125, 75, 110, 105), height=5,
        )
        for patient in self.store.list_outpatient_queue()[:6]:
            opd_tree.insert(
                "", "end", iid=f"opd-{patient['id']}",
                values=(
                    patient["id"], patient["name"], patient["specialty"],
                    patient["priority"], patient["status"],
                    self._registration_age(patient["created_at"]),
                ),
                tags=(patient["priority"].lower(),),
            )

        workload_panel = self._section(
            page,
            "Active specialty workload",
            "Open records by specialty. This is an administrative count, not a staffing recommendation.",
        )
        workload_panel.pack(fill="x", padx=28, pady=(0, 8))
        workload_tree = self._make_tree(
            workload_panel, ("specialty", "cases", "doctors"),
            ("SPECIALTY", "OPEN PATIENT RECORDS", "ASSIGNED DOCTORS"),
            (240, 190, 190), height=3,
        )
        for item in self.store.specialty_workload()[:4]:
            workload_tree.insert(
                "", "end",
                values=(item["specialty"], item["active_cases"], item["assigned_doctors"]),
            )

        tk.Label(
            page,
            text="Operational prototype only - no live clinical systems or triage decisions are represented.",
            bg=COLORS["background"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
        ).pack(anchor="w", padx=30, pady=(0, 8))

    def _show_appointments(self):
        page = self.content
        self._page_intro(
            page,
            "Outpatient appointment desk",
            "Schedule specialty visits, prevent booking conflicts and track check-in through completion.",
            "+  Book appointment",
            self._add_appointment_dialog,
        )
        filters = tk.Frame(
            page, bg=COLORS["white"],
            highlightbackground=COLORS["border"], highlightthickness=1,
        )
        filters.pack(fill="x", padx=28, pady=(0, 12))
        filter_row = tk.Frame(filters, bg=COLORS["white"])
        filter_row.pack(fill="x", padx=14, pady=10)
        tk.Label(
            filter_row, text="APPOINTMENT DATE", bg=COLORS["white"],
            fg=COLORS["muted"], font=("Segoe UI Semibold", 8),
        ).pack(side="left", padx=(0, 8))
        self.appointment_date_filter = tk.StringVar(value=date.today().isoformat())
        date_entry = ttk.Entry(
            filter_row, textvariable=self.appointment_date_filter,
            style="HMS.TEntry", width=14,
        )
        date_entry.pack(side="left", padx=(0, 8))
        date_entry.bind("<Return>", lambda _event: self._refresh_appointments())
        self._button(filter_row, "Show schedule", self._refresh_appointments).pack(side="left")
        self._button(
            filter_row, "Today",
            lambda: self._set_appointment_date(date.today().isoformat()),
        ).pack(side="left", padx=(8, 0))
        if not self.store.sample_appointment_count():
            self._button(
                filter_row, "Load fictional examples", self._load_sample_data,
            ).pack(side="right")

        schedule = self._section(
            page,
            "Clinic schedule",
            "Select a visit and update its workflow state. Appointment history is retained.",
        )
        schedule.pack(fill="both", expand=True, padx=28, pady=(0, 8))
        actions = tk.Frame(schedule, bg=COLORS["white"])
        actions.pack(fill="x", padx=12, pady=(0, 8))
        self._button(
            actions, "Update selected appointment",
            self._update_appointment_status,
        ).pack(side="right")
        self.appointment_tree = self._make_tree(
            schedule,
            ("number", "time", "patient", "specialty", "doctor", "duration", "reason", "status"),
            ("APPOINTMENT", "TIME", "PATIENT", "SPECIALTY", "DOCTOR", "MIN", "VISIT TYPE", "STATUS"),
            (100, 75, 145, 145, 140, 55, 175, 115),
            height=14,
        )
        self._refresh_appointments()
        tk.Label(
            page,
            text="Appointments are administrative records. Confirm availability directly with the clinic; no SMS, billing, or clinical record is generated.",
            bg=COLORS["background"], fg=COLORS["muted"], font=("Segoe UI", 8),
        ).pack(anchor="w", padx=30, pady=(0, 8))

    def _set_appointment_date(self, value):
        self.appointment_date_filter.set(value)
        self._refresh_appointments()

    def _refresh_appointments(self):
        if not hasattr(self, "appointment_tree") or not self.appointment_tree.winfo_exists():
            return
        try:
            rows = self.store.list_appointments(self.appointment_date_filter.get().strip())
        except ValueError as error:
            messagebox.showerror("Invalid appointment date", str(error))
            return
        for item in self.appointment_tree.get_children():
            self.appointment_tree.delete(item)
        for appointment in rows:
            appointment_time = datetime.fromisoformat(appointment["appointment_at"])
            tag = {
                "Cancelled": "complete",
                "No-show": "complete",
                "Completed": "complete",
            }.get(appointment["status"], "")
            self.appointment_tree.insert(
                "", "end", iid=str(appointment["id"]),
                values=(
                    appointment["appointment_number"],
                    appointment_time.strftime("%H:%M"),
                    appointment["patient_name"],
                    appointment["specialty"],
                    appointment["doctor_name"],
                    appointment["duration_minutes"],
                    appointment["reason"],
                    appointment["status"],
                ),
                tags=(tag,) if tag else (),
            )

    def _load_sample_data(self):
        if self.store.sample_case_count():
            if self.store.sample_appointment_count():
                messagebox.showinfo(
                    "Examples already loaded",
                    "Fictional sample patients and appointments are already in the local database.",
                )
                return
            action = self.store.load_demo_appointments
        else:
            action = self.store.load_demo_data

        confirmed = messagebox.askyesno(
            "Add fictional examples",
            "Add clearly labeled SAMPLE patient and outpatient appointment records to this local prototype?\n\n"
            "Existing patient and appointment records will not be changed. Do not use sample data for care decisions.",
        )
        if not confirmed:
            return
        try:
            action()
        except (sqlite3.Error, ValueError) as error:
            messagebox.showerror("Unable to load examples", str(error))
            return
        if self.current_page == "Appointments":
            sample_date = self.store.sample_appointment_date()
            self.appointment_date_filter.set(sample_date or date.today().isoformat())
            self._refresh_appointments()
        else:
            self.show_page("Dashboard")
        messagebox.showinfo(
            "Fictional examples added",
            "Sample patients and specialty appointments have been added. Each example patient name begins with SAMPLE.",
        )

    @staticmethod
    def _registration_age(created_at):
        registered = datetime.fromisoformat(created_at)
        minutes = max(0, int((datetime.now() - registered).total_seconds() // 60))
        if minutes < 60:
            return f"{minutes} min"
        hours, remainder = divmod(minutes, 60)
        return f"{hours}h {remainder}m"

    def _show_operations(self):
        page = self.content
        self._page_intro(
            page,
            "Patient flow and capacity",
            "Review inpatient bed assignments and progress the outpatient work queue.",
            "Set bed capacity",
            self._configure_bed_capacity,
        )
        counts = self.store.dashboard_counts()
        capacity = self.store.get_bed_capacity()
        snapshot = tk.Frame(page, bg=COLORS["white"], highlightbackground=COLORS["border"], highlightthickness=1)
        snapshot.pack(fill="x", padx=28, pady=(0, 12))
        snapshot_text = (
            f"Inpatient census: {counts['inpatients']} / {capacity} beds"
            if capacity else f"Inpatient census: {counts['inpatients']} | Bed capacity not configured"
        )
        tk.Label(
            snapshot, text=snapshot_text, bg=COLORS["white"], fg=COLORS["text"],
            font=("Segoe UI Semibold", 10),
        ).pack(side="left", padx=15, pady=12)
        tk.Label(
            snapshot,
            text=f"OPD waiting: {counts['waiting']}   |   In consultation: {counts['in_consultation']}   |   Unassigned beds: {counts['patients_without_bed']}",
            bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 9),
        ).pack(side="right", padx=15)

        tables = tk.Frame(page, bg=COLORS["background"])
        tables.pack(fill="both", expand=True, padx=28, pady=(0, 18))
        tables.grid_columnconfigure(0, weight=1)
        tables.grid_columnconfigure(1, weight=1)
        tables.grid_rowconfigure(0, weight=1)

        inpatient_panel = self._section(
            tables, "Inpatient census", "Update status to Discharged to close an admission.",
        )
        inpatient_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        inpatient_actions = tk.Frame(inpatient_panel, bg=COLORS["white"])
        inpatient_actions.pack(fill="x", padx=12, pady=(0, 8))
        self._button(
            inpatient_actions, "Update selected status",
            lambda: self._update_operation_status(self.inpatient_tree),
        ).pack(side="right")
        self._button(
            inpatient_actions, "Assign / change bed",
            lambda: self._edit_selected_bed(self.inpatient_tree),
        ).pack(side="right", padx=(0, 8))
        self.inpatient_tree = self._make_tree(
            inpatient_panel,
            ("id", "patient", "bed", "specialty", "doctor", "priority", "status"),
            ("ID", "PATIENT", "BED / ROOM", "SPECIALTY", "DOCTOR", "PRIORITY", "STATUS"),
            (80, 120, 95, 120, 115, 75, 95), height=12,
        )
        for patient in self.store.list_active_inpatients():
            self.inpatient_tree.insert(
                "", "end", iid=patient["id"],
                values=(
                    patient["id"], patient["name"], patient["bed"] or "Not assigned",
                    patient["specialty"], patient["doctor_name"],
                    patient["priority"], patient["status"],
                ),
                tags=(patient["priority"].lower(),),
            )

        outpatient_panel = self._section(
            tables, "Outpatient queue", "Registration age is shown; it is not a measured clinical wait time.",
        )
        outpatient_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        outpatient_actions = tk.Frame(outpatient_panel, bg=COLORS["white"])
        outpatient_actions.pack(fill="x", padx=12, pady=(0, 8))
        self._button(
            outpatient_actions, "Update selected status",
            lambda: self._update_operation_status(self.outpatient_tree),
        ).pack(side="right")
        self.outpatient_tree = self._make_tree(
            outpatient_panel,
            ("id", "patient", "specialty", "doctor", "priority", "status", "age"),
            ("ID", "PATIENT", "SPECIALTY", "DOCTOR", "PRIORITY", "STATUS", "REGISTERED"),
            (75, 110, 105, 105, 75, 105, 85), height=12,
        )
        for patient in self.store.list_outpatient_queue():
            self.outpatient_tree.insert(
                "", "end", iid=patient["id"],
                values=(
                    patient["id"], patient["name"], patient["specialty"],
                    patient["doctor_name"], patient["priority"], patient["status"],
                    self._registration_age(patient["created_at"]),
                ),
                tags=(patient["priority"].lower(),),
            )

    def _show_patients(self):
        page = self.content
        self._page_intro(
            page,
            "Patient coordination",
            "Separate inpatient and outpatient workflows, with staff-entered priority.",
            "+  Add patient",
            self._add_patient_dialog,
        )

        filters = tk.Frame(page, bg=COLORS["white"], highlightbackground=COLORS["border"], highlightthickness=1)
        filters.pack(fill="x", padx=28, pady=(0, 12))
        filters_inner = tk.Frame(filters, bg=COLORS["white"])
        filters_inner.pack(fill="x", padx=14, pady=12)
        self.patient_type_filter = tk.StringVar(value="All patient types")
        self.priority_filter = tk.StringVar(value="All priorities")
        self.patient_search = tk.StringVar()
        ttk.Combobox(
            filters_inner, textvariable=self.patient_type_filter,
            values=("All patient types",) + PATIENT_TYPES, state="readonly",
            width=18, style="HMS.TCombobox",
        ).pack(side="left", padx=(0, 8))
        ttk.Combobox(
            filters_inner, textvariable=self.priority_filter,
            values=("All priorities",) + PRIORITIES, state="readonly",
            width=16, style="HMS.TCombobox",
        ).pack(side="left", padx=(0, 8))
        search = ttk.Entry(filters_inner, textvariable=self.patient_search, style="HMS.TEntry", width=28)
        search.pack(side="left", padx=(0, 8))
        search.insert(0, "")
        search.bind("<Return>", lambda _event: self._refresh_patients())
        self._button(filters_inner, "Search", self._refresh_patients).pack(side="left")
        self._button(filters_inner, "Update status", self._update_patient_status).pack(side="right")
        self.patient_type_filter.trace_add("write", lambda *_args: self._refresh_patients())
        self.priority_filter.trace_add("write", lambda *_args: self._refresh_patients())

        listing = self._section(page, "Patient register", "Select a patient before updating the care status.")
        listing.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        self.patient_tree = self._make_tree(
            listing,
            ("id", "patient", "age", "type", "specialty", "doctor", "priority", "status", "bed"),
            ("PATIENT ID", "PATIENT", "AGE", "CARE TYPE", "SPECIALTY", "ASSIGNED DOCTOR", "PRIORITY", "STATUS", "BED / ROOM"),
            (100, 145, 55, 100, 150, 145, 85, 125, 90),
            height=12,
        )
        self._refresh_patients()

    def _refresh_patients(self):
        if not hasattr(self, "patient_tree") or not self.patient_tree.winfo_exists():
            return
        for item in self.patient_tree.get_children():
            self.patient_tree.delete(item)
        rows = self.store.list_patients(
            patient_type=self.patient_type_filter.get(),
            priority=self.priority_filter.get(),
            search=self.patient_search.get(),
        )
        for patient in rows:
            tag = patient["priority"].lower()
            if patient["status"] in ("Discharged", "Visit complete"):
                tag = "complete"
            self.patient_tree.insert(
                "", "end", iid=patient["id"],
                values=(
                    patient["id"], patient["name"], patient["age"],
                    patient["patient_type"], patient["specialty"],
                    patient["doctor_name"], patient["priority"], patient["status"],
                    patient["bed"] or "--",
                ),
                tags=(tag,),
            )

    def _show_doctors(self):
        page = self.content
        self._page_intro(
            page,
            "Specialty directory",
            "Fictional example roster - replace with the verified hospital directory before use.",
            "+  Add doctor",
            self._add_doctor_dialog,
        )
        toolbar = tk.Frame(page, bg=COLORS["background"])
        toolbar.pack(fill="x", padx=28, pady=(0, 12))
        tk.Label(
            toolbar, text="SPECIALTY", bg=COLORS["background"], fg=COLORS["muted"],
            font=("Segoe UI Semibold", 8),
        ).pack(side="left", padx=(0, 8))
        self.doctor_specialty_filter = tk.StringVar(value="All specialties")
        selector = ttk.Combobox(
            toolbar,
            textvariable=self.doctor_specialty_filter,
            values=("All specialties",) + SPECIALTIES,
            state="readonly",
            width=28,
            style="HMS.TCombobox",
        )
        selector.pack(side="left")
        selector.bind("<<ComboboxSelected>>", lambda _event: self._refresh_doctors())

        directory = self._section(page, "Doctors and specialty coverage")
        directory.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        self.doctor_tree = self._make_tree(
            directory,
            ("doctor", "specialty", "credentials", "clinic", "extension", "patients"),
            ("DOCTOR", "SPECIALTY", "QUALIFICATIONS", "CLINIC / UNIT", "EXTENSION", "ACTIVE CASES"),
            (175, 175, 140, 190, 90, 100),
            height=14,
        )
        self._refresh_doctors()

    def _refresh_doctors(self):
        if not hasattr(self, "doctor_tree") or not self.doctor_tree.winfo_exists():
            return
        for item in self.doctor_tree.get_children():
            self.doctor_tree.delete(item)
        for doctor in self.store.list_doctors(self.doctor_specialty_filter.get()):
            self.doctor_tree.insert(
                "", "end", iid=str(doctor["id"]),
                values=(
                    doctor["name"], doctor["specialty"], doctor["credentials"],
                    doctor["clinic"], doctor["extension"], doctor["active_patients"],
                ),
            )

    def _dialog(self, title, width=520, height=680):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=COLORS["background"])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.geometry(f"{width}x{height}")
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + max((self.root.winfo_width() - width) // 2, 0)
        y = self.root.winfo_rooty() + max((self.root.winfo_height() - height) // 2, 0)
        dialog.geometry(f"+{x}+{y}")
        return dialog

    def _configure_bed_capacity(self):
        dialog = self._dialog("HMS | Configure bed capacity", width=450, height=340)
        panel = tk.Frame(dialog, bg=COLORS["white"])
        panel.pack(fill="both", expand=True, padx=15, pady=15)
        tk.Label(
            panel, text="Configure inpatient capacity", bg=COLORS["white"],
            fg=COLORS["text"], font=("Segoe UI Semibold", 15),
        ).pack(anchor="w", padx=20, pady=(20, 5))
        current_census = len(self.store.list_active_inpatients())
        tk.Label(
            panel,
            text=f"Enter the hospital's total staffed inpatient beds. Current census: {current_census}.\n"
                 "Use 0 only to clear capacity when no inpatients are active.",
            bg=COLORS["white"], fg=COLORS["muted"], justify="left",
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=20, pady=(0, 12))
        capacity = tk.StringVar(value=str(self.store.get_bed_capacity()))
        self._form_label(panel, "Total staffed beds")
        capacity_entry = ttk.Entry(panel, textvariable=capacity, style="HMS.TEntry")
        capacity_entry.pack(fill="x", padx=20)

        def save():
            try:
                value = int(capacity.get())
                self.store.set_bed_capacity(value)
            except ValueError as error:
                messagebox.showerror("Invalid capacity", str(error), parent=dialog)
                return
            except sqlite3.Error as error:
                messagebox.showerror("Unable to save capacity", str(error), parent=dialog)
                return
            dialog.destroy()
            self.show_page(self.current_page)

        actions = tk.Frame(panel, bg=COLORS["white"])
        actions.pack(fill="x", padx=20, pady=20)
        self._button(actions, "Cancel", dialog.destroy).pack(side="right", padx=(8, 0))
        self._button(actions, "Save capacity", save, primary=True).pack(side="right")
        capacity_entry.focus_set()

    def _add_appointment_dialog(self):
        patients = self.store.list_patients(patient_type="Outpatient")
        if not patients:
            messagebox.showinfo(
                "Outpatient record required",
                "Register an outpatient in the Patient Register before booking an appointment.",
            )
            return

        dialog = self._dialog("HMS | Book outpatient appointment", width=590, height=720)
        panel = tk.Frame(dialog, bg=COLORS["white"])
        panel.pack(fill="both", expand=True, padx=15, pady=15)
        tk.Label(
            panel, text="Book outpatient appointment", bg=COLORS["white"],
            fg=COLORS["text"], font=("Segoe UI Semibold", 16),
        ).pack(anchor="w", padx=20, pady=(18, 3))
        tk.Label(
            panel,
            text="Select a registered outpatient. Active doctor and time-slot conflicts are checked before saving.",
            bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 8),
        ).pack(anchor="w", padx=20, pady=(0, 8))
        form = tk.Frame(panel, bg=COLORS["white"])
        form.pack(fill="both", expand=True, padx=20)

        patient_options = {
            f"{patient['id']}  -  {patient['name']}  -  {patient['specialty']}": patient
            for patient in patients
        }
        patient = tk.StringVar(value=next(iter(patient_options), ""))
        doctor = tk.StringVar()
        doctor_options = {}
        appointment_date = tk.StringVar(value=date.today().isoformat())
        first_slot = datetime.now() + timedelta(minutes=30)
        first_slot = first_slot.replace(second=0, microsecond=0)
        remainder = first_slot.minute % 15
        if remainder:
            first_slot += timedelta(minutes=15 - remainder)
        appointment_time = tk.StringVar(value=first_slot.strftime("%H:%M"))
        duration = tk.StringVar(value="30")
        reason = tk.StringVar(value="Initial consultation")

        self._form_label(form, "Outpatient *")
        patient_selector = ttk.Combobox(
            form, textvariable=patient, values=tuple(patient_options),
            state="readonly", style="HMS.TCombobox",
        )
        patient_selector.pack(fill="x")

        self._form_label(form, "Assigned specialist *")
        doctor_selector = ttk.Combobox(
            form, textvariable=doctor, state="readonly", style="HMS.TCombobox",
        )
        doctor_selector.pack(fill="x")

        date_time_row = tk.Frame(form, bg=COLORS["white"])
        date_time_row.pack(fill="x")
        date_column = tk.Frame(date_time_row, bg=COLORS["white"])
        date_column.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._form_label(date_column, "Date (YYYY-MM-DD) *")
        ttk.Entry(date_column, textvariable=appointment_date, style="HMS.TEntry").pack(fill="x")
        time_column = tk.Frame(date_time_row, bg=COLORS["white"])
        time_column.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self._form_label(time_column, "Start time (24-hour HH:MM) *")
        ttk.Entry(time_column, textvariable=appointment_time, style="HMS.TEntry").pack(fill="x")

        duration_reason_row = tk.Frame(form, bg=COLORS["white"])
        duration_reason_row.pack(fill="x")
        duration_column = tk.Frame(duration_reason_row, bg=COLORS["white"])
        duration_column.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._form_label(duration_column, "Slot duration (minutes)")
        ttk.Combobox(
            duration_column, textvariable=duration, values=("15", "30", "45", "60"),
            state="readonly", style="HMS.TCombobox",
        ).pack(fill="x")
        reason_column = tk.Frame(duration_reason_row, bg=COLORS["white"])
        reason_column.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self._form_label(reason_column, "Visit type / reason")
        ttk.Combobox(
            reason_column, textvariable=reason,
            values=("Initial consultation", "Follow-up", "Review", "Diagnostic discussion"),
            style="HMS.TCombobox",
        ).pack(fill="x")

        tk.Label(
            form,
            text="Scheduling aid only: this screen does not confirm clinician availability, room readiness, or clinical urgency.",
            bg=COLORS["white"], fg=COLORS["muted"], wraplength=500, justify="left",
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(14, 0))

        def update_doctors(*_args):
            selected_patient = patient_options.get(patient.get())
            doctor_options.clear()
            if selected_patient:
                available = self.store.list_doctors(selected_patient["specialty"])
                doctor_options.update({
                    f"{item['name']}  -  {item['clinic']}": item["id"]
                    for item in available
                })
            doctor_selector.configure(values=tuple(doctor_options))
            doctor.set(next(iter(doctor_options), ""))

        patient_selector.bind("<<ComboboxSelected>>", update_doctors)
        update_doctors()

        def save():
            selected_patient = patient_options.get(patient.get())
            selected_doctor = doctor_options.get(doctor.get())
            if not selected_patient or selected_doctor is None:
                messagebox.showerror("Required fields", "Select an outpatient and active doctor.", parent=dialog)
                return
            try:
                parsed_date = date.fromisoformat(appointment_date.get().strip())
                parsed_time = datetime.strptime(appointment_time.get().strip(), "%H:%M").time()
                starts_at = datetime.combine(parsed_date, parsed_time)
                appointment_id = self.store.add_appointment(
                    selected_patient["id"],
                    selected_doctor,
                    starts_at.isoformat(timespec="minutes"),
                    int(duration.get()),
                    reason.get(),
                )
            except (ValueError, sqlite3.Error) as error:
                messagebox.showerror("Unable to book appointment", str(error), parent=dialog)
                return
            dialog.destroy()
            self.show_page("Appointments")
            self.appointment_date_filter.set(parsed_date.isoformat())
            self._refresh_appointments()
            messagebox.showinfo(
                "Appointment booked",
                f"Appointment APT-{appointment_id:04d} has been scheduled.",
            )

        actions = tk.Frame(panel, bg=COLORS["white"])
        actions.pack(fill="x", padx=20, pady=(10, 18))
        self._button(actions, "Cancel", dialog.destroy).pack(side="right", padx=(8, 0))
        self._button(actions, "Book appointment", save, primary=True).pack(side="right")
        patient_selector.focus_set()

    def _update_appointment_status(self):
        selection = self.appointment_tree.selection()
        if not selection:
            messagebox.showinfo(
                "Select an appointment",
                "Select an appointment from the schedule before changing its status.",
            )
            return
        appointment_id = int(selection[0])
        appointment = self.store.connection.execute(
            """
            SELECT a.status, a.appointment_at, p.name AS patient_name,
                   printf('APT-%04d', a.id) AS appointment_number
            FROM appointments AS a
            JOIN patients AS p ON p.id = a.patient_id
            WHERE a.id = ?
            """,
            (appointment_id,),
        ).fetchone()
        if appointment is None:
            messagebox.showerror("Appointment not found", "Refresh the schedule and try again.")
            self._refresh_appointments()
            return
        allowed = APPOINTMENT_TRANSITIONS[appointment["status"]]
        if not allowed:
            messagebox.showinfo(
                "Appointment closed",
                f"{appointment['appointment_number']} is already {appointment['status'].lower()}.",
            )
            return

        dialog = self._dialog("HMS | Update appointment", width=460, height=390)
        panel = tk.Frame(dialog, bg=COLORS["white"])
        panel.pack(fill="both", expand=True, padx=15, pady=15)
        appointment_time = datetime.fromisoformat(appointment["appointment_at"]).strftime("%d %b %Y, %H:%M")
        tk.Label(
            panel, text="Update appointment status", bg=COLORS["white"],
            fg=COLORS["text"], font=("Segoe UI Semibold", 15),
        ).pack(anchor="w", padx=20, pady=(20, 5))
        tk.Label(
            panel,
            text=f"{appointment['appointment_number']}  -  {appointment['patient_name']}\n{appointment_time}",
            bg=COLORS["white"], fg=COLORS["muted"], justify="left",
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=20, pady=(0, 12))
        next_status = tk.StringVar(value=allowed[0])
        self._form_label(panel, f"Current status: {appointment['status']}")
        ttk.Combobox(
            panel, textvariable=next_status, values=allowed,
            state="readonly", style="HMS.TCombobox",
        ).pack(fill="x", padx=20)

        def save():
            try:
                self.store.update_appointment_status(appointment_id, next_status.get())
            except (ValueError, sqlite3.Error) as error:
                messagebox.showerror("Unable to update appointment", str(error), parent=dialog)
                return
            dialog.destroy()
            self._refresh_appointments()

        actions = tk.Frame(panel, bg=COLORS["white"])
        actions.pack(fill="x", padx=20, pady=20)
        self._button(actions, "Cancel", dialog.destroy).pack(side="right", padx=(8, 0))
        self._button(actions, "Save status", save, primary=True).pack(side="right")

    def _form_label(self, parent, text):
        tk.Label(
            parent, text=text.upper(), bg=COLORS["white"], fg=COLORS["muted"],
            font=("Segoe UI Semibold", 8),
        ).pack(anchor="w", pady=(10, 4))

    def _add_patient_dialog(self):
        dialog = self._dialog("HMS | Register patient")
        panel = tk.Frame(dialog, bg=COLORS["white"])
        panel.pack(fill="both", expand=True, padx=15, pady=15)
        tk.Label(panel, text="Register patient", bg=COLORS["white"], fg=COLORS["text"],
                 font=("Segoe UI Semibold", 16)).pack(anchor="w", padx=20, pady=(18, 2))
        tk.Label(
            panel,
            text="Priority is entered by staff. Follow your hospital's triage protocol.",
            bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 8),
        ).pack(anchor="w", padx=20, pady=(0, 8))
        form = tk.Frame(panel, bg=COLORS["white"])
        form.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        name = tk.StringVar()
        age = tk.StringVar()
        sex = tk.StringVar(value="Not specified")
        contact = tk.StringVar()
        patient_type = tk.StringVar(value="Outpatient")
        specialty = tk.StringVar(value=SPECIALTIES[0])
        doctor = tk.StringVar()
        priority = tk.StringVar(value="Routine")
        bed = tk.StringVar()
        doctor_options = {}

        self._form_label(form, "Patient name *")
        name_entry = ttk.Entry(form, textvariable=name, style="HMS.TEntry")
        name_entry.pack(fill="x")

        row = tk.Frame(form, bg=COLORS["white"])
        row.pack(fill="x")
        age_column = tk.Frame(row, bg=COLORS["white"])
        age_column.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._form_label(age_column, "Age *")
        ttk.Entry(age_column, textvariable=age, style="HMS.TEntry").pack(fill="x")
        sex_column = tk.Frame(row, bg=COLORS["white"])
        sex_column.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self._form_label(sex_column, "Sex")
        ttk.Combobox(
            sex_column, textvariable=sex,
            values=("Not specified", "Female", "Male", "Other"),
            state="readonly", style="HMS.TCombobox",
        ).pack(fill="x")

        self._form_label(form, "Contact number")
        ttk.Entry(form, textvariable=contact, style="HMS.TEntry").pack(fill="x")

        row = tk.Frame(form, bg=COLORS["white"])
        row.pack(fill="x")
        type_column = tk.Frame(row, bg=COLORS["white"])
        type_column.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._form_label(type_column, "Care type *")
        type_selector = ttk.Combobox(
            type_column, textvariable=patient_type, values=PATIENT_TYPES,
            state="readonly", style="HMS.TCombobox",
        )
        type_selector.pack(fill="x")
        priority_column = tk.Frame(row, bg=COLORS["white"])
        priority_column.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self._form_label(priority_column, "Workflow priority *")
        ttk.Combobox(
            priority_column, textvariable=priority, values=PRIORITIES,
            state="readonly", style="HMS.TCombobox",
        ).pack(fill="x")

        self._form_label(form, "Specialty / department *")
        specialty_selector = ttk.Combobox(
            form, textvariable=specialty, values=SPECIALTIES,
            state="readonly", style="HMS.TCombobox",
        )
        specialty_selector.pack(fill="x")

        self._form_label(form, "Assigned doctor *")
        doctor_selector = ttk.Combobox(
            form, textvariable=doctor, state="readonly", style="HMS.TCombobox",
        )
        doctor_selector.pack(fill="x")

        self._form_label(form, "Bed / room (for inpatients)")
        bed_entry = ttk.Entry(form, textvariable=bed, style="HMS.TEntry")
        bed_entry.pack(fill="x")

        def update_doctors(*_args):
            available = self.store.list_doctors(specialty.get())
            doctor_options.clear()
            doctor_options.update({f"{item['name']}  -  {item['clinic']}": item["id"] for item in available})
            doctor_selector.configure(values=tuple(doctor_options))
            doctor.set(next(iter(doctor_options), ""))

        specialty_selector.bind("<<ComboboxSelected>>", update_doctors)
        update_doctors()

        def save():
            patient_name = name.get().strip()
            if not patient_name:
                messagebox.showerror("Required field", "Enter the patient's name.", parent=dialog)
                name_entry.focus_set()
                return
            try:
                patient_age = int(age.get())
                if not 0 <= patient_age <= 120:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid age", "Enter an age from 0 to 120.", parent=dialog)
                return
            if not doctor.get() or doctor.get() not in doctor_options:
                messagebox.showerror(
                    "Doctor required",
                    "No active doctor is listed for this specialty. Add an appropriate doctor first.",
                    parent=dialog,
                )
                return
            try:
                patient_id = self.store.add_patient(
                    patient_name, patient_age, sex.get(), contact.get(),
                    patient_type.get(), specialty.get(), doctor_options[doctor.get()],
                    priority.get(), bed.get(),
                )
            except (sqlite3.Error, ValueError) as error:
                messagebox.showerror("Unable to save patient", str(error), parent=dialog)
                return
            dialog.destroy()
            self.show_page("Patients")
            messagebox.showinfo("Patient registered", f"Record {patient_id} has been added.")

        actions = tk.Frame(panel, bg=COLORS["white"])
        actions.pack(fill="x", padx=20, pady=(0, 18))
        self._button(actions, "Cancel", dialog.destroy).pack(side="right", padx=(8, 0))
        self._button(actions, "Save patient", save, primary=True).pack(side="right")
        name_entry.focus_set()
        type_selector.bind(
            "<<ComboboxSelected>>",
            lambda _event: bed_entry.configure(
                state="normal" if patient_type.get() == "Inpatient" else "disabled"
            ),
        )
        bed_entry.configure(state="disabled")

    def _add_doctor_dialog(self):
        dialog = self._dialog("HMS | Add doctor", width=500)
        panel = tk.Frame(dialog, bg=COLORS["white"])
        panel.pack(fill="both", expand=True, padx=15, pady=15)
        tk.Label(panel, text="Add doctor to directory", bg=COLORS["white"],
                 fg=COLORS["text"], font=("Segoe UI Semibold", 16)).pack(
                     anchor="w", padx=20, pady=(18, 12)
                 )
        form = tk.Frame(panel, bg=COLORS["white"])
        form.pack(fill="both", expand=True, padx=20)
        name = tk.StringVar()
        specialty = tk.StringVar(value=SPECIALTIES[0])
        credentials = tk.StringVar()
        clinic = tk.StringVar()
        extension = tk.StringVar()
        fields = (
            ("Doctor name *", name, "entry"),
            ("Specialty *", specialty, "specialty"),
            ("Qualifications", credentials, "entry"),
            ("Clinic / unit", clinic, "entry"),
            ("Phone extension", extension, "entry"),
        )
        name_entry = None
        for label, variable, kind in fields:
            self._form_label(form, label)
            if kind == "specialty":
                ttk.Combobox(
                    form, textvariable=variable, values=SPECIALTIES,
                    state="readonly", style="HMS.TCombobox",
                ).pack(fill="x")
            else:
                entry = ttk.Entry(form, textvariable=variable, style="HMS.TEntry")
                entry.pack(fill="x")
                if label.startswith("Doctor name"):
                    name_entry = entry

        def save():
            if not name.get().strip():
                messagebox.showerror("Required field", "Enter the doctor's name.", parent=dialog)
                name_entry.focus_set()
                return
            try:
                self.store.add_doctor(
                    name.get(), specialty.get(), credentials.get(), clinic.get(), extension.get()
                )
            except sqlite3.Error as error:
                messagebox.showerror("Unable to save doctor", str(error), parent=dialog)
                return
            dialog.destroy()
            self.show_page("Doctors")
            messagebox.showinfo("Doctor added", "The specialty directory has been updated.")

        actions = tk.Frame(panel, bg=COLORS["white"])
        actions.pack(fill="x", padx=20, pady=(12, 18))
        self._button(actions, "Cancel", dialog.destroy).pack(side="right", padx=(8, 0))
        self._button(actions, "Save doctor", save, primary=True).pack(side="right")
        name_entry.focus_set()

    def _update_patient_status(self):
        selected = self.patient_tree.selection()
        if not selected:
            messagebox.showinfo("Select a patient", "Select a patient record before updating its status.")
            return
        self._update_patient_status_for_id(selected[0])

    def _update_operation_status(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("Select a patient", "Select a patient record before updating its status.")
            return
        self._update_patient_status_for_id(selected[0])

    def _edit_selected_bed(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("Select an inpatient", "Select an active inpatient before assigning a bed.")
            return
        self._edit_patient_bed(selected[0])

    def _edit_patient_bed(self, patient_id):
        patient = self.store.connection.execute(
            "SELECT name, patient_type, status, bed FROM patients WHERE id = ?",
            (patient_id,),
        ).fetchone()
        if patient is None:
            messagebox.showerror("Patient not found", "Refresh the census and try again.")
            return
        if patient["patient_type"] != "Inpatient" or patient["status"] == "Discharged":
            messagebox.showerror("Bed assignment unavailable", "Only active inpatients can be assigned a bed.")
            return
        dialog = self._dialog("HMS | Assign inpatient bed", width=450, height=360)
        panel = tk.Frame(dialog, bg=COLORS["white"])
        panel.pack(fill="both", expand=True, padx=15, pady=15)
        tk.Label(
            panel, text="Assign bed / room", bg=COLORS["white"],
            fg=COLORS["text"], font=("Segoe UI Semibold", 15),
        ).pack(anchor="w", padx=20, pady=(20, 5))
        tk.Label(
            panel, text=f"{patient['name']}  |  {patient_id}",
            bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 9),
        ).pack(anchor="w", padx=20, pady=(0, 10))
        tk.Label(
            panel, text="Enter the hospital's bed / room identifier. A location already assigned to another active inpatient cannot be reused.",
            bg=COLORS["white"], fg=COLORS["muted"], justify="left", wraplength=360,
            font=("Segoe UI", 9),
        ).pack(anchor="w", padx=20, pady=(0, 8))
        bed = tk.StringVar(value=patient["bed"])
        self._form_label(panel, "Bed / room")
        bed_entry = ttk.Entry(panel, textvariable=bed, style="HMS.TEntry")
        bed_entry.pack(fill="x", padx=20)

        def save():
            try:
                self.store.update_patient_bed(patient_id, bed.get())
            except (sqlite3.Error, ValueError) as error:
                messagebox.showerror("Unable to assign bed", str(error), parent=dialog)
                return
            dialog.destroy()
            self.show_page(self.current_page)

        actions = tk.Frame(panel, bg=COLORS["white"])
        actions.pack(fill="x", padx=20, pady=20)
        self._button(actions, "Cancel", dialog.destroy).pack(side="right", padx=(8, 0))
        self._button(actions, "Save assignment", save, primary=True).pack(side="right")
        bed_entry.focus_set()

    def _update_patient_status_for_id(self, patient_id):
        patient = self.store.connection.execute(
            "SELECT name, patient_type, status FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
        if patient is None:
            messagebox.showerror("Patient not found", "Refresh the register and try again.")
            self._refresh_patients()
            return
        dialog = self._dialog("HMS | Update patient status", width=440)
        panel = tk.Frame(dialog, bg=COLORS["white"])
        panel.pack(fill="both", expand=True, padx=15, pady=15)
        tk.Label(panel, text="Update care status", bg=COLORS["white"], fg=COLORS["text"],
                 font=("Segoe UI Semibold", 15)).pack(anchor="w", padx=20, pady=(20, 3))
        tk.Label(
            panel, text=f"{patient['name']}  ·  {patient_id}  ·  {patient['patient_type']}",
            bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI", 9),
        ).pack(anchor="w", padx=20, pady=(0, 14))
        variable = tk.StringVar(value=patient["status"])
        self._form_label(panel, "Status")
        selector = ttk.Combobox(
            panel, textvariable=variable, values=STATUSES[patient["patient_type"]],
            state="readonly", style="HMS.TCombobox",
        )
        selector.pack(fill="x", padx=20)

        def save():
            try:
                self.store.update_status(patient_id, variable.get())
            except (sqlite3.Error, ValueError) as error:
                messagebox.showerror("Unable to update status", str(error), parent=dialog)
                return
            dialog.destroy()
            if self.current_page == "Patients":
                self._refresh_patients()
            else:
                self.show_page(self.current_page)

        actions = tk.Frame(panel, bg=COLORS["white"])
        actions.pack(fill="x", padx=20, pady=20)
        self._button(actions, "Cancel", dialog.destroy).pack(side="right", padx=(8, 0))
        self._button(actions, "Save status", save, primary=True).pack(side="right")

    def _close(self):
        self.store.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    HMSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
