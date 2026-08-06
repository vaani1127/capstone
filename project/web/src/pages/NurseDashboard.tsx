import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api';
import '../styles/dashboard.css';

interface QueueStatus {
  total_queue_length: number;
  patients: Array<{
    appointment_id: number;
    patient_id: number;
    patient_name: string;
    queue_position: number;
    status: string;
    estimated_wait_time?: number;
  }>;
}

interface Appointment {
  id: number;
  doctor_id: number;
  doctor_name?: string;
  patient_name?: string;
  scheduled_time: string;
  status: string;
  appointment_type: string;
  queue_position: number | null;
}

interface Doctor {
  id: number;
  name: string;
  specialization?: string;
}

type Tab = 'home' | 'walkin' | 'vitals';

const statusLabel: Record<string, string> = {
  scheduled: 'Scheduled',
  checked_in: 'Checked In',
  in_progress: 'In Progress',
  completed: 'Completed',
  no_show: 'No-Show',
};

export default function NurseDashboard() {
  const { user, logout } = useAuthStore();
  const [tab, setTab] = useState<Tab>('home');

  const [todayAppointments, setTodayAppointments] = useState<Appointment[]>([]);
  const [doctorQueues, setDoctorQueues] = useState<Array<{ doctor_id: number; doctor_name: string; queue: QueueStatus }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Walk-in form state
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [selectedDoctor, setSelectedDoctor] = useState('');
  const [patientName, setPatientName] = useState('');
  const [patientEmail, setPatientEmail] = useState('');
  const [patientPhone, setPatientPhone] = useState('');
  const [dob, setDob] = useState('');
  const [gender, setGender] = useState('');
  const [address, setAddress] = useState('');
  const [bloodGroup, setBloodGroup] = useState('');
  const [walkInSubmitting, setWalkInSubmitting] = useState(false);
  const [walkInMessage, setWalkInMessage] = useState('');
  const [walkInError, setWalkInError] = useState('');

  // Vitals form state
  const [patientId, setPatientId] = useState('');
  const [systolic, setSystolic] = useState('');
  const [diastolic, setDiastolic] = useState('');
  const [heartRate, setHeartRate] = useState('');
  const [temperature, setTemperature] = useState('');
  const [vitalsMessage, setVitalsMessage] = useState('');
  const [vitalsError, setVitalsError] = useState('');
  const [vitalsSubmitting, setVitalsSubmitting] = useState(false);

  useEffect(() => {
    loadData();
    loadDoctors();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const appts = await apiClient.get<Appointment[]>('/appointments/');
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);

      const filtered = appts
        .filter((a) => {
          const t = new Date(a.scheduled_time);
          return a.status !== 'cancelled' && t >= today && t < tomorrow;
        })
        .sort((a, b) => new Date(a.scheduled_time).getTime() - new Date(b.scheduled_time).getTime());
      setTodayAppointments(filtered);

      const doctorIds = Array.from(new Set(filtered.map((a) => a.doctor_id)));
      const queues: Array<{ doctor_id: number; doctor_name: string; queue: QueueStatus }> = [];
      for (const doctorId of doctorIds) {
        try {
          const q = await apiClient.get<QueueStatus & { doctor_name?: string }>(`/queue/doctor/${doctorId}`);
          queues.push({ doctor_id: doctorId, doctor_name: q.doctor_name || 'Doctor', queue: q });
        } catch {
          // continue loading other doctors
        }
      }
      setDoctorQueues(queues);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const loadDoctors = async () => {
    try {
      const data = await apiClient.get<Doctor[]>('/users/doctors');
      setDoctors(data);
    } catch {
      // ignore — walk-in tab will show empty doctor list
    }
  };

  const submitWalkIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoctor) {
      setWalkInError('Please select a doctor');
      return;
    }
    setWalkInSubmitting(true);
    setWalkInError('');
    setWalkInMessage('');
    try {
      const result = await apiClient.post<{ queue_position: number; estimated_wait_time?: number }>(
        '/appointments/walk-in',
        {
          doctor_id: Number(selectedDoctor),
          patient_name: patientName,
          patient_email: patientEmail || undefined,
          patient_phone: patientPhone || undefined,
          date_of_birth: dob || undefined,
          gender: gender || undefined,
          address: address || undefined,
          blood_group: bloodGroup || undefined,
        }
      );
      setWalkInMessage(
        `Registered successfully! Queue position: ${result.queue_position}${
          result.estimated_wait_time ? `, estimated wait: ${result.estimated_wait_time} min` : ''
        }`
      );
      setPatientName('');
      setPatientEmail('');
      setPatientPhone('');
      setDob('');
      setGender('');
      setAddress('');
      setBloodGroup('');
      setSelectedDoctor('');
      loadData();
    } catch (err) {
      setWalkInError(err instanceof Error ? err.message : 'Failed to register walk-in patient');
    } finally {
      setWalkInSubmitting(false);
    }
  };

  const submitVitals = async (e: React.FormEvent) => {
    e.preventDefault();
    setVitalsSubmitting(true);
    setVitalsError('');
    setVitalsMessage('');

    try {
      await apiClient.post('/vitals/', {
        patient_id: Number(patientId),
        systolic_bp: systolic ? Number(systolic) : undefined,
        diastolic_bp: diastolic ? Number(diastolic) : undefined,
        heart_rate: heartRate ? Number(heartRate) : undefined,
        temperature: temperature ? Number(temperature) : undefined,
      });
      setVitalsMessage('Vitals recorded successfully');
      setPatientId('');
      setSystolic('');
      setDiastolic('');
      setHeartRate('');
      setTemperature('');
    } catch (err) {
      setVitalsError(err instanceof Error ? err.message : 'Failed to record vitals');
    } finally {
      setVitalsSubmitting(false);
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
          <button className={`tab-button ${tab === 'walkin' ? 'active' : ''}`} onClick={() => setTab('walkin')}>
            Walk-in Registration
          </button>
          <button className={`tab-button ${tab === 'vitals' ? 'active' : ''}`} onClick={() => setTab('vitals')}>
            Record Vitals
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        {tab === 'home' && (
          <>
            <section className="queue-section">
              <h2>Queue Status - All Doctors</h2>
              {loading ? (
                <div className="loading">Loading...</div>
              ) : doctorQueues.length === 0 ? (
                <p className="no-patients">No patients in queue. All queues are clear!</p>
              ) : (
                <div className="patient-list">
                  {doctorQueues.map(({ doctor_id, doctor_name, queue }) => (
                    <div key={doctor_id} className="patient-card" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                        <h3>Dr. {doctor_name}</h3>
                        <span className="queue-count">{queue.total_queue_length} in queue</span>
                      </div>
                      {queue.patients.slice(0, 2).map((p) => (
                        <p key={p.appointment_id} className="status">
                          #{p.queue_position} {p.patient_name} — ~{p.estimated_wait_time ?? 0} min
                        </p>
                      ))}
                      {queue.patients.length > 2 && (
                        <p className="status">+{queue.patients.length - 2} more in queue</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h2>Today's Appointments</h2>
              {todayAppointments.length === 0 ? (
                <p className="no-patients">No appointments today</p>
              ) : (
                <div className="patient-list">
                  {todayAppointments.map((appt) => (
                    <div key={appt.id} className="patient-card">
                      <div className="info">
                        <h3>{appt.patient_name || 'Patient'}</h3>
                        <p className="status">
                          Dr. {appt.doctor_name || 'Doctor'} ·{' '}
                          {new Date(appt.scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                        <span className={`role-badge role-${appt.status}`}>{statusLabel[appt.status] || appt.status}</span>
                        {appt.queue_position !== null && (
                          <p className="queue-count">Queue Position: {appt.queue_position}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}

        {tab === 'walkin' && (
          <section>
            <h2>Walk-in Patient Registration</h2>
            {walkInError && <div className="error-message">{walkInError}</div>}
            {walkInMessage && <div className="success-message">{walkInMessage}</div>}
            <form onSubmit={submitWalkIn} className="vitals-form">
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
              <div className="form-group">
                <label>Full Name *</label>
                <input value={patientName} onChange={(e) => setPatientName(e.target.value)} required />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Email (Optional)</label>
                  <input type="email" value={patientEmail} onChange={(e) => setPatientEmail(e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Phone (Optional)</label>
                  <input value={patientPhone} onChange={(e) => setPatientPhone(e.target.value)} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Date of Birth (Optional)</label>
                  <input type="date" value={dob} onChange={(e) => setDob(e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Gender (Optional)</label>
                  <select value={gender} onChange={(e) => setGender(e.target.value)}>
                    <option value="">Select</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Blood Group (Optional)</label>
                  <select value={bloodGroup} onChange={(e) => setBloodGroup(e.target.value)}>
                    <option value="">Select</option>
                    {['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-'].map((bg) => (
                      <option key={bg} value={bg}>{bg}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Address (Optional)</label>
                  <input value={address} onChange={(e) => setAddress(e.target.value)} />
                </div>
              </div>
              <button type="submit" className="refresh-button" disabled={walkInSubmitting}>
                {walkInSubmitting ? 'Registering...' : 'Register Walk-in Patient'}
              </button>
            </form>
          </section>
        )}

        {tab === 'vitals' && (
          <section>
            <h2>Record Patient Vitals</h2>
            {vitalsError && <div className="error-message">{vitalsError}</div>}
            {vitalsMessage && <div className="success-message">{vitalsMessage}</div>}
            <form onSubmit={submitVitals} className="vitals-form">
              <div className="form-group">
                <label htmlFor="patientId">Patient ID</label>
                <input
                  id="patientId"
                  type="number"
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  required
                  disabled={vitalsSubmitting}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="systolic">Systolic BP</label>
                  <input
                    id="systolic"
                    type="number"
                    value={systolic}
                    onChange={(e) => setSystolic(e.target.value)}
                    disabled={vitalsSubmitting}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="diastolic">Diastolic BP</label>
                  <input
                    id="diastolic"
                    type="number"
                    value={diastolic}
                    onChange={(e) => setDiastolic(e.target.value)}
                    disabled={vitalsSubmitting}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="heartRate">Heart Rate</label>
                  <input
                    id="heartRate"
                    type="number"
                    value={heartRate}
                    onChange={(e) => setHeartRate(e.target.value)}
                    disabled={vitalsSubmitting}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="temperature">Temperature (°F)</label>
                  <input
                    id="temperature"
                    type="number"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(e.target.value)}
                    disabled={vitalsSubmitting}
                  />
                </div>
              </div>

              <button type="submit" className="refresh-button" disabled={vitalsSubmitting}>
                {vitalsSubmitting ? 'Saving...' : 'Record Vitals'}
              </button>
            </form>
          </section>
        )}
      </main>
    </div>
  );
}
