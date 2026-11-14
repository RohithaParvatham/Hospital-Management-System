# HMS Prototype

This is a new, standalone prototype. It does not modify or require the original
`hospital.py` application.

## Run

From PowerShell:

```powershell
cd "C:\Users\Admin\Downloads\Hospital-Management-System-main\Hospital-Management-System-main\HMS_Prototype"
py hms.py
```

It uses Python's built-in Tkinter and SQLite modules, so it does not need a
MySQL server, connector package, or password. Its local database is created as
`hms_prototype.sqlite3` in this folder. The specialty directory starts with
fictional example doctors across multiple specialties. The workspace prototype
database now contains five clearly marked fictional sample patients and three
linked outpatient appointments. Existing local patient records were preserved.
On another database, choose **Add fictional examples** to add the scenario
without overwriting existing patient or appointment records.

## Prototype workflows

- Dashboard cards summarize inpatient census, OPD waiting, open urgent/high
  workflow flags, and today's admissions, outpatient registrations, and
  appointments.
- Configure total staffed bed capacity to see occupancy and identify inpatient
  records without a bed/room entered. Capacity cannot be set below the current
  inpatient census. Assign or change a bed from the Operations screen; an
  occupied bed cannot be assigned to a second active inpatient.
- Operations page shows inpatient census and the active OPD queue. Staff can
  progress outpatient status from waiting to consultation to visit complete,
  or close an inpatient admission as discharged.
- Appointments provides a date-based clinic schedule. Book a visit for an
  outpatient and matching active specialty doctor, choose a slot length, then
  progress it through Scheduled, Checked in, In consultation, and Completed.
  Cancellation and no-show are also recorded without deleting history.
- Booking checks prevent overlapping active appointments for the same doctor
  or patient. Cancelled, no-show, and completed slots do not block later
  bookings.
- Dashboard summarizes active patient records by specialty. These counts are
  operational indicators, not staffing or treatment recommendations.
- Patient register separates inpatient and outpatient records and supports
  specialty, doctor, workflow-priority, and status fields, plus search and
  filters.
- Doctor directory groups clinicians by specialty and includes qualifications,
  clinic/unit, and phone extension.
- Patient status options depend on care type. Records can be marked discharged
  or visit complete rather than being deleted.

Use fictional data only. Priority is a staff-entered workflow label; this
prototype does not perform clinical triage and is not for clinical use or
storing real patient information.
OPD registration age is not a measured wait time. Appointment scheduling does
not confirm real clinician availability and does not send reminders. This
prototype does not include live clinical systems, bed-unit inventory, billing,
or medical records.

## Test

```powershell
py -m unittest discover -s . -v
```
