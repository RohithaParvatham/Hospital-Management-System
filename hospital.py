import tkinter as tk
from tkinter import messagebox, scrolledtext
import mysql.connector

class CityHospitalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("City Hospital Management System")
        self.root.geometry("800x600")

        self.connection = mysql.connector.connect(
            host="localhost", user="root", passwd="yourpassword", database="city_hospitals"
        )
        self.cursor = self.connection.cursor()

        self.create_tables()
        self.show_login_screen()

    def create_tables(self):
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS patient_detail (name VARCHAR(30) PRIMARY KEY, sex VARCHAR(15), age INT(3), address VARCHAR(50), contact VARCHAR(15))"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS doctor_details (name VARCHAR(30) PRIMARY KEY, specialisation VARCHAR(40), age INT(3), address VARCHAR(50), contact VARCHAR(15), fees INT(10), monthly_salary INT(10))"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS nurse_details (name VARCHAR(30) PRIMARY KEY, age INT(3), address VARCHAR(50), contact VARCHAR(15), monthly_salary INT(10))"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS user_data (username VARCHAR(30) PRIMARY KEY, password VARCHAR(30))"
        )
        self.connection.commit()

    def show_login_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.label = tk.Label(self.root, text="Welcome to City Hospital")
        self.label.pack(pady=10)

        self.login_button = tk.Button(self.root, text="Login", command=self.show_login_form)
        self.login_button.pack(pady=5)

        self.register_button = tk.Button(self.root, text="Register", command=self.show_register_form)
        self.register_button.pack(pady=5)

    def show_login_form(self):
        self.username = tk.StringVar()
        self.password = tk.StringVar()

        for widget in self.root.winfo_children():
            widget.destroy()

        self.label = tk.Label(self.root, text="Login")
        self.label.pack(pady=10)

        self.username_label = tk.Label(self.root, text="Username:")
        self.username_label.pack(pady=5)
        self.username_entry = tk.Entry(self.root, textvariable=self.username)
        self.username_entry.pack(pady=5)

        self.password_label = tk.Label(self.root, text="Password:")
        self.password_label.pack(pady=5)
        self.password_entry = tk.Entry(self.root, textvariable=self.password, show="*")
        self.password_entry.pack(pady=5)

        self.login_button = tk.Button(self.root, text="Login", command=self.login)
        self.login_button.pack(pady=10)

        self.back_button = tk.Button(self.root, text="Back", command=self.show_login_screen)
        self.back_button.pack(pady=10)

    def show_register_form(self):
        self.new_username = tk.StringVar()
        self.new_password = tk.StringVar()

        for widget in self.root.winfo_children():
            widget.destroy()

        self.label = tk.Label(self.root, text="Register")
        self.label.pack(pady=10)

        self.username_label = tk.Label(self.root, text="Username:")
        self.username_label.pack(pady=5)
        self.username_entry = tk.Entry(self.root, textvariable=self.new_username)
        self.username_entry.pack(pady=5)

        self.password_label = tk.Label(self.root, text="Password:")
        self.password_label.pack(pady=5)
        self.password_entry = tk.Entry(self.root, textvariable=self.new_password, show="*")
        self.password_entry.pack(pady=5)

        self.register_button = tk.Button(self.root, text="Register", command=self.register)
        self.register_button.pack(pady=10)

        self.back_button = tk.Button(self.root, text="Back", command=self.show_login_screen)
        self.back_button.pack(pady=10)

    def login(self):
        username = self.username.get()
        password = self.password.get()

        self.cursor.execute("SELECT password FROM user_data WHERE username=%s", (username,))
        row = self.cursor.fetchone()
        if row and row[0] == password:
            messagebox.showinfo("Success", "Login Successful!")
            self.show_admin_menu()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def register(self):
        username = self.new_username.get()
        password = self.new_password.get()

        try:
            self.cursor.execute("INSERT INTO user_data (username, password) VALUES (%s, %s)", (username, password))
            self.connection.commit()
            messagebox.showinfo("Success", "Registration Successful!")
            self.show_login_form()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Error: {err}")

    def show_admin_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.label = tk.Label(self.root, text="Admin Menu")
        self.label.pack(pady=10)

        self.doctor_button = tk.Button(self.root, text="Doctor Details", command=self.show_doctor_details)
        self.doctor_button.pack(pady=5)

        self.nurse_button = tk.Button(self.root, text="Nurse Details", command=self.show_nurse_details)
        self.nurse_button.pack(pady=5)

        self.patient_button = tk.Button(self.root, text="Patient Details", command=self.show_patient_details)
        self.patient_button.pack(pady=5)

        self.logout_button = tk.Button(self.root, text="Logout", command=self.show_login_screen)
        self.logout_button.pack(pady=10)

    def show_doctor_details(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.label = tk.Label(self.root, text="Doctor Details")
        self.label.pack(pady=10)

        self.display_button = tk.Button(self.root, text="Display All Doctors", command=self.display_doctors)
        self.display_button.pack(pady=5)

        self.add_button = tk.Button(self.root, text="Add New Doctor", command=self.add_doctor)
        self.add_button.pack(pady=5)

        self.delete_button = tk.Button(self.root, text="Delete Doctor", command=self.delete_doctor)
        self.delete_button.pack(pady=5)

        self.back_button = tk.Button(self.root, text="Back", command=self.show_admin_menu)
        self.back_button.pack(pady=10)

        self.text_box = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=70, height=10)
        self.text_box.pack(pady=10)

    def display_doctors(self):
        self.cursor.execute("SELECT * FROM doctor_details")
        rows = self.cursor.fetchall()
        self.text_box.delete(1.0, tk.END)
        for row in rows:
            self.text_box.insert(tk.END, f"{row}\n")

    def add_doctor(self):
        self.new_name = tk.StringVar()
        self.new_specialisation = tk.StringVar()
        self.new_age = tk.IntVar()
        self.new_address = tk.StringVar()
        self.new_contact = tk.StringVar()
        self.new_fees = tk.IntVar()
        self.new_salary = tk.IntVar()

        for widget in self.root.winfo_children():
            widget.destroy()

        self.label = tk.Label(self.root, text="Add New Doctor")
        self.label.pack(pady=10)

        self.name_label = tk.Label(self.root, text="Name:")
        self.name_label.pack(pady=5)
        self.name_entry = tk.Entry(self.root, textvariable=self.new_name)
        self.name_entry.pack(pady=5)

        self.specialisation_label = tk.Label(self.root, text="Specialisation:")
        self.specialisation_label.pack(pady=5)
        self.specialisation_entry = tk.Entry(self.root, textvariable=self.new_specialisation)
        self.specialisation_entry.pack(pady=5)

        self.age_label = tk.Label(self.root, text="Age:")
        self.age_label.pack(pady=5)
        self.age_entry = tk.Entry(self.root, textvariable=self.new_age)
        self.age_entry.pack(pady=5)

        self.address_label = tk.Label(self.root, text="Address:")
        self.address_label.pack(pady=5)
        self.address_entry = tk.Entry(self.root, textvariable=self.new_address)
        self.address_entry.pack(pady=5)

        self.contact_label = tk.Label(self.root, text="Contact:")
        self.contact_label.pack(pady=5)
        self.contact_entry = tk.Entry(self.root, textvariable=self.new_contact)
        self.contact_entry.pack(pady=5)

        self.fees_label = tk.Label(self.root, text="Fees:")
        self.fees_label.pack(pady=5)
        self.fees_entry = tk.Entry(self.root, textvariable=self.new_fees)
        self.fees_entry.pack(pady=5)

        self.salary_label = tk.Label(self.root, text="Monthly Salary:")
        self.salary_label.pack(pady=5)
        self.salary_entry = tk.Entry(self.root, textvariable=self.new_salary)
        self.salary_entry.pack(pady=5)

        self.add_button = tk.Button(self.root, text="Add", command=self.insert_doctor)
        self.add_button.pack(pady=10)

        self.back_button = tk.Button(self.root, text="Back", command=self.show_doctor_details)
        self.back_button.pack(pady=10)

    def insert_doctor(self):
        name = self.new_name.get()
        specialisation = self.new_specialisation.get()
        age = self.new_age.get()
        address = self.new_address.get()
        contact = self.new_contact.get()
        fees = self.new_fees.get()
        salary = self.new_salary.get()

        try:
            self.cursor.execute(
                "INSERT INTO doctor_details (name, specialisation, age, address, contact, fees, monthly_salary) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (name, specialisation, age, address, contact, fees, salary)
            )
            self.connection.commit()
            messagebox.showinfo("Success", "Doctor added successfully!")
            self.show_doctor_details()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Error: {err}")

    def delete_doctor(self):
        self.delete_name = tk.StringVar()

        for widget in self.root.winfo_children():
            widget.destroy()

        self.label = tk.Label(self.root, text="Delete Doctor")
        self.label.pack(pady=10)

        self.name_label = tk.Label(self.root, text="Name:")
        self.name_label.pack(pady=5)
        self.name_entry = tk.Entry(self.root, textvariable=self.delete_name)
        self.name_entry.pack(pady=5)

        self.delete_button = tk.Button(self.root, text="Delete", command=self.remove_doctor)
        self.delete_button.pack(pady=10)

        self.back_button = tk.Button(self.root, text="Back", command=self.show_doctor_details)
        self.back_button.pack(pady=10)

    def remove_doctor(self):
        name = self.delete_name.get()

        try:
            self.cursor.execute("DELETE FROM doctor_details WHERE name=%s", (name,))
            self.connection.commit()
            messagebox.showinfo("Success", "Doctor deleted successfully!")
            self.show_doctor_details()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Error: {err}")

    def show_nurse_details(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.label = tk.Label(self.root, text="Nurse Details")
        self.label.pack(pady=10)

        self.display_button = tk.Button(self.root, text="Display All Nurses", command=self.display_nurses)
        self.display_button.pack(pady=5)

        self.add_button = tk.Button(self.root, text="Add New Nurse", command=self.add_nurse)
        self.add_button.pack(pady=5)

        self.delete_button = tk.Button(self.root, text="Delete Nurse", command=self.delete_nurse)
        self.delete_button.pack(pady=5)

        self.back_button = tk.Button(self.root, text="Back", command=self.show_admin_menu)
        self.back_button.pack(pady=10)

        self.text_box = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=70, height=10)
        self.text_box.pack(pady=10)

    def display_nurses(self):
        self.cursor.execute("SELECT * FROM nurse_details")
        rows = self.cursor.fetchall()
        self.text_box.delete(1.0, tk.END)
        for row in rows:
            self.text_box.insert(tk.END, f"{row}\n")

    def add_nurse(self):
        self.new_name = tk.StringVar()
        self.new_age = tk.IntVar()
        self.new_address = tk.StringVar()
        self.new_contact = tk.StringVar()
        self.new_salary = tk.IntVar()

        for widget in self.root.winfo_children():
            widget.destroy()

        self.label = tk.Label(self.root, text="Add New Nurse")
        self.label.pack(pady=10)

        self.name_label = tk.Label(self.root, text="Name:")
        self.name_label.pack(pady=5)
        self.name_entry = tk.Entry(self.root, textvariable=self.new_name)
        self.name_entry.pack(pady=5)

        self.age_label = tk.Label(self.root, text="Age:")
        self.age_label.pack(pady=5)
        self.age_entry = tk.Entry(self.root, textvariable=self.new_age)
        self.age_entry.pack(pady=5)

        self.address_label = tk.Label(self.root, text="Address:")
        self.address_label.pack(pady=5)
        self.address_entry = tk.Entry(self.root, textvariable=self.new_address)
        self.address_entry.pack(pady=5)

        self.contact_label = tk.Label(self.root, text="Contact:")
        self.contact_label.pack(pady=5)
        self.contact_entry = tk.Entry(self.root, textvariable=self.new_contact)
        self.contact_entry.pack(pady=5)

        self.salary_label = tk.Label(self.root, text="Monthly Salary:")
        self.salary_label.pack(pady=5)
        self.salary_entry = tk.Entry(self.root, textvariable=self.new_salary)
        self.salary_entry.pack(pady=5)

        self.add_button = tk.Button(self.root, text="Add", command=self.insert_nurse)
        self.add_button.pack(pady=10)

        self.back_button = tk.Button(self.root, text="Back", command=self.show_nurse_details)
        self.back_button.pack(pady=10)

    def insert_nurse(self):
        name = self.new_name.get()
        age = self.new_age.get()
        address = self.new_address.get()
        contact = self.new_contact.get()
        salary = self.new_salary.get()

        try:
            self.cursor.execute(
                "INSERT INTO nurse_details (name, age, address, contact, monthly_salary) VALUES (%s, %s, %s, %s, %s)",
                (name, age, address, contact, salary)
            )
            self.connection.commit()
            messagebox.showinfo("Success", "Nurse added successfully!")
            self.show_nurse_details()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Error: {err}")

    def delete_nurse(self):
        self.delete_name = tk.StringVar()

        for widget in self.root.winfo_children():
            widget.destroy()

        self.label = tk.Label(self.root, text="Delete Nurse")
        self.label.pack(pady=10)

        self.name_label = tk.Label(self.root, text="Name:")
        self.name_label.pack(pady=5)
        self.name_entry = tk.Entry(self.root, textvariable=self.delete_name)
        self.name_entry.pack(pady=5)

        self.delete_button = tk.Button(self.root, text="Delete", command=self.remove_nurse)
        self.delete_button.pack(pady=10)

        self.back_button = tk.Button(self.root, text="Back", command=self.show_nurse_details)
        self.back_button.pack(pady=10)

    def remove_nurse(self):
        name = self.delete_name.get()

        try:
            self.cursor.execute("DELETE FROM nurse_details WHERE name=%s", (name,))
            self.connection.commit()
            messagebox.showinfo("Success", "Nurse deleted successfully!")
            self.show_nurse_details()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Error: {err}")

    def show_patient_details(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.label = tk.Label(self.root, text="Patient Details")
        self.label.pack(pady=10)

        self.display_button = tk.Button(self.root, text="Display All Patients", command=self.display_patients)
        self.display_button.pack(pady=5)

        self.add_button = tk.Button(self.root, text="Add New Patient", command=self.add_patient)
        self.add_button.pack(pady=5)

        self.delete_button = tk.Button(self.root, text="Discharge Patient", command=self.delete_patient)
        self.delete_button.pack(pady=5)

        self.back_button = tk.Button(self.root, text="Back", command=self.show_admin_menu)
        self.back_button.pack(pady=10)

        self.text_box = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=70, height=10)
        self.text_box.pack(pady=10)

    def display_patients(self):
        self.cursor.execute("SELECT * FROM patient_detail")
        rows = self.cursor.fetchall()
        self.text_box.delete(1.0, tk.END)
        for row in rows:
            self.text_box.insert(tk.END, f"{row}\n")

    def add_patient(self):
        self.new_name = tk.StringVar()
        self.new_sex = tk.StringVar()
        self.new_age = tk.IntVar()
        self.new_address = tk.StringVar()
        self.new_contact = tk.StringVar()

        for widget in self.root.winfo_children():
            widget.destroy()

        self.label = tk.Label(self.root, text="Add New Patient")
        self.label.pack(pady=10)

        self.name_label = tk.Label(self.root, text="Name:")
        self.name_label.pack(pady=5)
        self.name_entry = tk.Entry(self.root, textvariable=self.new_name)
        self.name_entry.pack(pady=5)

        self.sex_label = tk.Label(self.root, text="Sex:")
        self.sex_label.pack(pady=5)
        self.sex_entry = tk.Entry(self.root, textvariable=self.new_sex)
        self.sex_entry.pack(pady=5)

        self.age_label = tk.Label(self.root, text="Age:")
        self.age_label.pack(pady=5)
        self.age_entry = tk.Entry(self.root, textvariable=self.new_age)
        self.age_entry.pack(pady=5)

        self.address_label = tk.Label(self.root, text="Address:")
        self.address_label.pack(pady=5)
        self.address_entry = tk.Entry(self.root, textvariable=self.new_address)
        self.address_entry.pack(pady=5)

        self.contact_label = tk.Label(self.root, text="Contact:")
        self.contact_label.pack(pady=5)
        self.contact_entry = tk.Entry(self.root, textvariable=self.new_contact)
        self.contact_entry.pack(pady=5)

        self.add_button = tk.Button(self.root, text="Add", command=self.insert_patient)
        self.add_button.pack(pady=10)

        self.back_button = tk.Button(self.root, text="Back", command=self.show_patient_details)
        self.back_button.pack(pady=10)

    def insert_patient(self):
        name = self.new_name.get()
        sex = self.new_sex.get()
        age = self.new_age.get()
        address = self.new_address.get()
        contact = self.new_contact.get()

        try:
            self.cursor.execute(
                "INSERT INTO patient_detail (name, sex, age, address, contact) VALUES (%s, %s, %s, %s, %s)",
                (name, sex, age, address, contact)
            )
            self.connection.commit()
            messagebox.showinfo("Success", "Patient added successfully!")
            self.show_patient_details()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Error: {err}")

    def delete_patient(self):
        self.delete_name = tk.StringVar()

        for widget in self.root.winfo_children():
            widget.destroy()

        self.label = tk.Label(self.root, text="Discharge Patient")
        self.label.pack(pady=10)

        self.name_label = tk.Label(self.root, text="Name:")
        self.name_label.pack(pady=5)
        self.name_entry = tk.Entry(self.root, textvariable=self.delete_name)
        self.name_entry.pack(pady=5)

        self.delete_button = tk.Button(self.root, text="Discharge", command=self.remove_patient)
        self.delete_button.pack(pady=10)

        self.back_button = tk.Button(self.root, text="Back", command=self.show_patient_details)
        self.back_button.pack(pady=10)

    def remove_patient(self):
        name = self.delete_name.get()

        try:
            self.cursor.execute("DELETE FROM patient_detail WHERE name=%s", (name,))
            self.connection.commit()
            messagebox.showinfo("Success", "Patient discharged successfully!")
            self.show_patient_details()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Error: {err}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CityHospitalApp(root)
    root.mainloop()
