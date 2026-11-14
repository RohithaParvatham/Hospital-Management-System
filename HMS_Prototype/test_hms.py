import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from hms import HospitalStore


class HospitalStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = HospitalStore(Path(self.temp_dir.name) / "test_hms.sqlite3")

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def test_seeded_doctors_are_grouped_by_specialty(self):
        doctors = self.store.list_doctors("Cardiology")
        self.assertEqual(len(doctors), 1)
        self.assertEqual(doctors[0]["specialty"], "Cardiology")
        self.assertGreaterEqual(len(self.store.list_doctors()), 7)

    def test_patient_types_priority_status_and_filters(self):
        doctor_id = self.store.list_doctors("Cardiology")[0]["id"]
        urgent_id = self.store.add_patient(
            "Prototype Patient A", 45, "Female", "", "Inpatient",
            "Cardiology", doctor_id, "Urgent", "ICU-01",
        )
        routine_id = self.store.add_patient(
            "Prototype Patient B", 31, "Male", "", "Outpatient",
            "Cardiology", doctor_id, "Routine", "",
        )

        patients = self.store.list_patients()
        self.assertEqual([row["id"] for row in patients], [urgent_id, routine_id])
        self.assertEqual(patients[0]["status"], "Admitted")
        self.assertEqual(patients[1]["status"], "Waiting")
        self.assertEqual(len(self.store.list_patients(patient_type="Inpatient")), 1)
        self.assertEqual(len(self.store.list_patients(priority="Urgent")), 1)
        self.assertEqual(len(self.store.list_patients(search="Prototype Patient B")), 1)

        self.store.update_status(urgent_id, "Discharged")
        self.assertEqual(
            self.store.connection.execute(
                "SELECT status FROM patients WHERE id = ?", (urgent_id,)
            ).fetchone()["status"],
            "Discharged",
        )

    def test_rejects_status_for_the_wrong_patient_type(self):
        doctor_id = self.store.list_doctors("Pediatrics")[0]["id"]
        patient_id = self.store.add_patient(
            "Prototype Patient C", 8, "Not specified", "", "Outpatient",
            "Pediatrics", doctor_id, "High", "",
        )
        with self.assertRaises(ValueError):
            self.store.update_status(patient_id, "Admitted")

    def test_dashboard_counts(self):
        doctor_id = self.store.list_doctors("Cardiology")[0]["id"]
        self.store.add_patient(
            "Prototype Patient D", 52, "Male", "", "Inpatient",
            "Cardiology", doctor_id, "Urgent", "ICU-02",
        )
        counts = self.store.dashboard_counts()
        self.assertEqual(counts["total"], 1)
        self.assertEqual(counts["inpatients"], 1)
        self.assertEqual(counts["urgent"], 1)
        self.assertGreaterEqual(counts["doctors"], 7)
        self.assertEqual(counts["patients_without_bed"], 0)
        self.assertEqual(counts["today_admissions"], 1)

    def test_capacity_cannot_be_set_below_current_census(self):
        doctor_id = self.store.list_doctors("Cardiology")[0]["id"]
        self.store.add_patient(
            "Prototype Patient E", 52, "Male", "", "Inpatient",
            "Cardiology", doctor_id, "Routine", "",
        )
        self.store.set_bed_capacity(12)
        self.assertEqual(self.store.get_bed_capacity(), 12)
        with self.assertRaises(ValueError):
            self.store.set_bed_capacity(0)
        self.assertEqual(self.store.dashboard_counts()["patients_without_bed"], 1)

    def test_active_inpatient_beds_are_not_double_assigned(self):
        cardiologist = self.store.list_doctors("Cardiology")[0]["id"]
        neurologist = self.store.list_doctors("Neurology")[0]["id"]
        first_id = self.store.add_patient(
            "Prototype Patient G", 52, "Male", "", "Inpatient",
            "Cardiology", cardiologist, "Routine", "ICU-01",
        )
        second_id = self.store.add_patient(
            "Prototype Patient H", 47, "Female", "", "Inpatient",
            "Neurology", neurologist, "High", "",
        )
        with self.assertRaises(ValueError):
            self.store.update_patient_bed(second_id, "icu-01")
        self.store.update_status(first_id, "Discharged")
        self.store.update_patient_bed(second_id, "icu-01")
        self.assertEqual(
            self.store.connection.execute(
                "SELECT bed FROM patients WHERE id = ?", (second_id,)
            ).fetchone()["bed"],
            "icu-01",
        )

    def test_sample_data_is_explicitly_labeled_and_never_duplicated(self):
        self.store.load_demo_data()
        patients = self.store.list_patients()
        self.assertEqual(len(patients), 5)
        self.assertEqual(self.store.sample_case_count(), 5)
        self.assertTrue(all(patient["name"].startswith("SAMPLE - ") for patient in patients))
        self.assertEqual(len(self.store.list_active_inpatients()), 2)
        self.assertEqual(len(self.store.list_outpatient_queue()), 3)
        self.assertEqual(self.store.sample_appointment_count(), 3)
        self.assertEqual(len(self.store.list_appointments(self.store.sample_appointment_date())), 3)
        with self.assertRaises(ValueError):
            self.store.load_demo_data()

    def test_sample_scenario_preserves_existing_patient_records(self):
        doctor_id = self.store.list_doctors("Cardiology")[0]["id"]
        existing_id = self.store.add_patient(
            "Existing Prototype Record", 40, "Female", "", "Outpatient",
            "Cardiology", doctor_id, "Routine", "",
        )
        self.store.load_demo_data()
        self.assertEqual(self.store.dashboard_counts()["total"], 6)
        self.assertEqual(self.store.sample_case_count(), 5)
        existing = self.store.connection.execute(
            "SELECT name FROM patients WHERE id = ?", (existing_id,)
        ).fetchone()
        self.assertEqual(existing["name"], "Existing Prototype Record")
        self.assertEqual(self.store.sample_appointment_count(), 3)

    def test_appointment_booking_blocks_overlapping_doctor_slots(self):
        doctor_id = self.store.list_doctors("Cardiology")[0]["id"]
        first_patient = self.store.add_patient(
            "Prototype Appointment A", 45, "Female", "", "Outpatient",
            "Cardiology", doctor_id, "Routine", "",
        )
        second_patient = self.store.add_patient(
            "Prototype Appointment B", 49, "Male", "", "Outpatient",
            "Cardiology", doctor_id, "Routine", "",
        )
        starts_at = (datetime.now() + timedelta(days=1)).replace(
            second=0, microsecond=0
        ).isoformat(timespec="minutes")
        first_id = self.store.add_appointment(
            first_patient, doctor_id, starts_at, 30, "Initial consultation"
        )
        second_start = (
            datetime.fromisoformat(starts_at) + timedelta(minutes=15)
        ).isoformat(timespec="minutes")
        with self.assertRaisesRegex(ValueError, "doctor already has an active appointment"):
            self.store.add_appointment(
                second_patient, doctor_id, second_start, 30, "Follow-up"
            )

        self.store.update_appointment_status(first_id, "Cancelled")
        second_id = self.store.add_appointment(
            second_patient, doctor_id, second_start, 30, "Follow-up"
        )
        self.assertGreater(second_id, first_id)

    def test_appointment_requires_outpatient_and_matching_specialty(self):
        cardiologist = self.store.list_doctors("Cardiology")[0]["id"]
        inpatient_id = self.store.add_patient(
            "Prototype Appointment C", 51, "Male", "", "Inpatient",
            "Cardiology", cardiologist, "Routine", "",
        )
        outpatient_id = self.store.add_patient(
            "Prototype Appointment D", 35, "Female", "", "Outpatient",
            "Cardiology", cardiologist, "Routine", "",
        )
        starts_at = (datetime.now() + timedelta(days=2)).replace(
            second=0, microsecond=0
        ).isoformat(timespec="minutes")
        with self.assertRaisesRegex(ValueError, "only be booked for outpatient"):
            self.store.add_appointment(inpatient_id, cardiologist, starts_at, 30, "Review")

        neurologist = self.store.list_doctors("Neurology")[0]["id"]
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.store.add_appointment(outpatient_id, neurologist, starts_at, 30, "Review")

    def test_appointment_status_transitions_and_date_filtering(self):
        cardiologist = self.store.list_doctors("Cardiology")[0]["id"]
        patient_id = self.store.add_patient(
            "Prototype Appointment E", 40, "Female", "", "Outpatient",
            "Cardiology", cardiologist, "Routine", "",
        )
        starts = datetime.now() + timedelta(days=3)
        starts_at = starts.replace(second=0, microsecond=0).isoformat(timespec="minutes")
        appointment_id = self.store.add_appointment(
            patient_id, cardiologist, starts_at, 45, "Review"
        )
        self.assertEqual(len(self.store.list_appointments(starts.date().isoformat())), 1)
        self.assertEqual(len(self.store.list_appointments((starts + timedelta(days=1)).date().isoformat())), 0)

        self.store.update_appointment_status(appointment_id, "Checked in")
        self.store.update_appointment_status(appointment_id, "In consultation")
        self.store.update_appointment_status(appointment_id, "Completed")
        with self.assertRaisesRegex(ValueError, "Cannot move"):
            self.store.update_appointment_status(appointment_id, "Scheduled")
        appointment = self.store.connection.execute(
            "SELECT status FROM appointments WHERE id = ?", (appointment_id,)
        ).fetchone()
        self.assertEqual(appointment["status"], "Completed")

    def test_specialty_workload_excludes_completed_visits(self):
        doctor_id = self.store.list_doctors("Pediatrics")[0]["id"]
        patient_id = self.store.add_patient(
            "Prototype Patient F", 8, "Not specified", "", "Outpatient",
            "Pediatrics", doctor_id, "Routine", "",
        )
        self.store.update_status(patient_id, "Visit complete")
        self.assertEqual(self.store.specialty_workload(), [])


if __name__ == "__main__":
    unittest.main()
