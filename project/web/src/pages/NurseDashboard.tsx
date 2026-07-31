import { useAuthStore } from '@/store/auth';
import '../styles/dashboard.css';

export default function NurseDashboard() {
  const { user, logout } = useAuthStore();

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Welcome, {user?.name}</h1>
        <button onClick={logout} className="logout-button">
          Logout
        </button>
      </header>

      <main className="dashboard-content">
        <section className="info-section">
          <h2>Nurse Dashboard</h2>
          <p>Quick actions: Walk-in registration, Record vitals, Check queue status</p>
          <div className="coming-soon">
            <p>⏳ Dashboard features coming soon...</p>
          </div>
        </section>
      </main>
    </div>
  );
}
