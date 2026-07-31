import { useAuthStore } from '@/store/auth';
import '../styles/dashboard.css';

export default function AdminDashboard() {
  const { user, logout } = useAuthStore();

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Admin Dashboard - {user?.name}</h1>
        <button onClick={logout} className="logout-button">
          Logout
        </button>
      </header>

      <main className="dashboard-content">
        <section className="info-section">
          <h2>System Administration</h2>
          <p>Manage users, view anomaly alerts, audit logs, and system settings</p>
          <div className="coming-soon">
            <p>⏳ Admin panel features coming soon...</p>
          </div>
        </section>
      </main>
    </div>
  );
}
