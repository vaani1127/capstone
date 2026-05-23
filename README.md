# HealthSaathi – AI-Powered Healthcare Management System

HealthSaathi is a capstone healthcare project designed to manage patient records, appointments, diagnoses, prescriptions, vitals, allergies, procedures, organizations, and audit logs. The project uses structured healthcare datasets to support patient management, clinical record tracking, and synthetic audit-log based anomaly detection.

## Project Overview

The goal of HealthSaathi is to build a healthcare management system that can store, organize, and analyze patient-related medical data in a structured way. The system is designed around multiple CSV datasets mapped from healthcare data sources such as Synthea, along with additional synthetic data for audit-log analysis.

This project can be used for:

- Patient profile management
- Appointment and encounter tracking
- Diagnosis and condition history
- Prescription and medication records
- Vitals and clinical observations
- Allergy and procedure tracking
- Healthcare organization management
- Audit-log analysis and anomaly detection

## Dataset Files

The project uses the following main dataset files:

| File Name | Purpose |
|---|---|
| `01_patients.csv` | Stores patient demographic and basic healthcare profile information |
| `02_appointments_encounters.csv` | Stores appointment, visit, and OPD encounter history |
| `03_diagnoses_conditions.csv` | Stores diagnosis and medical condition history |
| `04_prescriptions_medications.csv` | Stores prescription and medicine records |
| `05_vitals_observations.csv` | Stores vitals, lab values, and clinical observations |
| `06_allergies.csv` | Stores patient allergy records |
| `07_procedures.csv` | Stores medical procedures performed during treatment |
| `08_organizations.csv` | Stores clinic, hospital, and healthcare organization details |
| `09_audit_logs_synthetic.csv` | Stores synthetic access logs for anomaly detection |

## Features

- Structured healthcare database design
- Patient-centric record management
- Appointment and encounter history tracking
- Diagnosis and prescription management
- Vitals and observation storage
- Allergy and procedure record support
- Organization and hospital data management
- Synthetic audit-log dataset for security analysis
- Suitable for machine learning and anomaly detection experiments

## Tech Stack

The project can be implemented using:

- Python
- Pandas
- NumPy
- Scikit-learn
- SQL / DBMS
- Flask or Streamlit 
- CSV-based datasets
- Flutter

## Folder Structure

```text
capstone/
│
├── datasets/
│   ├── 01_patients.csv
│   ├── 02_appointments_encounters.csv
│   ├── 03_diagnoses_conditions.csv
│   ├── 04_prescriptions_medications.csv
│   ├── 05_vitals_observations.csv
│   ├── 06_allergies.csv
│   ├── 07_procedures.csv
│   ├── 08_organizations.csv
│   └── 09_audit_logs_synthetic.csv
│
├── notebooks/
│   └── data_analysis.ipynb
│
├── src/
│   └── main.py
│
├── README.md
└── requirements.txt
