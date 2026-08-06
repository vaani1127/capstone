import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api';
import '../styles/dashboard.css';

interface Appointment {
  id: number;
  doctor_id: number;
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

interface Doctor {
  id: number;
  name: string;
  specialization?: string;
}

interface Procedure {
  id: number;
  description: string;
  performed_at: string;
  outcome?: string;
  performed_by_name?: string;
}

interface Vitals {
  id: number;
  recorded_at: string;
  systolic_bp?: number;
  diastolic_bp?: number;
  heart_rate?: number;
  temperature?: number;
}

interface QueueStatus {
  total_queue_length: number;
  patients: Array<{
    appointment_id: number;
    patient_name: string;
    queue_position: number;
    estimated_wait_time?: number;
  }>;
}

type Tab = 'home' | 'book' | 'records' | 'procedures' | 'queue' | 'vitals';

const statusLabel: Record<string, string> = {
  scheduled: 'Scheduled',
  checked_in: 'Checked In',
  in_progress: 'In Progress',
  completed: 'Completed',
  no_show: 'No-Show',
  cancelled: 'Cancelled',
};

export default function PatientDashboard() {
  const { user, logout } = useAuthStore();
  const [tab, setTab] = useState<Tab>('home');

  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [apptLoading, setApptLoading] = useState(true);
  const [apptError, setApptError] = useState('');

  const [records, setRecords] = useState<MedicalRecord[]>([]);
  const [recordsLoading, setRecordsLoading] = useState(true);
  const [recordsError, setRecordsError] = useState('');

  // Booking state
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [selectedDoctor, setSelectedDoctor] = useState('');
  const [bookDate, setBookDate] = useState('');
  const [bookTime, setBookTime] = useState('');
  const [booking, setBooking] = useState(false);
  const [bookMessage, setBookMessage] = useState('');
  const [bookError, setBookError] = useState('');

  // Procedures state
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [proceduresLoading, setProceduresLoading] = useState(true);
  const [proceduresError, setProceduresError] = useState('');

  // Queue status state
  const [queueDoctorId, setQueueDoctorId] = useState('');
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null);
  const [queueLoading, setQueueLoading] = useState(false);
  const [queueError, setQueueError] = useState('');

  // Vitals history state
  const [vitals, setVitals] = useState<Vitals[]>([]);
  const [vitalsLoading, setVitalsLoading] = useState(true);
  const [vitalsError, setVitalsError] = useState('');

  useEffect(() => {
    loadAppointments();
    loadRecords();
    loadDoctors();
    loadProcedures();
    loadVitals();
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

  const loadDoctors = async () => {
    try {
      const data = await apiClient.get<Doctor[]>('/users/doctors');
      setDoctors(data);
    } catch {
      // ignore
    }
  };

  const loadProcedures = async () => {
    setProceduresLoading(true);
    setProceduresError('');
    try {
      const data = await apiClient.get<{ procedures: Procedure[] }>('/procedures/me');
      setProcedures(data.procedures);
    } catch (err) {
      setProceduresError(err instanceof Error ? err.message : 'Failed to load procedures');
    } finally {
      setProceduresLoading(false);
    }
  };

  const loadVitals = async () => {
    setVitalsLoading(true);
    setVitalsError('');
    try {
      const data = await apiClient.get<{ vitals: Vitals[] }>('/vitals/me');
      setVitals(data.vitals);
    } catch (err) {
      setVitalsError(err instanceof Error ? err.message : 'Failed to load vitals history');
    } finally {
      setVitalsLoading(false);
    }
  };

  const loadQueueStatus = async () => {
    if (!queueDoctorId) return;
    setQueueLoading(true);
    setQueueError('');
    try {
      const data = await apiClient.get<QueueStatus>(`/queue/doctor/${queueDoctorId}`);
      setQueueStatus(data);
    } catch (err) {
      setQueueError(err instanceof Error ? err.message : 'Failed to load queue status');
    } finally {
      setQueueLoading(false);
    }
  };

  const bookAppointment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoctor || !bookDate || !bookTime) {
      setBookError('Please select doctor, date, and time');
      return;
    }
    setBooking(true);
    setBookError('');
    setBookMessage('');
    try {
      const scheduledTime = new Date(`${bookDate}T${bookTime}:00`).toISOString();
      await apiClient.post('/appointments/', {
        doctor_id: Number(selectedDoctor),
        scheduled_time: scheduledTime,
      });
      setBookMessage('Appointment booked successfully!');
      setSelectedDoctor('');
      setBookDate('');
      setBookTime('');
      loadAppointments();
    } catch (err) {
      setBookError(err instanceof Error ? err.message : 'Failed to book appointment');
    } finally {
      setBooking(false);
    }
  };

