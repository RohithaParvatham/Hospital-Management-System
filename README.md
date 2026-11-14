# HMS - Hospital Management System

This repository's main application is the standalone Tkinter and SQLite
prototype in `HMS_Prototype`. The root `hospital.py` file launches it.

## Run

From PowerShell in this project folder:

```powershell
py hospital.py
```

The app uses Python's built-in Tkinter and SQLite modules. It does not need
MySQL or a third-party Python package. Its local database is stored at
`HMS_Prototype/hms_prototype.sqlite3`.

The app includes a specialty doctor directory, inpatient/outpatient register,
bed capacity and assignment workflow, outpatient operations queue, and
appointment booking with overlap checks and status tracking. It starts with
fictional example doctors. Patient and appointment examples are clearly
labelled `SAMPLE` and can be added from the dashboard or Appointments page.

## Tests

```powershell
py -m unittest discover -s HMS_Prototype -v
```

## Project layout

- `hospital.py` - root application launcher.
- `HMS_Prototype/hms.py` - Tkinter interface and application logic.
- `HMS_Prototype/test_hms.py` - automated tests using temporary SQLite databases.
- `HMS_Prototype/README.md` - feature and prototype-scope details.

This is an academic administrative workflow prototype, not a production
clinical system. Use fictional data only. It has no login, user roles,
diagnoses, prescriptions, billing, external APIs, or production privacy
controls.
