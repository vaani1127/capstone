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

export default function DoctorDashboard() {
  const { user, logout } = useAuthStore();
  const [queue, setQueue] = useState<QueueStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadQueue();
  }, []);

  const loadQueue = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await apiClient.get<QueueStatus>('/queue/status');
      setQueue(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load queue');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Welcome, Dr. {user?.name}</h1>
        <button onClick={logout} className="logout-button">
          Logout
        </button>
      </header>

      <main className="dashboard-content">
        <section className="queue-section">
          <h2>Patient Queue</h2>

          {error && <div className="error-message">{error}</div>}

          {loading ? (
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
      </main>
    </div>
  );
}
