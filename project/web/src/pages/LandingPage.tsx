import { useState, useEffect } from 'react'
import '../styles/landing.css'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export default function LandingPage() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [showInstallButton, setShowInstallButton] = useState(false)
  const [isInstalled, setIsInstalled] = useState(false)

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
      setShowInstallButton(true)
    }

    const appInstalledHandler = () => {
      setIsInstalled(true)
      setShowInstallButton(false)
    }

    window.addEventListener('beforeinstallprompt', handler)
    window.addEventListener('appinstalled', appInstalledHandler)

    if (window.navigator.standalone === true) {
      setIsInstalled(true)
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handler)
      window.removeEventListener('appinstalled', appInstalledHandler)
    }
  }, [])

  const handleInstall = async () => {
    if (!deferredPrompt) return

    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice

    if (outcome === 'accepted') {
      setDeferredPrompt(null)
      setShowInstallButton(false)
    }
  }

  return (
    <div className="landing-container">
      <div className="landing-content">
        {/* Header */}
        <div className="landing-header">
          <div className="app-icon">H</div>
          <h1>HealthSaathi</h1>
          <p className="tagline">Hospital Management System</p>
        </div>

        {/* Features */}
        <div className="features">
          <div className="feature-item">
            <div className="feature-icon">👥</div>
            <h3>User Management</h3>
            <p>Admin, Doctor, Nurse, Patient roles</p>
          </div>

          <div className="feature-item">
            <div className="feature-icon">📅</div>
            <h3>Appointments</h3>
            <p>Schedule and manage clinic appointments</p>
          </div>

          <div className="feature-item">
            <div className="feature-icon">📋</div>
            <h3>Medical Records</h3>
            <p>Complete patient EHR system</p>
          </div>

          <div className="feature-item">
            <div className="feature-icon">🏥</div>
            <h3>Queue Management</h3>
            <p>Real-time patient queue tracking</p>
          </div>

          <div className="feature-item">
            <div className="feature-icon">⚡</div>
            <h3>Fast & Secure</h3>
            <p>JWT authentication, HIPAA compliant</p>
          </div>

          <div className="feature-item">
            <div className="feature-icon">📱</div>
            <h3>Works Offline</h3>
            <p>Progressive Web App technology</p>
          </div>
        </div>

        {/* Installation Section */}
        <div className="installation-section">
          {showInstallButton && !isInstalled && (
            <>
              <p className="install-prompt">Install HealthSaathi on your phone for easy access</p>
              <button
                className="install-button"
                onClick={handleInstall}
              >
                📲 Install on Home Screen
              </button>
              <p className="install-hint">Click above to install the app, or continue in browser</p>
            </>
          )}

          {isInstalled && (
            <p className="installed-message">✅ App installed successfully!</p>
          )}

          {!showInstallButton && !isInstalled && (
            <p className="browser-hint">
              💡 Use "Add to Home Screen" from your browser menu to install
            </p>
          )}
        </div>

        {/* Action Button */}
        <a href="/login" className="continue-button">
          Continue to App →
        </a>

        {/* Footer */}
        <div className="landing-footer">
          <p>A secure Hospital Management System for clinics</p>
          <p className="version">HealthSaathi v1.0.0</p>
        </div>
      </div>
    </div>
  )
}
