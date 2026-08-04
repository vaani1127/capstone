import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store/auth';
import { wsService } from '@/services/websocket';
import ProtectedRoute from '@/components/ProtectedRoute';
import LandingPage from '@/pages/LandingPage';
import LoginPage from '@/pages/LoginPage';
import DoctorDashboard from '@/pages/DoctorDashboard';
import NurseDashboard from '@/pages/NurseDashboard';
import AdminDashboard from '@/pages/AdminDashboard';
import PatientDashboard from '@/pages/PatientDashboard';
import './App.css';

function App() {
  const { isAuthenticated, user } = useAuthStore();
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    // Detect if app is running in standalone mode (opened from home screen)
    const standalone = window.matchMedia('(display-mode: standalone)').matches ||
                      (window.navigator as any).standalone === true;
    setIsStandalone(standalone);
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      wsService.connect().catch((error) => {
        console.error('Failed to connect WebSocket:', error);
      });

      return () => {
        wsService.disconnect();
      };
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <BrowserRouter>
        <Routes>
          {/* Skip landing page if app is running in standalone mode (installed app) */}
          <Route path="/" element={isStandalone ? <LoginPage /> : <LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/doctor/*"
          element={
            <ProtectedRoute roles={['Doctor']}>
              <DoctorDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/nurse/*"
          element={
            <ProtectedRoute roles={['Nurse']}>
              <NurseDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/*"
          element={
            <ProtectedRoute roles={['Admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/patient/*"
          element={
            <ProtectedRoute roles={['Patient']}>
              <PatientDashboard />
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to={`/${user?.role.toLowerCase()}/*`} replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
