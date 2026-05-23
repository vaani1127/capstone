# HealthSaathi Dataset Mapping

| Final File | Original Source | HealthSaathi Module | Required? | Reason |
|---|---|---|---|---|
| 01_patients.csv | patients.csv | Patient Management | Yes | Core patient profile data |
| 02_appointments_encounters.csv | encounters.csv | Appointments / Visits | Yes | Used for OPD visit and encounter history |
| 03_diagnoses_conditions.csv | conditions.csv | Diagnosis / Medical Records | Yes | Used for disease and diagnosis history |
| 04_prescriptions_medications.csv | medications.csv | Prescription Module | Yes | Used for medicine and prescription records |
| 05_vitals_observations.csv | observations.csv | Vitals / Lab Observations | Yes | Used for vitals and clinical observations |
| 06_allergies.csv | allergies.csv | Allergy Records | Yes | Important for safe treatment and prescriptions |
| 07_procedures.csv | procedures.csv | Procedure Records | Yes | Stores treatment/procedure history |
| 08_organizations.csv | organizations.csv | Clinic / Hospital Info | Yes | Stores healthcare organization details |
| 09_audit_logs_synthetic.csv | Generated | Anomaly Detection | Yes | Real access logs are not public, so synthetic logs are used |
| 09_optional_immunizations.csv | immunizations.csv | Vaccination History | Optional | Add only if vaccination module is included |
| 10_optional_claims.csv | claims.csv | Billing / Insurance | Optional | Add only if billing/claims module is included |
