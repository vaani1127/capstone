import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api';
import '../styles/dashboard.css';

interface Appointment {
  id: number;
  doctor_name?: string;
  doctor_specialization?: string;
  scheduled_time: string;
  status: string;
  queue_position: number | null;
  estimated_wait_time?: number | null;
}

interface MedicalRecord {
  id: number;
  diagnosis?: string;
  consultation_notes?: string;
  prescription?: string;
  created_at: string;
}

type Tab = 'appointments' | 'records';

export default function PatientDashboard() {
  const { user, logout } = useAuthStore();
  const [tab, setTab] = useState<Tab>('appointments');

  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [apptLoading, setApptLoading] = useState(true);
  const [apptError, setApptError] = useState('');

  const [records, setRecords] = useState<MedicalRecord[]>([]);
  const [recordsLoading, setRecordsLoading] = useState(true);
  const [recordsError, setRecordsError] = useState('');

  useEffect(() => {
    loadAppointments();
    loadRecords();
  }, []);

  const loadAppointments = async () => {
    setApptLoading(true);
    setApptError('');
    try {
      const data = await apiClient.get<Appointment[]>('/appointments/');
      setAppointments(data);
    } catch (err) {
      setApptError(err instanceof Error ? err.message : 'Failed to load appointments');
    } finally {
      setApptLoading(false);
    }
  };

  const loadRecords = async () => {
    setRecordsLoading(true);
    setRecordsError('');
    try {
      const data = await apiClient.get<MedicalRecord[]>('/medical-records/me');
      setRecords(data);
    } catch (err) {
      setRecordsError(err instanceof Error ? err.message : 'Failed to load medical records');
    } finally {
      setRecordsLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Welcome, {user?.name}</h1>
        <button onClick={logout} className="logout-button">
          Logout
        </button>
      </header>

      <main className="dashboard-content">
        <div className="tabs">
          <button
            className={`tab-button ${tab === 'appointments' ? 'active' : ''}`}
            onClick={() => setTab('appointments')}
          >
            My Appointments
          </button>
          <button
            className={`tab-button ${tab === 'records' ? 'active' : ''}`}
            onClick={() => setTab('records')}
          >
            Medical Records
          </button>
        </div>

        {tab === 'appointments' && (
          <section>
            <h2>My Appointments</h2>
            {apptError && <div className="error-message">{apptError}</div>}
            {apptLoading ? (
              <div className="loading">Loading appointments...</div>
            ) : appointments.length === 0 ? (
              <p className="no-patients">No appointments found</p>
            ) : (
              <div className="patient-list">
                {appointments.map((appt) => (
                  <div key={appt.id} className="patient-card">
                    <div className="info">
                      <h3>{appt.doctor_name || 'Doctor'}</h3>
                      <p className="status">{appt.doctor_specialization}</p>
                      <p>{new Date(appt.scheduled_time).toLocaleString()}</p>
                      <span className={`role-badge role-${appt.status}`}>{appt.status}</span>
                      {appt.queue_position !== null && (
                        <p className="queue-count">Queue position: {appt.queue_position}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {tab === 'records' && (
          <section>
            <h2>Medical Records</h2>
            {recordsError && <div className="error-message">{recordsError}</div>}
            {recordsLoading ? (
              <div className="loading">Loading records...</div>
            ) : records.length === 0 ? (
              <p className="no-patients">No medical records found</p>
            ) : (
              <div className="patient-list">
                {records.map((record) => (
                  <div key={record.id} className="alert-card">
                    <div className="alert-info">
                      <h3>{record.diagnosis || 'Consultation'}</h3>
                      {record.consultation_notes && <p>{record.consultation_notes}</p>}
                      {record.prescription && <p><strong>Prescription:</strong> {record.prescription}</p>}
                      <p className="alert-time">{new Date(record.created_at).toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
