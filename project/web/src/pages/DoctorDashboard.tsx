import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api';
import '../styles/dashboard.css';

interface QueuePatient {
  appointment_id: number;
  patient_id: number;
  patient_name: string;
  queue_position: number;
  status: string;
  estimated_wait_time?: number;
  appointment_type?: string;
  scheduled_time?: string;
}

interface QueueStatus {
  queue_length: number;
  patients: QueuePatient[];
}

interface Appointment {
  id: number;
  patient_id: number;
  patient_name?: string;
  scheduled_time: string;
  status: string;
  appointment_type: string;
  queue_position: number | null;
}

interface SearchPatient {
  id: number;
  name: string;
  email: string;
  phone?: string;
}

interface Allergy {
  id: number;
  allergen: string;
  reaction?: string;
  severity: string;
  onset_date?: string;
  notes?: string;
}

type Tab = 'home' | 'queue' | 'consultation' | 'search' | 'allergies';

const statusLabel: Record<string, string> = {
  scheduled: 'Scheduled',
  checked_in: 'Checked In',
  in_progress: 'In Progress',
  completed: 'Completed',
  no_show: 'No-Show',
};

export default function DoctorDashboard() {
  const { user, logout } = useAuthStore();
  const [tab, setTab] = useState<Tab>('home');

  // Home / queue shared state
  const [queue, setQueue] = useState<QueueStatus | null>(null);
  const [todayAppointments, setTodayAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updating, setUpdating] = useState(false);

  // Consultation state
  const [activeAppointment, setActiveAppointment] = useState<Appointment | null>(null);
  const [symptoms, setSymptoms] = useState('');
  const [observations, setObservations] = useState('');
  const [diagnosis, setDiagnosis] = useState('');
  const [medication, setMedication] = useState('');
  const [dosage, setDosage] = useState('');
  const [frequency, setFrequency] = useState('');
  const [duration, setDuration] = useState('');
  const [savingConsultation, setSavingConsultation] = useState(false);
  const [consultationMessage, setConsultationMessage] = useState('');

  // Patient search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchPatient[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState('');

  // Allergies state
  const [allergyPatientId, setAllergyPatientId] = useState('');
  const [allergies, setAllergies] = useState<Allergy[]>([]);
  const [allergiesLoading, setAllergiesLoading] = useState(false);
  const [allergiesError, setAllergiesError] = useState('');
  const [newAllergen, setNewAllergen] = useState('');
  const [newReaction, setNewReaction] = useState('');
  const [newSeverity, setNewSeverity] = useState('mild');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const queueData = await apiClient.get<QueueStatus>('/queue/status');
      setQueue(queueData);

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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (appointmentId: number, status: string) => {
    setUpdating(true);
    try {
      await apiClient.patch(`/appointments/${appointmentId}/status`, { status });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update status');
    } finally {
      setUpdating(false);
    }
  };

  const startConsultation = async (appointmentId: number) => {
    await updateStatus(appointmentId, 'in_progress');
    const appt = todayAppointments.find((a) => a.id === appointmentId) ||
      (queue?.patients || []).find((p) => p.appointment_id === appointmentId) as unknown as Appointment;
    if (appt) {
      setActiveAppointment(
        'patient_id' in appt
          ? (appt as Appointment)
          : {
              id: (appt as unknown as QueuePatient).appointment_id,
              patient_id: (appt as unknown as QueuePatient).patient_id,
              patient_name: (appt as unknown as QueuePatient).patient_name,
              scheduled_time: (appt as unknown as QueuePatient).scheduled_time || new Date().toISOString(),
              status: 'in_progress',
              appointment_type: (appt as unknown as QueuePatient).appointment_type || 'scheduled',
              queue_position: (appt as unknown as QueuePatient).queue_position,
            }
      );
      setTab('consultation');
      setConsultationMessage('');
    }
  };

  const saveConsultation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeAppointment) return;
    setSavingConsultation(true);
    setConsultationMessage('');
    try {
      const consultationNotes = `Symptoms: ${symptoms}\n\nObservations: ${observations}`.trim();
      await apiClient.post('/medical-records/consultation-notes', {
        patient_id: activeAppointment.patient_id,
        appointment_id: activeAppointment.id,
        consultation_notes: consultationNotes,
        diagnosis,
      });

      if (medication.trim()) {
        const prescription = `Medication: ${medication}\nDosage: ${dosage}\nFrequency: ${frequency}\nDuration: ${duration}`.trim();
        await apiClient.post('/medical-records/prescriptions', {
          patient_id: activeAppointment.patient_id,
          appointment_id: activeAppointment.id,
          prescription,
        });
      }

      await apiClient.patch(`/appointments/${activeAppointment.id}/status`, { status: 'completed' });

      setConsultationMessage('Consultation saved successfully');
      setSymptoms('');
      setObservations('');
      setDiagnosis('');
      setMedication('');
      setDosage('');
      setFrequency('');
      setDuration('');
      setActiveAppointment(null);
      loadData();
    } catch (err) {
      setConsultationMessage(err instanceof Error ? err.message : 'Failed to save consultation');
    } finally {
      setSavingConsultation(false);
    }
  };

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(() => {
      performSearch(searchQuery.trim());
    }, 400);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery]);

  const performSearch = async (query: string) => {
    setSearching(true);
    setSearchError('');
    try {
      const data = await apiClient.get<{ results: SearchPatient[] }>(
        `/patients/search?q=${encodeURIComponent(query)}`
      );
      setSearchResults(data.results);
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  const loadAllergies = async () => {
    if (!allergyPatientId) return;
    setAllergiesLoading(true);
    setAllergiesError('');
    try {
      const data = await apiClient.get<{ allergies: Allergy[] }>(`/allergies/patient/${allergyPatientId}`);
      setAllergies(data.allergies);
    } catch (err) {
      setAllergiesError(err instanceof Error ? err.message : 'Failed to load allergies');
    } finally {
      setAllergiesLoading(false);
    }
  };

  const addAllergy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!allergyPatientId || !newAllergen.trim()) return;
    try {
      await apiClient.post('/allergies/', {
        patient_id: Number(allergyPatientId),
        allergen: newAllergen,
        reaction: newReaction || undefined,
        severity: newSeverity,
      });
      setNewAllergen('');
      setNewReaction('');
      setNewSeverity('mild');
      loadAllergies();
    } catch (err) {
      setAllergiesError(err instanceof Error ? err.message : 'Failed to add allergy');
    }
  };

  const queueLength = queue?.queue_length ?? 0;
  const patients = queue?.patients ?? [];

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Dr. {user?.name}</h1>
        <button onClick={logout} className="logout-button">
          Logout
        </button>
      </header>

      <main className="dashboard-content">
        <div className="tabs">
          <button className={`tab-button ${tab === 'home' ? 'active' : ''}`} onClick={() => setTab('home')}>
            Home
          </button>
          <button className={`tab-button ${tab === 'queue' ? 'active' : ''}`} onClick={() => setTab('queue')}>
            Queue ({queueLength})
          </button>
          <button
            className={`tab-button ${tab === 'consultation' ? 'active' : ''}`}
            onClick={() => setTab('consultation')}
          >
            Consultation
          </button>
          <button className={`tab-button ${tab === 'search' ? 'active' : ''}`} onClick={() => setTab('search')}>
            Patient Search
          </button>
          <button className={`tab-button ${tab === 'allergies' ? 'active' : ''}`} onClick={() => setTab('allergies')}>
            Allergies
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        {tab === 'home' && (
          <>
            <section>
              <h2>Today's Appointments</h2>
              {loading ? (
                <div className="loading">Loading...</div>
              ) : todayAppointments.length === 0 ? (
                <p className="no-patients">No appointments today. Enjoy your day!</p>
              ) : (
                <div className="patient-list">
                  {todayAppointments.map((appt) => (
                    <div key={appt.id} className="patient-card">
                      <div className="info">
                        <h3>{appt.patient_name || 'Patient'}</h3>
                        <p className="status">
                          {new Date(appt.scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          {' · '}
                          {appt.appointment_type === 'walk_in' ? 'Walk-in' : 'Scheduled'}
                        </p>
                        <span className={`role-badge role-${appt.status}`}>
                          {statusLabel[appt.status] || appt.status}
                        </span>
                        {appt.queue_position !== null && (
                          <p className="queue-count">Queue Position: {appt.queue_position}</p>
                        )}
                      </div>
                      {(appt.status === 'checked_in' || appt.queue_position === 1) && (
                        <button className="ack-button" onClick={() => startConsultation(appt.id)} disabled={updating}>
                          Start Consultation
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}

        {tab === 'queue' && (
          <section className="queue-section">
            <h2>Queue Management</h2>
            {loading ? (
              <div className="loading">Loading queue...</div>
            ) : patients.length === 0 ? (
              <p className="no-patients">No patients in queue. You're all caught up!</p>
            ) : (
              <div className="patient-list">
                <p className="queue-count">
                  {patients.length} {patients.length === 1 ? 'patient' : 'patients'} waiting
                </p>
                {[...patients]
                  .sort((a, b) => a.queue_position - b.queue_position)
                  .map((p) => {
                    const isFirst = p.queue_position === 1;
                    const isInProgress = p.status === 'in_progress';
                    const isCheckedIn = p.status === 'checked_in';
                    const isScheduled = p.status === 'scheduled';
                    return (
                      <div key={p.appointment_id} className="patient-card">
                        <div className="position">{p.queue_position}</div>
                        <div className="info">
                          <h3>{p.patient_name}</h3>
                          <p className="status">
                            Wait: ~{p.estimated_wait_time ?? 0} min ·{' '}
                            {p.appointment_type === 'walk_in' ? 'Walk-in' : 'Scheduled'}
                          </p>
                          <span className={`role-badge role-${p.status}`}>{statusLabel[p.status] || p.status}</span>
                        </div>
                        <div style={{ display: 'flex', gap: 8 }}>
                          {!isInProgress && (isFirst || isCheckedIn) && (
                            <button className="ack-button" onClick={() => startConsultation(p.appointment_id)} disabled={updating}>
                              Start
                            </button>
                          )}
                          {isInProgress && (
                            <button
                              className="ack-button"
                              onClick={() => updateStatus(p.appointment_id, 'completed')}
                              disabled={updating}
                            >
                              Complete
                            </button>
                          )}
                          {isScheduled && (
                            <button
                              className="ack-button"
                              style={{ background: '#c62828' }}
                              onClick={() => updateStatus(p.appointment_id, 'no_show')}
                              disabled={updating}
                            >
                              Mark No-Show
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </section>
        )}

        {tab === 'consultation' && (
          <section>
            <h2>Consultation</h2>
            {!activeAppointment ? (
              <p className="no-patients">Start a consultation from Home or Queue to begin.</p>
            ) : (
              <>
                <p className="queue-count">
                  Patient: <strong>{activeAppointment.patient_name || `#${activeAppointment.patient_id}`}</strong>
                </p>
                {consultationMessage && (
                  <div className={consultationMessage.includes('success') ? 'success-message' : 'error-message'}>
                    {consultationMessage}
                  </div>
                )}
                <form onSubmit={saveConsultation} className="vitals-form">
                  <div className="form-group">
                    <label>Symptoms</label>
                    <input value={symptoms} onChange={(e) => setSymptoms(e.target.value)} placeholder="Enter patient symptoms" />
                  </div>
                  <div className="form-group">
                    <label>Observations</label>
                    <input value={observations} onChange={(e) => setObservations(e.target.value)} placeholder="Enter clinical observations" />
                  </div>
                  <div className="form-group">
                    <label>Diagnosis</label>
                    <input value={diagnosis} onChange={(e) => setDiagnosis(e.target.value)} placeholder="Enter diagnosis" required />
                  </div>
                  <div className="form-group">
                    <label>Medication Name</label>
                    <input value={medication} onChange={(e) => setMedication(e.target.value)} placeholder="e.g., Paracetamol" />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Dosage</label>
                      <input value={dosage} onChange={(e) => setDosage(e.target.value)} placeholder="e.g., 500mg" />
                    </div>
                    <div className="form-group">
                      <label>Frequency</label>
                      <input value={frequency} onChange={(e) => setFrequency(e.target.value)} placeholder="e.g., 3 times/day" />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Duration</label>
                    <input value={duration} onChange={(e) => setDuration(e.target.value)} placeholder="e.g., 5 days" />
                  </div>
                  <button type="submit" className="refresh-button" disabled={savingConsultation}>
                    {savingConsultation ? 'Saving...' : 'Save & Complete'}
                  </button>
                </form>
              </>
            )}
          </section>
        )}

        {tab === 'search' && (
          <section>
            <h2>Patient Search</h2>
            <div className="form-group">
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by name or phone number..."
                autoFocus
              />
            </div>
            {searchError && <div className="error-message">{searchError}</div>}
            {searching ? (
              <div className="loading">Searching...</div>
            ) : searchResults.length === 0 && searchQuery.trim() ? (
              <p className="no-patients">No patients found</p>
            ) : (
              <div className="patient-list">
                {searchResults.map((p) => (
                  <div key={p.id} className="patient-card">
                    <div className="info">
                      <h3>{p.name}</h3>
                      <p className="status">{p.email}{p.phone ? ` · ${p.phone}` : ''}</p>
                    </div>
                    <button
                      className="ack-button"
                      onClick={() => {
                        setAllergyPatientId(String(p.id));
                        setTab('allergies');
                      }}
                    >
                      View Allergies
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {tab === 'allergies' && (
          <section>
            <h2>Patient Allergies</h2>
            <div className="form-row">
              <div className="form-group">
                <label>Patient ID</label>
                <input
                  type="number"
                  value={allergyPatientId}
                  onChange={(e) => setAllergyPatientId(e.target.value)}
                />
              </div>
              <div className="form-group" style={{ justifyContent: 'flex-end' }}>
                <button type="button" className="refresh-button" onClick={loadAllergies}>
                  Load Allergies
                </button>
              </div>
            </div>

            {allergiesError && <div className="error-message">{allergiesError}</div>}
            {allergiesLoading ? (
              <div className="loading">Loading allergies...</div>
            ) : (
              <div className="patient-list">
                {allergies.length === 0 ? (
                  <p className="no-patients">No allergies recorded</p>
                ) : (
                  allergies.map((a) => (
                    <div key={a.id} className="alert-card">
                      <div className="alert-info">
                        <h3>{a.allergen}</h3>
                        {a.reaction && <p>Reaction: {a.reaction}</p>}
                        <span className={`role-badge role-${a.severity}`}>{a.severity}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {allergyPatientId && (
              <form onSubmit={addAllergy} className="vitals-form" style={{ marginTop: 20 }}>
                <h3>Add New Allergy</h3>
                <div className="form-group">
                  <label>Allergen *</label>
                  <input value={newAllergen} onChange={(e) => setNewAllergen(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Reaction (optional)</label>
                  <input value={newReaction} onChange={(e) => setNewReaction(e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Severity *</label>
                  <select value={newSeverity} onChange={(e) => setNewSeverity(e.target.value)}>
                    <option value="mild">Mild</option>
                    <option value="moderate">Moderate</option>
                    <option value="severe">Severe</option>
                  </select>
                </div>
                <button type="submit" className="refresh-button">
                  Add Allergy
                </button>
              </form>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