  const cancelAppointment = async (id: number) => {
    try {
      await apiClient.delete(`/appointments/${id}`);
      loadAppointments();
    } catch (err) {
      setApptError(err instanceof Error ? err.message : 'Failed to cancel appointment');
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
          <button className={`tab-button ${tab === 'home' ? 'active' : ''}`} onClick={() => setTab('home')}>
            Home
          </button>
          <button className={`tab-button ${tab === 'book' ? 'active' : ''}`} onClick={() => setTab('book')}>
            Book Appointment
          </button>
          <button className={`tab-button ${tab === 'records' ? 'active' : ''}`} onClick={() => setTab('records')}>
            Medical Records
          </button>
          <button className={`tab-button ${tab === 'procedures' ? 'active' : ''}`} onClick={() => setTab('procedures')}>
            Procedures
          </button>
          <button className={`tab-button ${tab === 'queue' ? 'active' : ''}`} onClick={() => setTab('queue')}>
            Queue Status
          </button>
          <button className={`tab-button ${tab === 'vitals' ? 'active' : ''}`} onClick={() => setTab('vitals')}>
            Vitals History
          </button>
        </div>

        {tab === 'home' && (
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
                      <span className={`role-badge role-${appt.status}`}>{statusLabel[appt.status] || appt.status}</span>
                      {appt.queue_position !== null && (
                        <p className="queue-count">Queue position: {appt.queue_position}</p>
                      )}
                    </div>
                    {appt.status === 'scheduled' && (
                      <button className="ack-button" style={{ background: '#c62828' }} onClick={() => cancelAppointment(appt.id)}>
                        Cancel
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {tab === 'book' && (
          <section>
            <h2>Book an Appointment</h2>
            {bookError && <div className="error-message">{bookError}</div>}
            {bookMessage && <div className="success-message">{bookMessage}</div>}
            <form onSubmit={bookAppointment} className="vitals-form">
              <div className="form-group">
                <label>Doctor *</label>
                <select value={selectedDoctor} onChange={(e) => setSelectedDoctor(e.target.value)} required>
                  <option value="">Select a doctor</option>
                  {doctors.map((d) => (
                    <option key={d.id} value={d.id}>
                      Dr. {d.name} {d.specialization ? `(${d.specialization})` : ''}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Date *</label>
                  <input type="date" value={bookDate} onChange={(e) => setBookDate(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Time *</label>
                  <input type="time" value={bookTime} onChange={(e) => setBookTime(e.target.value)} required />
                </div>
              </div>
              <button type="submit" className="refresh-button" disabled={booking}>
                {booking ? 'Booking...' : 'Book Appointment'}
              </button>
            </form>
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

        {tab === 'procedures' && (
          <section>
            <h2>Procedure History</h2>
            {proceduresError && <div className="error-message">{proceduresError}</div>}
            {proceduresLoading ? (
              <div className="loading">Loading procedures...</div>
            ) : procedures.length === 0 ? (
              <p className="no-patients">No procedures on record</p>
            ) : (
              <div className="patient-list">
                {procedures.map((p) => (
                  <div key={p.id} className="alert-card">
                    <div className="alert-info">
                      <h3>{p.description}</h3>
                      {p.outcome && <p>Outcome: {p.outcome}</p>}
                      {p.performed_by_name && <p>By: {p.performed_by_name}</p>}
                      <p className="alert-time">{new Date(p.performed_at).toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {tab === 'queue' && (
          <section>
            <h2>Queue Status</h2>
            <div className="form-row">
              <div className="form-group">
                <label>Doctor</label>
                <select value={queueDoctorId} onChange={(e) => setQueueDoctorId(e.target.value)}>
                  <option value="">Select a doctor</option>
                  {doctors.map((d) => (
                    <option key={d.id} value={d.id}>
                      Dr. {d.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group" style={{ justifyContent: 'flex-end' }}>
                <button type="button" className="refresh-button" onClick={loadQueueStatus}>
                  Check Queue
                </button>
              </div>
            </div>
            {queueError && <div className="error-message">{queueError}</div>}
            {queueLoading ? (
              <div className="loading">Loading queue...</div>
            ) : queueStatus ? (
              <div className="patient-list">
                <p className="queue-count">{queueStatus.total_queue_length} patients waiting</p>
                {queueStatus.patients.map((p) => (
                  <div key={p.appointment_id} className="patient-card">
                    <div className="position">{p.queue_position}</div>
                    <div className="info">
                      <h3>{p.patient_name}</h3>
                      <p className="status">Wait: ~{p.estimated_wait_time ?? 0} min</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-patients">Select a doctor to check queue status</p>
            )}
          </section>
        )}

        {tab === 'vitals' && (
          <section>
            <h2>Vitals History</h2>
            {vitalsError && <div className="error-message">{vitalsError}</div>}
            {vitalsLoading ? (
              <div className="loading">Loading vitals...</div>
            ) : vitals.length === 0 ? (
              <p className="no-patients">No vitals recorded</p>
            ) : (
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>BP</th>
                      <th>Heart Rate</th>
                      <th>Temp (°F)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vitals.map((v) => (
                      <tr key={v.id}>
                        <td>{new Date(v.recorded_at).toLocaleString()}</td>
                        <td>{v.systolic_bp && v.diastolic_bp ? `${v.systolic_bp}/${v.diastolic_bp}` : '—'}</td>
                        <td>{v.heart_rate ?? '—'}</td>
                        <td>{v.temperature ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
