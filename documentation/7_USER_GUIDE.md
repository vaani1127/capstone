# User Guide & Training

Complete guide for all user roles with feature walkthroughs and best practices.

## Table of Contents

1. [Patient Guide](#patient-user-guide)
2. [Doctor Guide](#doctor-user-guide)
3. [Nurse Guide](#nurse-user-guide)
4. [Admin Guide](#admin-user-guide)

---

## Patient User Guide

### Getting Started

#### Creating Your Account

1. Open HealthSaathi app
2. Tap "Register" on login screen
3. Fill in your details:
   - Full Name
   - Email Address
   - Password (minimum 8 characters with uppercase, lowercase, number)
   - Date of Birth
   - Gender
   - Phone Number
   - Address
   - Blood Group (optional)
4. Tap "Create Account"
5. Login with your credentials

#### Dashboard Overview

Your patient dashboard shows:
- **Quick Actions** - Book appointment, view queue, medical history
- **Upcoming Appointments** - Scheduled appointments with times
- **Recent Medical Records** - Latest consultation notes
- **Profile Section** - Your personal information

### Booking Appointments

1. Tap **"Book Appointment"** on dashboard
2. **Select Doctor**
   - Browse by specialization (General, Cardiology, Pediatrics, etc.)
   - View doctor's qualifications and experience
   - See current queue length for wait time estimate
3. **Choose Date & Time**
   - View available time slots
   - Select preferred appointment time
4. **Confirm Booking**
   - Review appointment details
   - Tap "Confirm"
   - Receive confirmation with appointment ID
5. **Notification**
   - You'll receive SMS/app notification before appointment

### Checking Queue Status

1. Tap **"Queue Status"** on dashboard
2. Select your doctor or current appointment
3. View:
   - Your current queue position
   - Estimated wait time
   - Number of patients ahead
   - Real-time updates via WebSocket

The queue position updates automatically every few seconds!

### Appointment Management

**Cancel Appointment**
1. Open "Upcoming Appointments"
2. Find appointment to cancel
3. Tap "Cancel"
4. Confirm cancellation
5. Cancellation must be at least 2 hours before appointment

**Reschedule Appointment**
1. Open "Upcoming Appointments"
2. Tap appointment and select "Reschedule"
3. Choose new date/time
4. Confirm changes

### Accessing Medical Records

1. Tap **"Medical History"** on dashboard
2. Browse past consultations (newest first)
3. Tap any record to view:
   - Consultation notes from doctor
   - Diagnosis information
   - Prescribed medications
   - Follow-up instructions
4. **Download/Share**
   - Download record as PDF
   - Share with other healthcare providers

### Managing Your Profile

1. Tap **Profile icon** → Settings
2. Update personal information
3. Manage privacy settings:
   - Who can access your records
   - Notification preferences
   - Data sharing options
4. **Security**
   - Change password
   - Enable two-factor authentication
   - View login history

---

## Doctor User Guide

### Getting Started

**Dashboard Overview**
- **Patient Queue** - Real-time list of patients waiting
- **Today's Appointments** - Scheduled consultations
- **Quick Stats** - Number of patients seen today
- **Medical Records** - Quick access to previous patient records

### Managing Your Queue

1. Tap **"Patient Queue"** on dashboard
2. View patients in order (queue position)
3. For each patient:
   - Name and registration number
   - Reason for visit (if available)
   - Time waited
   - Patient's medical history link

**Checking In Patient**
1. Select patient from queue
2. Tap "Check In"
3. Patient status changes to "In Progress"
4. Next patient queues automatically

### Consultation Process

**Creating Medical Record**
1. Patient checked in
2. Tap "Create Consultation Note"
3. Enter:
   - **Complaint**: What brought patient in
   - **Vitals**: Blood pressure, temperature, etc.
   - **Examination**: Physical examination findings
   - **Diagnosis**: Your diagnosis
   - **Treatment Plan**: Medications and follow-up
4. **Add Prescription**
   - Select medications from database
   - Enter dosage and duration
   - Add special instructions
5. **Save Record**
   - Record automatically pushed to blockchain
   - Audit trail created
   - Patient receives notification
6. **Mark Complete**
   - Tap "End Consultation"
   - Patient moves out of queue
   - Next patient called automatically

### Accessing Patient History

1. Tap **"Patient Records"** on dashboard
2. Search patient by name or ID
3. View:
   - Demographic information
   - Past consultation notes (chronologically)
   - Medication history
   - Allergies and blood type
4. Use history to understand patient context

### My Statistics

View:
- Patients seen today/this week/this month
- Average consultation duration
- Queue efficiency metrics
- Patient satisfaction ratings

### Best Practices

- **Always verify patient identity** before creating records
- **Update medical records promptly** while details are fresh
- **Check patient allergies** before prescribing medications
- **Document thoroughly** - clear notes help continuity of care
- **Review previous visits** - context improves care quality

---

## Nurse User Guide

### Getting Started

**Dashboard Overview**
- **Walk-in Registration** - Register new patients
- **Doctor Queues** - View all doctor queues
- **Queue Management** - Update patient statuses
- **Check-in Counter** - Manage patient check-ins

### Walk-in Patient Registration

1. Tap **"Register Walk-in"** on dashboard
2. Enter patient details:
   - Full Name
   - Phone Number
   - Date of Birth
   - Gender
   - Blood Group
   - Chief Complaint (optional)
3. Tap "Create Account"
4. System generates temporary patient ID
5. Patient added to selected doctor's queue

**For Returning Patients**
1. Tap "Returning Patient" option
2. Search by email or phone
3. Confirm patient identity
4. Add to doctor queue

### Queue Management

**Update Patient Status**
1. View doctor queue
2. For each patient, options:
   - "Check In" - Patient arrived
   - "In Progress" - Patient with doctor
   - "Complete" - Consultation done
3. Tap status to update
4. Queue automatically reorders

**Monitor Queue**
- View all doctors' queues simultaneously
- Identify bottlenecks
- Help manage overall clinic flow

### Patient Check-in at Counter

1. Patient arrives and reports to center
2. Tap "Check In" in app
3. Scan patient ID or search by name
4. Verify patient identity (name, DOB)
5. Mark "Checked In"
6. Patient can now view real-time queue position

### Handling Issues

**Patient Doesn't Appear After Call**
- Mark as "No Show"
- System automatically moves to next patient
- Record kept for statistics

**Emergency/Priority Patient**
- Tap "Priority Check-in"
- Move to top of queue
- Doctor notified

**Duplicate Registration**
- Search before registering new walk-in
- Merge records if duplicate found

### Best Practices

- Register patients with **accurate information**
- Use **clear, legible handwriting** on forms
- Check **ID/proof** before registration
- Maintain **patient privacy** during registration
- Keep queue **smoothly flowing** by updating statuses promptly

---

## Admin User Guide

### Getting Started

**Dashboard Overview**
- **User Management** - Create and manage users
- **System Statistics** - Usage metrics and trends
- **Audit Logs** - All system activity
- **Alerts** - System alerts and tampering warnings

### User Management

**Create New User**
1. Tap **"Users"** → "Create User"
2. Enter details:
   - Name, Email, Phone
   - Select Role: Admin, Doctor, Nurse, or Patient
   - Set temporary password
3. Tap "Create"
4. User receives activation email

**Manage Users**
1. View all users in system
2. Filter by role
3. For each user:
   - View profile and activity
   - Reset password
   - Deactivate/Reactivate account
   - Change role
   - Delete (irreversible)

**Doctor Profiles**
1. For new doctors, add specialization
2. Set average consultation duration
3. Configure availability/schedules
4. View performance metrics

### Audit & Compliance

**View Audit Logs**
1. Tap **"Audit Logs"**
2. Filter by:
   - Date range
   - User
   - Action type
   - Resource type
3. View complete record of:
   - Who accessed what
   - When they accessed it
   - What changes were made
   - From which IP address

**Tampering Alerts**
1. Tap **"Security"** → "Tampering Alerts"
2. View medical records with detected tampering
3. For each alert:
   - See what was modified
   - View before/after values
   - Identify who made changes
   - View blockchain verification status
4. **Respond to Alert**
   - Investigate unauthorized changes
   - Rollback if necessary
   - Contact affected parties

### System Monitoring

**Dashboard Statistics**
- Total users by role
- Daily appointment volume
- Queue utilization rate
- Average wait times
- System uptime
- Database size

**Performance Metrics**
- API response times
- Queue operation speed
- Medical record access speed
- Blockchain verification performance

### Backup & Recovery

**Database Backups**
- View last backup timestamp
- Schedule regular backups
- Download backup file
- Test restore process

**System Recovery**
- In case of issues
- Follow restoration procedures
- Verify data integrity
- Notify users of any outage

### Security Management

**Password Policies**
- Set minimum password length
- Require complexity (uppercase, lowercase, numbers)
- Set password expiry (optional)

**Session Management**
- View active sessions
- Force logout if needed
- Set session timeout duration

**API Tokens**
- Review active API tokens
- Revoke compromised tokens
- Monitor token usage

### Best Practices

- **Regular backups** - Ensure data protection
- **Monitor audit logs** - Catch suspicious activity early
- **Respond to alerts** - Investigate tampering immediately
- **User role review** - Ensure appropriate permissions
- **System maintenance** - Schedule updates during off-hours
- **Data privacy** - Never access patient data unnecessarily

---

## Training Checklist

### For New Patients
- ✅ Account creation
- ✅ Booking first appointment
- ✅ Checking queue status
- ✅ Accessing medical records
- ✅ Managing profile

### For New Doctors
- ✅ Dashboard navigation
- ✅ Viewing patient queue
- ✅ Creating medical records
- ✅ Prescribing medications
- ✅ Retrieving patient history

### For New Nurses
- ✅ Walk-in registration
- ✅ Queue management
- ✅ Patient check-in
- ✅ Status updates
- ✅ Emergency procedures

### For New Admins
- ✅ User management basics
- ✅ Viewing audit logs
- ✅ Understanding tampering alerts
- ✅ Backup procedures
- ✅ Emergency contacts

---

## Common Questions

**Q: How do I reset my password?**  
A: Tap "Forgot Password" on login screen, enter email, follow recovery link.

**Q: What if I miss my appointment?**  
A: You can reschedule up to 2 hours after appointment time, otherwise contact admin.

**Q: How are my medical records protected?**  
A: Records are blockchain-backed, encrypted, and access is strictly controlled by role.

**Q: Can I access my records from the web?**  
A: Currently available on mobile app only. Web portal coming soon.

**Q: How often are backups performed?**  
A: Daily at 2 AM. Contact admin if data recovery needed.

---

For technical setup, see [1_QUICK_START.md](1_QUICK_START.md)  
For API details, see [4_API_DOCUMENTATION.md](4_API_DOCUMENTATION.md)
