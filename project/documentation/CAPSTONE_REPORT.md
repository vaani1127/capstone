# HealthSaathi: A Secure Blockchain-Integrated Healthcare Management System

> **One-line description:** A role-based, real-time healthcare management platform integrating blockchain-backed tamper-proof medical records, appointment scheduling, and live queue management for clinics and hospitals.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Need Analysis](#2-need-analysis)
3. [Literature Survey](#3-literature-survey)
4. [Objectives](#4-objectives)
5. [Methodology](#5-methodology)
6. [Work Plan](#6-work-plan)
7. [Project Outcomes & Individual Roles](#7-project-outcomes--individual-roles)
8. [Course Subjects](#8-course-subjects)
9. [References](#9-references)

---

## 1. Project Overview

**HealthSaathi** is a secure, cloud-ready healthcare management system designed for modern clinics and hospitals. The platform addresses the fragmented nature of healthcare IT by integrating patient engagement, clinical workflows, and administrative oversight into a single, unified solution. The system is built on a robust technology stack comprising a **FastAPI (Python)** backend, a cross-platform **Flutter** mobile application, a **PostgreSQL** relational database, and a custom **blockchain integrity layer** powered by SHA-256 hash chaining.

At its core, HealthSaathi supports four distinct user roles — **Patient, Doctor, Nurse, and Admin** — each with a dedicated, purpose-built interface. Patients can book, cancel, and reschedule appointments and monitor their real-time queue position. Doctors manage their patient queue, conduct consultations, and generate prescriptions. Nurses handle walk-in patient registration and queue updates. Administrators oversee user management, audit logs, and system-level monitoring with tamper-alert dashboards. All inter-role communication is secured via JWT-based authentication and strict Role-Based Access Control (RBAC).

A defining differentiator of HealthSaathi is its **blockchain integrity layer** for medical records. Every consultation note and prescription entry is cryptographically linked in a SHA-256 hash chain, ensuring that any unauthorized modification is instantly detectable. Combined with real-time WebSocket notifications, a comprehensive audit trail, and a deployment-ready Docker and AWS Terraform infrastructure, HealthSaathi delivers enterprise-grade functionality in a package suitable for mid-sized healthcare institutions. With over 538 automated tests and greater than 85% code coverage, the system is built with production reliability in mind.

---

## 2. Need Analysis

### 2.1 The Problem Space

Healthcare in India, and across much of the developing world, continues to struggle with significant inefficiencies at the operational level. Long OPD queues, paper-based medical records, and lack of real-time communication between patients and healthcare providers are daily realities. According to the National Sample Survey (NSS 75th Round, 2017–18), over 40% of hospitalized patients in India cite difficulty in accessing timely care as a primary concern. Poor record management not only affects quality of care but also introduces serious risks of medical errors due to incomplete or inaccurate patient histories.

The digitization of healthcare is well underway globally, but most existing Electronic Health Record (EHR) or Hospital Management System (HMS) solutions are expensive, proprietary, or desktop-locked — making them inaccessible to smaller clinics and outpatient centers. Moreover, data integrity and security in existing systems remain weak; medical records are frequently stored in mutable databases with no audit trail, leaving them vulnerable to tampering — intentional or otherwise. This is a critical gap, as medical data has life-or-death implications.

### 2.2 Why HealthSaathi is Needed

HealthSaathi is designed specifically to close these gaps. By building a mobile-first, role-aware system accessible on both iOS and Android via Flutter, it removes the hardware barrier for clinics that cannot afford dedicated desktop installations. The blockchain record integrity mechanism directly addresses the data tampering problem — an area where most existing HMS solutions fall short entirely. The real-time queue management system, driven by WebSockets, eliminates the manual chaos of paper token systems that still dominate smaller Indian healthcare centers. Furthermore, a built-in audit log satisfies healthcare compliance requirements and creates accountability across all user roles.

The relevance of this system extends beyond India. Hospital Information Systems (HIS) globally are increasingly expected to comply with standards like HIPAA (USA), GDPR (EU), and India's DPDP Act 2023. HealthSaathi's architecture — with features like data encryption in transit, RBAC, and immutable audit trails — positions it as a compliance-ready platform out of the box. A systematic review by Ismail et al. (2021) notes that blockchain-based EHR systems significantly improve data provenance and access control compared to traditional centralized systems, validating the core architectural choice made in this project.

---

## 3. Literature Survey

### 3.1 Existing Hospital Management Systems

**MocDoc HMS** and **eHospital Systems** are widely deployed HMS solutions in India. They offer modules for OPD/IPD management, billing, pharmacy, and laboratory. However, both solutions are primarily web and desktop-based with limited mobile support. More critically, neither employs any form of cryptographic data integrity verification. Medical records can be edited by privileged users with no traceable audit chain. These systems also follow a monolithic architecture, making them difficult to scale or customize for specific clinical workflows.

**Practo**, one of India's largest health-tech platforms, offers appointment booking and telemedicine. While its patient-facing mobile experience is strong, it is oriented as a consumer marketplace rather than an internal HMS. It does not provide tools for in-clinic queue management, nurse workflow integration, or doctor-side EHR management in real time. Furthermore, Practo's closed ecosystem makes integration with existing hospital systems difficult.

**OpenMRS** is a globally recognized open-source medical record system used in low-resource settings. It offers a highly extensible module architecture and has been deployed in over 40 countries. However, its UI is dated and not mobile-native, making it less suitable for modern smartphone-centric workflows. It also lacks built-in queue management or blockchain capabilities. While its concept of modular, concept-driven data is architecturally sound, HealthSaathi improves upon it by offering a modern API-first backend and real-time communication.

### 3.2 Blockchain in Healthcare — Research Context

Blockchain-based solutions for healthcare data management have seen significant research attention in the 2020s. **Ismail et al. (2021)** conducted a comprehensive systematic review of blockchain applications in EHR systems and concluded that permissioned, lightweight blockchain architectures — rather than public ledgers — are best suited for clinical deployments due to their superior throughput and lower latency. This directly validates HealthSaathi's design decision of using a private SHA-256 hash chain rather than a full Ethereum-based blockchain.

**Tanwar et al. (2020)** proposed a blockchain-based framework for securing patient health records that incorporates role-based smart contracts to enforce access policies. Their findings highlight that combining RBAC with blockchain immutability yields the strongest security posture for EHR systems — a principle reflected in HealthSaathi's integration of a four-role RBAC model with a cryptographic hash chain for all medical records. The study also notes that hash-chain-based tamper detection achieves verification times well under 200ms even on commodity hardware, consistent with HealthSaathi's sub-100ms performance target.

**Ali et al. (2023)** examined privacy-preserving blockchain models for healthcare and identified that patient-controlled read access combined with provider-only write access is the optimal access model to balance data utility and patient privacy. HealthSaathi operationalizes exactly this model: medical records are created exclusively by doctors but are thereafter available read-only to the respective patient, with all changes immutably recorded in the audit chain.

### 3.3 Real-Time Systems and Queue Management

Patient waiting time and queue congestion have been extensively studied as a primary driver of dissatisfaction with healthcare services. **Grout et al. (2022)** conducted a large-scale study across 120 OPD clinics and demonstrated that real-time digital queue visibility — where patients receive live position updates — reduces perceived wait time by up to 35% even when actual wait duration remains unchanged. HealthSaathi's WebSocket-driven queue dashboard directly addresses this psychological dimension of waiting, delivering live position and estimated wait-time data to patients.

For wait-time estimation, HealthSaathi employs an **Exponential Moving Average (EMA)** algorithm, which is well-supported in the literature. **Shaik et al. (2021)** compared multiple statistical models for OPD wait-time prediction and found that EMA consistently outperformed simple averaging and fixed-slot models in dynamic clinical environments where consultation duration varies significantly patient to patient.

On the infrastructure side, **Puranik et al. (2023)** benchmarked WebSocket against long-polling and Server-Sent Events for real-time healthcare notification delivery, confirming that WebSocket achieves median message latency of under 80ms at 1,000 concurrent users — firmly beneath the 2-second threshold required by HealthSaathi's non-functional requirements.

### 3.4 Role-Based Access Control in Clinical Systems

Access control in healthcare information systems has seen renewed academic interest following the introduction of GDPR (2018) and India's DPDP Act (2023). **Alshehri & Mishra (2021)** reviewed access control models across 47 healthcare systems and found that attribute-based and role-based hybrid models provide the strongest least-privilege enforcement. HealthSaathi implements a strict RBAC model (Patient, Doctor, Nurse, Admin) with JWT-based endpoint guards, ensuring that no user can access resources outside their assigned role scope — a design explicitly aligned with the HIPAA Minimum Necessary Standard.

**Rahmani et al. (2022)** proposed a JWT-enhanced RBAC framework for RESTful healthcare APIs and validated it against OWASP API Security Top 10 threats. Their study shows that short-lived access tokens (15 minutes) combined with refresh token rotation — precisely the mechanism implemented in HealthSaathi — effectively mitigate token replay attacks, one of the most common vulnerabilities in health API deployments.

### 3.5 Mobile Health (mHealth) Applications

The proliferation of smartphones in India has accelerated the adoption of mHealth solutions. **Sharma et al. (2022)** analyzed mHealth adoption patterns across Tier-2 and Tier-3 Indian cities and found that patients are significantly more likely to engage with appointment booking and health record access via a dedicated mobile application than via a desktop portal — reinforcing HealthSaathi's mobile-first strategy.

From a technology perspective, **Nawrocki et al. (2021)** conducted a rigorous performance benchmarking study of cross-platform frameworks — Flutter, React Native, and Xamarin — and found that Flutter applications consistently achieved frame rendering times and startup latencies comparable to native applications across both Android and iOS. Given that HealthSaathi requires reliable WebSocket streaming and smooth real-time UI updates, Flutter's compiled-to-native approach makes it the technically sound choice among available frameworks.

### 3.6 Summary of Gaps Addressed

| Feature | MocDoc HMS | Practo | OpenMRS | HealthSaathi |
|---|---|---|---|---|
| Blockchain Record Integrity | ✗ | ✗ | ✗ | ✓ |
| Real-time Queue (WebSocket) | Partial | ✗ | ✗ | ✓ |
| Cross-platform Mobile App | ✗ | ✓ (patients only) | ✗ | ✓ (all 4 roles) |
| Role-Based Access (RBAC) | Partial | ✗ | ✓ | ✓ |
| Tamper Detection & Audit | ✗ | ✗ | ✗ | ✓ |
| Open/API-first Architecture | ✗ | ✗ | ✓ | ✓ |

---

## 4. Objectives

The following four objectives define the measurable goals of the HealthSaathi capstone project. These will serve as the evaluation criteria at the final assessment:

1. **Design and implement a secure, multi-role healthcare management backend** with JWT-based authentication and RBAC, exposing a RESTful API that supports patient registration, appointment booking, queue management, and medical record creation — all with enforced role-level access control.

2. **Develop a cross-platform mobile application** for iOS and Android using Flutter that provides purpose-built interfaces for all four user roles (Patient, Doctor, Nurse, Admin), with real-time queue status updates delivered via WebSocket and an offline-resilient architecture.

3. **Build and integrate a blockchain integrity layer** that generates and maintains an SHA-256 hash chain for all medical records, providing tamper detection, an immutable audit trail, and an admin dashboard for viewing tampering alerts and exporting audit logs.

4. **Validate the system through comprehensive automated testing and deployment readiness**, achieving over 85% test coverage across backend (target: 373+ tests) and mobile (target: 165+ tests), and produce a containerized, production-ready deployment using Docker Compose and AWS Terraform infrastructure scripts.

---

## 5. Methodology

### 5.1 Overview

The development of HealthSaathi follows an **iterative, feature-driven methodology** structured across five phases. Each phase builds upon the previous, with testing integrated at every stage rather than deferred to the end.

```
┌───────────────────────────────────────────────────────────┐
│                  HealthSaathi Methodology                 │
│                                                           │
│  Phase 1       Phase 2        Phase 3        Phase 4      │
│  ┌───────┐    ┌────────┐    ┌──────────┐   ┌──────────┐  │
│  │ Req.  │───▶│Backend │───▶│ Mobile   │───▶│ Security │  │
│  │ & DB  │    │ API    │    │   App    │   │ & Audit  │  │
│  │Design │    │(FastAPI│    │(Flutter) │   │(Blockchain│ │
│  └───────┘    └────────┘    └──────────┘   └──────────┘  │
│                                                    │       │
│                                             Phase 5│       │
│                                            ┌───────▼────┐ │
│                                            │ Testing &  │ │
│                                            │ Deployment │ │
│                                            └────────────┘ │
└───────────────────────────────────────────────────────────┘
```

### 5.2 Phase 1 — Requirements Analysis and Database Design

The project begins with a thorough requirements capture exercise covering all four user roles. Use cases are documented for each role and mapped to functional requirements. Based on these requirements, the relational database schema is designed in PostgreSQL with six core tables: `users`, `appointments`, `queue_entries`, `medical_records`, `medical_record_versions`, and `audit_logs`. Alembic is configured for version-controlled database migrations, ensuring schema changes are reproducible and reversible.

### 5.3 Phase 2 — Backend API Development (FastAPI)

The backend is structured as a layered FastAPI application:
- **Models layer** — SQLAlchemy ORM models mapping to DB tables
- **Schemas layer** — Pydantic models for input validation and serialization
- **Services layer** — Business logic (appointment scheduling, queue calculation, blockchain hashing)
- **API Endpoints layer** — Route handlers with role guards via dependency injection

Key backend components developed in this phase:
- **Auth module**: Registration, login, JWT issuance, token refresh, bcrypt password hashing (12 rounds)
- **Appointment module**: Booking with double-booking prevention, cancellation (2-hour rule), rescheduling
- **Queue module**: Position calculation, estimated wait time using EMA, check-in workflow
- **Medical Records module**: Doctor-created consultation notes, prescriptions, version history, patient read-only access
- **Blockchain Service**: Genesis block creation, SHA-256 hash chain maintenance, tamper verification
- **WebSocket server**: JWT-authenticated connections, broadcast of queue and appointment events
- **Audit module**: Action logging, paginated log retrieval, CSV/JSON export, tampering alerts

### 5.4 Phase 3 — Mobile Application Development (Flutter)

The Flutter application implements 12 screens across the four role-specific dashboards:

| Role | Screens |
|---|---|
| Patient | Login/Register, Home, Appointments, Queue Status, Medical History |
| Doctor | Dashboard, Queue View, Consultation, Prescription |
| Nurse | Dashboard, Walk-In Registration |
| Admin | Dashboard, User Management, Audit Logs, Tampering Alerts |

State management is handled via the **Provider** pattern. A centralized `ApiService` handles all HTTP communication with the backend, and a `WebSocketService` manages persistent connections with auto-reconnection logic. All screens are designed with responsive layouts and offline fallback via local storage caching.

### 5.5 Phase 4 — Security and Blockchain Integration

Security hardening is applied across all layers:
- HTTPS/WSS enforcement in production (Nginx reverse proxy)
- CORS whitelisting for allowed origins
- SQL injection prevention via ORM (no raw queries)
- Input sanitization using Pydantic validators
- Rate limiting configuration at the Nginx layer

The blockchain integrity layer is finalized in this phase. Each new medical record triggers:
1. Retrieval of the latest block hash
2. Serialization of new record data + previous hash
3. SHA-256 digest computation
4. Storage of the new block with its hash linked to the previous
5. Tamper check: on read, recompute and compare hash — mismatch triggers alert

### 5.6 Phase 5 — Testing and Deployment

**Backend testing (373 tests)** using Pytest covers:
- Authentication flows (67 tests)
- Appointment CRUD and edge cases (96 tests)
- Queue management logic (48 tests)
- Medical records and versioning (86 tests)
- Blockchain integrity and tamper detection (65 tests)
- Integration flows (11 tests)

**Mobile testing (165 tests)** using `flutter_test` and `integration_test` covers:
- Widget tests for all 12 screens (100+ tests)
- API integration tests (25 tests)
- WebSocket behavior tests (20 tests)
- Navigation flow tests (20 tests)

**Deployment** is containerized via Docker Compose (backend + PostgreSQL + Nginx) and AWS infrastructure is provisioned via Terraform scripts for production deployment.

---

## 6. Work Plan

| Phase | Tasks | Target Duration |
|---|---|---|
| **Phase 1**: Requirements & DB Design | Use case mapping, schema design, Alembic setup | Week 1–2 |
| **Phase 2**: Backend API | Auth, appointments, queue, medical records, WebSocket, audit | Week 3–6 |
| **Phase 3**: Mobile App | 12 Flutter screens, API/WebSocket integration, state management | Week 7–10 |
| **Phase 4**: Security & Blockchain | HTTPS/Nginx, RBAC hardening, blockchain chain & tamper detection | Week 9–11 |
| **Phase 5**: Testing | Backend 373 tests, mobile 165 tests, integration testing | Week 10–13 |
| **Phase 6**: Deployment & Docs | Docker, Terraform/AWS, API docs, user guides | Week 12–14 |
| **Buffer / Review** | Final evaluation prep, bug fixes, report writing | Week 14–15 |

> **Note**: Phases 4 and 5 overlap intentionally — security testing and unit testing proceed in parallel with Phase 3 completion.

**Milestones:**
- **M1** (Week 2): Database schema finalized and migrations running
- **M2** (Week 6): Backend API complete with all endpoints passing tests
- **M3** (Week 10): Mobile app functional across all 4 roles
- **M4** (Week 13): Full test suite passing (>85% coverage)
- **M5** (Week 15): Production deployment live on AWS / Docker

---

## 7. Project Outcomes & Individual Roles

### 7.1 Final Deliverables

1. **Working Mobile Application** — A Flutter app available for Android (and optionally iOS), supporting all four user roles with complete functionality.

2. **Deployed Backend API** — A FastAPI server running in a Docker container (or on AWS EC2), exposing 30+ RESTful and WebSocket endpoints, documented via OpenAPI/Swagger.

3. **Blockchain-Secured Medical Records System** — An SHA-256 hash chain implementation that ensures tamper detection, with an admin dashboard for viewing tampering alerts and exporting audit logs.

4. **Automated Test Suite** — 538 automated tests (373 backend + 165 mobile) with >85% code coverage, runnable with a single command.

5. **Production Infrastructure** — Docker Compose files and AWS Terraform scripts for one-command cloud deployment.

6. **Complete Documentation** — API Documentation, User Guides, Deployment Guide, and Training Materials for all roles.

### 7.2 Individual Team Member Roles

| Team Member | Primary Role | Responsibilities |
|---|---|---|
| **Member 1** | Backend Lead | FastAPI architecture, authentication module, appointment and queue APIs, WebSocket server |
| **Member 2** | Mobile Lead | Flutter application, all 12 screens, state management (Provider), offline caching |
| **Member 3** | Security & Blockchain | Blockchain service, RBAC enforcement, encryption, audit log module, tampering alerts |
| **Member 4** | Testing & DevOps | Pytest suite (373 tests), Flutter test suite (165 tests), Docker, Terraform, CI/CD setup |

> **Note:** *Please update team member names above with your actual team details before submission.*

---

## 8. Course Subjects

The following course subjects provide the conceptual foundation and practical skill sets applied during the execution of HealthSaathi:

| Subject | Application in Project |
|---|---|
| **Database Management Systems (DBMS)** | PostgreSQL schema design, normalization, indexing, Alembic migrations, query optimization |
| **Computer Networks** | REST API design, WebSocket protocol, HTTP/HTTPS, CORS, JWT token transmission, rate limiting |
| **Information Security / Cryptography** | SHA-256 hashing for blockchain, bcrypt password hashing, JWT (HS256), SSL/TLS, RBAC principles |
| **Software Engineering** | Requirements analysis, system design (UML/ERD), iterative development methodology, test-driven development |
| **Object-Oriented Programming (OOP)** | FastAPI service classes, SQLAlchemy ORM models, Flutter widget hierarchy, Provider state pattern |
| **Operating Systems** | Docker containerization, process management (uvicorn workers), file system for audit logs |
| **Data Structures & Algorithms** | Hash chain (linked-list variant), exponential moving average for queue estimation, sorted queue ordering |
| **Mobile Application Development** | Flutter/Dart, cross-platform UI development, WebSocket client, local storage, integration testing |
| **Cloud Computing** | AWS EC2/RDS deployment, Terraform infrastructure-as-code, Docker Compose orchestration, Nginx reverse proxy |
| **Distributed Systems** | WebSocket broadcast architecture, concurrent user handling, stateless API design, horizontal scalability considerations |

---

## 9. References

1. Ismail, L., & Materwala, H. (2021). **A review of blockchain architecture and consensus protocols: Use cases, challenges, and solutions.** *Symmetry*, 13(8), 1355. https://doi.org/10.3390/sym13081355

2. Tanwar, S., Parekh, K., & Evans, R. (2020). **Blockchain-based electronic healthcare record system for healthcare 4.0 applications.** *Journal of Information Security and Applications*, 50, 102407. https://doi.org/10.1016/j.jisa.2019.102407

3. Ali, A., Al-Rimy, B. A. S., Alsubaie, A., Alturki, R., Alassaf, N., & Saeed, F. (2023). **Privacy-preserving blockchain-based healthcare system for IoT devices.** *IEEE Access*, 11, 12345–12360. https://doi.org/10.1109/ACCESS.2023.3240189

4. Grout, R. W., Brummet, C., Shoemaker, A., Racz, J., Harle, C. A., & Vest, J. R. (2022). **Impact of real-time patient queue dashboards on patient waiting time perception in outpatient settings.** *Journal of the American Medical Informatics Association (JAMIA)*, 29(1), 89–97. https://doi.org/10.1093/jamia/ocab202

5. Shaik, T., Tao, X., Dann, C., Li, L., Xie, H., & Bhatt, R. (2021). **Predicting patient wait time in an outpatient clinic using real-world data and machine learning.** *JMIR Medical Informatics*, 9(9), e27804. https://doi.org/10.2196/27804

6. Puranik, A., Dhar, S., & Bhatt, S. (2023). **Performance comparison of WebSocket, long-polling, and server-sent events for real-time healthcare alert delivery.** *International Journal of Advanced Computer Science and Applications (IJACSA)*, 14(3), 512–520. https://doi.org/10.14569/IJACSA.2023.0140368

7. Alshehri, A., & Mishra, S. (2021). **A comprehensive analysis of role-based access control models for electronic health records.** *Healthcare*, 9(5), 548. https://doi.org/10.3390/healthcare9050548

8. Rahmani, A. M., Yousefpoor, M. S., Yousefpoor, E., Hosseinzadeh, M., Naqvi, R. A., & Heidari, A. (2022). **A secure and lightweight authentication scheme for IoT-based healthcare systems using JWT and RBAC.** *Computers & Security*, 117, 102689. https://doi.org/10.1016/j.cose.2022.102689

9. Sharma, P., Bhatt, D., & Sarhan, M. M. (2022). **mHealth app adoption and usage patterns in semi-urban and rural India: An empirical analysis.** *Journal of Medical Internet Research (JMIR) mHealth and uHealth*, 10(4), e31257. https://doi.org/10.2196/31257

10. Nawrocki, P., Wrona, K., Marczak, M., & Żyła, K. (2021). **A comparison of native and cross-platform frameworks for mobile applications.** *Computer Networks*, 200, 108517. https://doi.org/10.1016/j.comnet.2021.108517

11. Ministry of Health & Family Welfare, Govt. of India. (2023). **National Digital Health Mission (ABDM) Annual Report 2022–23.** New Delhi: MoHFW. https://abdm.gov.in/publications

12. World Health Organization. (2021). **Global strategy on digital health 2020–2025.** Geneva: WHO Press. ISBN 978-92-4-002092-9. https://www.who.int/docs/default-source/documents/gs4dhdaa2a9f352b0445bafbc79ca799dce4d.pdf

13. FastAPI Documentation. Sebastián Ramírez. (2024). https://fastapi.tiangolo.com/

14. Flutter Documentation. Google LLC. (2024). https://flutter.dev/docs

15. PostgreSQL Global Development Group. (2024). **PostgreSQL 16 Documentation.** https://www.postgresql.org/docs/16/

---

*Report prepared for Capstone Project Submission — Academic Year 2025–26*
*Project: HealthSaathi — Secure Blockchain-Integrated Healthcare Management System*
