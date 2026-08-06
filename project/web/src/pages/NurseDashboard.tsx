import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api';
import '../styles/dashboard.css';

interface QueueStatus {
  queue_length: number;
  patients: Array<{
    appointment_id: number;
    patient_id: number;
    patient_name: string;
    queue_position: number;
    status: string;
  }>;
}

type Tab = 'queue' | 'vitals';

export default function NurseDashboard() {
  const { user, logout } = useAuthStore();
  const [tab, setTab] = useState<Tab>('queue');

  const [queue, setQueue] = useState<QueueStatus | null>(null);
  const [queueLoading, setQueueLoading] = useState(true);
  const [queueError, setQueueError] = useState('');

  const [patientId, setPatientId] = useState('');
  const [systolic, setSystolic] = useState('');
  const [diastolic, setDiastolic] = useState('');
  const [heartRate, setHeartRate] = useState('');
  const [temperature, setTemperature] = useState('');
  const [vitalsMessage, setVitalsMessage] = useState('');
  const [vitalsError, setVitalsError] = useState('');
  const [vitalsSubmitting, setVitalsSubmitting] = useState(false);

  useEffect(() => {
    loadQueue();
  }, []);

  const loadQueue = async () => {
    setQueueLoading(true);
    setQueueError('');
    try {
      const data = await apiClient.get<QueueStatus>('/queue/status');
      setQueue(data);
    } catch (err) {
      setQueueError(err instanceof Error ? err.message : 'Failed to load queue');
    } finally {
      setQueueLoading(false);
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
          <button
            className={`tab-button ${tab === 'queue' ? 'active' : ''}`}
            onClick={() => setTab('queue')}
          >
            Patient Queue
          </button>
          <button
            className={`tab-button ${tab === 'vitals' ? 'active' : ''}`}
            onClick={() => setTab('vitals')}
          >
            Record Vitals
          </button>
        </div>

        {tab === 'queue' && (
          <section className="queue-section">
            <h2>Patient Queue</h2>
            {queueError && <div className="error-message">{queueError}</div>}
            {queueLoading ? (
              <div className="loading">Loading queue...</div>
            ) : queue ? (
              <div className="queue-display">
                <p className="queue-count">
                  Patients in queue: <strong>{queue.queue_length}</strong>
                </p>
                {queue.patients.length > 0 ? (
                  <div className="patient-list">
                    {queue.patients.map((patient) => (
                      <div key={patient.appointment_id} className="patient-card">
                        <div className="position">{patient.queue_position}</div>
                        <div className="info">
                          <h3>{patient.patient_name}</h3>
                          <p className="status">{patient.status}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="no-patients">No patients in queue</p>
                )}
                <button onClick={loadQueue} className="refresh-button">
                  Refresh Queue
                </button>
              </div>
            ) : null}
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
