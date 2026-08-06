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

type Tab = 'users' | 'alerts';

export default function AdminDashboard() {
  const { user, logout } = useAuthStore();
  const [tab, setTab] = useState<Tab>('users');

  const [users, setUsers] = useState<UserItem[]>([]);
  const [usersLoading, setUsersLoading] = useState(true);
  const [usersError, setUsersError] = useState('');

  const [alerts, setAlerts] = useState<AnomalyAlert[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [alertsError, setAlertsError] = useState('');

  useEffect(() => {
    loadUsers();
    loadAlerts();
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
          <button
            className={`tab-button ${tab === 'users' ? 'active' : ''}`}
            onClick={() => setTab('users')}
          >
            Users ({users.length})
          </button>
          <button
            className={`tab-button ${tab === 'alerts' ? 'active' : ''}`}
            onClick={() => setTab('alerts')}
          >
            Anomaly Alerts ({alerts.length})
          </button>
        </div>

        {tab === 'users' && (
          <section>
            <h2>System Users</h2>
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
      </main>
    </div>
  );
}
