import { useAuthStore } from '@/store/auth';
import '../styles/dashboard.css';

export default function PatientDashboard() {
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
          <h2>Your Health Portal</h2>
          <p>View appointments, medical history, vitals, and allergies</p>
          <div className="coming-soon">
            <p>⏳ Patient portal features coming soon...</p>
          </div>
        </section>
      </main>
    </div>
  );
}
