import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api';
import '../styles/dashboard.css';

interface UserItem {
  id: number;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface AnomalyAlert {
  id: number;
  trigger_type: string;
  narrative: string | null;
  is_acknowledged: boolean;
  created_at: string;
}

interface AnomalyAlertList {
  alerts: AnomalyAlert[];
  total: number;
}

interface AuditLog {
  id: number;
  record_type: string;
  user_name?: string;
  is_tampered: boolean;
  timestamp: string;
}

interface ChainIntegrity {
  is_valid: boolean;
  total_records: number;
  tampered_records: number;
}

interface BehavioralScore {
  id: number;
  score: number;
  computed_at: string;
  role: string;
}

interface BehavioralTrend {
  user_id: number;
  scores: BehavioralScore[];
  average_score: number;
  max_score: number;
  sustained_trend_flagged: boolean;
}

interface Organization {
  id: number;
  name: string;
  city?: string;
  state?: string;
  phone?: string;
}

interface Provider {
  id: number;
  name: string;
  speciality?: string;
  city?: string;
  encounter_count: number;
}

type Tab = 'home' | 'users' | 'alerts' | 'audit' | 'trend' | 'organizations' | 'providers';

export default function AdminDashboard() {
  const { user, logout } = useAuthStore();
  const [tab, setTab] = useState<Tab>('home');

  const [users, setUsers] = useState<UserItem[]>([]);
  const [usersLoading, setUsersLoading] = useState(true);
  const [usersError, setUsersError] = useState('');
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState('Patient');
  const [createUserError, setCreateUserError] = useState('');

  const [alerts, setAlerts] = useState<AnomalyAlert[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [alertsError, setAlertsError] = useState('');

  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [chainIntegrity, setChainIntegrity] = useState<ChainIntegrity | null>(null);
  const [auditLoading, setAuditLoading] = useState(true);
  const [auditError, setAuditError] = useState('');

  const [trendUserId, setTrendUserId] = useState('');
  const [trend, setTrend] = useState<BehavioralTrend | null>(null);
  const [trendLoading, setTrendLoading] = useState(false);
  const [trendError, setTrendError] = useState('');

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [orgsLoading, setOrgsLoading] = useState(true);
  const [orgsError, setOrgsError] = useState('');

  const [providers, setProviders] = useState<Provider[]>([]);
  const [providersLoading, setProvidersLoading] = useState(true);
  const [providersError, setProvidersError] = useState('');

  useEffect(() => {
    loadUsers();
    loadAlerts();
    loadAudit();
    loadOrganizations();
    loadProviders();
  }, []);

  const loadUsers = async () => {
    setUsersLoading(true);
    setUsersError('');
    try {
      const data = await apiClient.get<UserItem[]>('/users/');
      setUsers(data);
    } catch (err) {
      setUsersError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setUsersLoading(false);
    }
  };

  const loadAlerts = async () => {
    setAlertsLoading(true);
    setAlertsError('');
    try {
      const data = await apiClient.get<AnomalyAlertList>('/anomaly/alerts');
      setAlerts(data.alerts);
    } catch (err) {
      setAlertsError(err instanceof Error ? err.message : 'Failed to load alerts');
    } finally {
      setAlertsLoading(false);
    }
  };

  const acknowledgeAlert = async (alertId: number) => {
    try {
      await apiClient.post(`/anomaly/alerts/${alertId}/acknowledge`, {});
      loadAlerts();
    } catch (err) {
      setAlertsError(err instanceof Error ? err.message : 'Failed to acknowledge alert');
    }
  };

  const loadAudit = async () => {
    setAuditLoading(true);
    setAuditError('');
    try {
      const integrity = await apiClient.get<ChainIntegrity>('/audit/chain-integrity');
      setChainIntegrity(integrity);
      const logs = await apiClient.get<{ logs: AuditLog[] }>('/audit/logs?page=1&page_size=20');
      setAuditLogs(logs.logs);
    } catch (err) {
      setAuditError(err instanceof Error ? err.message : 'Failed to load audit data');
    } finally {
      setAuditLoading(false);
    }
  };

  const loadTrend = async () => {
    if (!trendUserId) return;
    setTrendLoading(true);
    setTrendError('');
    try {
      const data = await apiClient.get<BehavioralTrend>(`/anomaly/behavioral-scores/${trendUserId}?limit=30`);
      setTrend(data);
    } catch (err) {
      setTrendError(err instanceof Error ? err.message : 'Failed to load behavioral trend');
    } finally {
      setTrendLoading(false);
    }
  };

  const loadOrganizations = async () => {
    setOrgsLoading(true);
    setOrgsError('');
    try {
      const data = await apiClient.get<{ organizations: Organization[] }>('/organizations/?page=1&page_size=20');
      setOrganizations(data.organizations);
    } catch (err) {
      setOrgsError(err instanceof Error ? err.message : 'Failed to load organizations');
    } finally {
      setOrgsLoading(false);
    }
  };

  const loadProviders = async () => {
    setProvidersLoading(true);
    setProvidersError('');
    try {
      const data = await apiClient.get<{ providers: Provider[] }>('/providers/?page=1&page_size=20');
      setProviders(data.providers);
    } catch (err) {
      setProvidersError(err instanceof Error ? err.message : 'Failed to load providers');
    } finally {
      setProvidersLoading(false);
    }
  };

  const createUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateUserError('');
    try {
      await apiClient.post('/auth/register', {
        name: newName,
        email: newEmail,
        password: newPassword,
        role: newRole,
      });
      setNewName('');
      setNewEmail('');
      setNewPassword('');
      setNewRole('Patient');
      setShowCreateUser(false);
      loadUsers();
    } catch (err) {
      setCreateUserError(err instanceof Error ? err.message : 'Failed to create user');
    }
  };

  const unacknowledgedCount = alerts.filter((a) => !a.is_acknowledged).length;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Admin Dashboard - {user?.name}</h1>
        <button onClick={logout} className="logout-button">
          Logout
        </button>
      </header>

      <main className="dashboard-content">
        <div className="tabs">
          <button className={`tab-button ${tab === 'home' ? 'active' : ''}`} onClick={() => setTab('home')}>
            Home
          </button>
          <button className={`tab-button ${tab === 'users' ? 'active' : ''}`} onClick={() => setTab('users')}>
            Users ({users.length})
          </button>
          <button className={`tab-button ${tab === 'alerts' ? 'active' : ''}`} onClick={() => setTab('alerts')}>
            Alerts ({unacknowledgedCount})
          </button>
          <button className={`tab-button ${tab === 'audit' ? 'active' : ''}`} onClick={() => setTab('audit')}>
            Audit Log
          </button>
          <button className={`tab-button ${tab === 'trend' ? 'active' : ''}`} onClick={() => setTab('trend')}>
            Behavioral Trend
          </button>
          <button className={`tab-button ${tab === 'organizations' ? 'active' : ''}`} onClick={() => setTab('organizations')}>
            Organizations
          </button>
          <button className={`tab-button ${tab === 'providers' ? 'active' : ''}`} onClick={() => setTab('providers')}>
            Providers
          </button>
        </div>

        {tab === 'home' && (
          <section>
            <h2>System Overview</h2>
            <div className="patient-list">
              <div className="patient-card">
                <div className="info">
                  <h3>{users.length}</h3>
                  <p className="status">Total Users</p>
                </div>
              </div>
              <div className="patient-card">
                <div className="info">
                  <h3>{unacknowledgedCount}</h3>
                  <p className="status">Unacknowledged Alerts</p>
                </div>
              </div>
              <div className="patient-card">
                <div className="info">
                  <h3>{chainIntegrity ? (chainIntegrity.is_valid ? 'Valid' : 'Tampered') : '—'}</h3>
                  <p className="status">Audit Chain Integrity</p>
                </div>
              </div>
              <div className="patient-card">
                <div className="info">
                  <h3>{organizations.length}</h3>
                  <p className="status">Organizations</p>
                </div>
              </div>
            </div>
          </section>
        )}

        {tab === 'users' && (
          <section>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2>System Users</h2>
              <button className="refresh-button" onClick={() => setShowCreateUser(!showCreateUser)}>
                {showCreateUser ? 'Cancel' : '+ Add User'}
              </button>
            </div>

            {showCreateUser && (
              <form onSubmit={createUser} className="vitals-form" style={{ marginBottom: 20 }}>
                {createUserError && <div className="error-message">{createUserError}</div>}
                <div className="form-row">
                  <div className="form-group">
                    <label>Name *</label>
                    <input value={newName} onChange={(e) => setNewName(e.target.value)} required />
                  </div>
                  <div className="form-group">
                    <label>Email *</label>
                    <input type="email" value={newEmail} onChange={(e) => setNewEmail(e.target.value)} required />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Password *</label>
                    <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
                  </div>
                  <div className="form-group">
                    <label>Role *</label>
                    <select value={newRole} onChange={(e) => setNewRole(e.target.value)}>
                      <option value="Admin">Admin</option>
                      <option value="Doctor">Doctor</option>
                      <option value="Nurse">Nurse</option>
                      <option value="Patient">Patient</option>
                    </select>
                  </div>
                </div>
                <button type="submit" className="refresh-button">Create User</button>
              </form>
            )}

            {usersError && <div className="error-message">{usersError}</div>}
            {usersLoading ? (
              <div className="loading">Loading users...</div>
            ) : (
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.id}>
                        <td>{u.name}</td>
                        <td>{u.email}</td>
                        <td>
                          <span className={`role-badge role-${u.role.toLowerCase()}`}>{u.role}</span>
                        </td>
                        <td>
                          <span className={u.is_active ? 'status-active' : 'status-inactive'}>
                            {u.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {tab === 'alerts' && (
          <section>
            <h2>Anomaly Alerts</h2>
            {alertsError && <div className="error-message">{alertsError}</div>}
            {alertsLoading ? (
              <div className="loading">Loading alerts...</div>
            ) : alerts.length === 0 ? (
              <p className="no-patients">No anomaly alerts</p>
            ) : (
              <div className="patient-list">
                {alerts.map((alert) => (
                  <div key={alert.id} className="alert-card">
                    <div className="alert-info">
                      <h3>{alert.trigger_type.replace(/_/g, ' ')}</h3>
                      <p>{alert.narrative || 'No details available'}</p>
                      <p className="alert-time">{new Date(alert.created_at).toLocaleString()}</p>
                    </div>
                    {!alert.is_acknowledged ? (
                      <button className="ack-button" onClick={() => acknowledgeAlert(alert.id)}>
                        Acknowledge
                      </button>
                    ) : (
                      <span className="status-active">Acknowledged</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {tab === 'audit' && (
          <section>
            <h2>Audit Dashboard</h2>
            {auditError && <div className="error-message">{auditError}</div>}
            {auditLoading ? (
              <div className="loading">Loading audit data...</div>
            ) : (
              <>
                {chainIntegrity && (
                  <div className="patient-list" style={{ marginBottom: 20 }}>
                    <div className="patient-card">
                      <div className="info">
                        <h3>{chainIntegrity.is_valid ? '✅ Chain Valid' : '⚠️ Chain Tampered'}</h3>
                        <p className="status">
                          {chainIntegrity.total_records} records · {chainIntegrity.tampered_records} tampered
                        </p>
                      </div>
                    </div>
                  </div>
                )}
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>User</th>
                        <th>Status</th>
                        <th>Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditLogs.map((log) => (
                        <tr key={log.id}>
                          <td>{log.record_type}</td>
                          <td>{log.user_name || 'System'}</td>
                          <td>
                            <span className={log.is_tampered ? 'status-inactive' : 'status-active'}>
                              {log.is_tampered ? 'Tampered' : 'Verified'}
                            </span>
                          </td>
                          <td>{new Date(log.timestamp).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </section>
        )}

        {tab === 'trend' && (
          <section>
            <h2>Behavioral Score Trend</h2>
            <div className="form-row">
              <div className="form-group">
                <label>User ID</label>
                <input type="number" value={trendUserId} onChange={(e) => setTrendUserId(e.target.value)} />
              </div>
              <div className="form-group" style={{ justifyContent: 'flex-end' }}>
                <button type="button" className="refresh-button" onClick={loadTrend}>
                  Load Trend
                </button>
              </div>
            </div>
            {trendError && <div className="error-message">{trendError}</div>}
            {trendLoading ? (
              <div className="loading">Loading trend...</div>
            ) : trend ? (
              <>
                <div className="patient-list" style={{ marginBottom: 16 }}>
                  <div className="patient-card">
                    <div className="info">
                      <h3>Avg: {trend.average_score.toFixed(3)} · Max: {trend.max_score.toFixed(3)}</h3>
                      <p className="status">
                        {trend.sustained_trend_flagged ? '⚠️ Sustained trend flagged' : '✅ No sustained trend'}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Score</th>
                        <th>Role</th>
                        <th>Computed At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {trend.scores.map((s) => (
                        <tr key={s.id}>
                          <td>{s.score.toFixed(3)}</td>
                          <td>{s.role}</td>
                          <td>{new Date(s.computed_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <p className="no-patients">Enter a user ID to view their behavioral score trend</p>
            )}
          </section>
        )}

        {tab === 'organizations' && (
          <section>
            <h2>Organizations</h2>
            {orgsError && <div className="error-message">{orgsError}</div>}
            {orgsLoading ? (
              <div className="loading">Loading organizations...</div>
            ) : organizations.length === 0 ? (
              <p className="no-patients">No organizations found</p>
            ) : (
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>City</th>
                      <th>State</th>
                      <th>Phone</th>
                    </tr>
                  </thead>
                  <tbody>
                    {organizations.map((o) => (
                      <tr key={o.id}>
                        <td>{o.name}</td>
                        <td>{o.city || '—'}</td>
                        <td>{o.state || '—'}</td>
                        <td>{o.phone || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {tab === 'providers' && (
          <section>
            <h2>Providers</h2>
            {providersError && <div className="error-message">{providersError}</div>}
            {providersLoading ? (
              <div className="loading">Loading providers...</div>
            ) : providers.length === 0 ? (
              <p className="no-patients">No providers found</p>
            ) : (
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Speciality</th>
                      <th>City</th>
                      <th>Encounters</th>
                    </tr>
                  </thead>
                  <tbody>
                    {providers.map((p) => (
                      <tr key={p.id}>
                        <td>{p.name}</td>
                        <td>{p.speciality || '—'}</td>
                        <td>{p.city || '—'}</td>
                        <td>{p.encounter_count}</td>
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
